# OpenUI's React Renderer Explained: How Progressive Hydration Works with Streamed Model Output

Most LLM apps still treat the response as text first and UI second. The server waits for the model to finish, parses the result, and only then does the client get to decide what to render. That is fine for chat bubbles. It gets awkward once the model is supposed to produce an actual interface: tables, forms, cards, filters, actions, maybe a chart or two. At that point, waiting for the final token feels wasteful if the first half of the UI is already structurally clear.

OpenUI takes a different route. It asks the model to emit OpenUI Lang, a compact component-oriented language, and feeds the growing response into a streaming parser and React renderer. The result is not hydration in the usual server-rendered React sense. It is closer to progressive UI materialization: incomplete model output is repeatedly turned into the best component tree OpenUI can safely build at that moment, and React reconciles that tree as more text arrives.

I spent most of my time reading the current OpenUI source instead of working from the high-level diagram. This is the path I found from streamed model text to rendered React components.

## The Core Loop

At a high level, OpenUI's renderer pipeline is:

1. Define a component library with typed props.
2. Generate a system prompt from that library.
3. Ask the model to stream OpenUI Lang.
4. Parse the partial response with `createStreamingParser`.
5. Materialize a component tree from the parsed statements.
6. Evaluate dynamic props and query results.
7. Render the resulting `ElementNode` tree through React components.

The public OpenUI README describes this as:

```txt
Component Library -> System Prompt -> LLM -> OpenUI Lang Stream -> Renderer -> Live UI
```

The part worth paying attention to is the handoff between "OpenUI Lang Stream" and "Renderer". The renderer does not need the final token. The parser is built to tolerate partial input, unresolved references, and temporarily invalid structures while still returning a renderable tree when it can.

Here is the same flow with the moving pieces named:

```txt
model text
  |
  v
response string grows
  |
  v
createStreamingParser.set(response)
  |
  +--> cache complete statements
  +--> auto-close the current partial statement
  +--> keep unresolved refs as metadata
  |
  v
materializeValue(root statement)
  |
  v
ElementNode tree
  |
  v
useOpenUIState evaluates props, queries, state, actions
  |
  v
Renderer / RenderNode call registered React components
  |
  v
React reconciles the newest tree
```

That diagram is intentionally plain. The interesting part is not a hidden runtime trick. It is the fact that OpenUI keeps producing a normal-ish component tree even while the source text is still incomplete.

## Why Plain JSON Is Awkward for Streaming UI

JSON is easy to validate once it is complete. Mid-stream, it is a worse fit.

Imagine a model streaming this:

```json
{
  "component": "Card",
  "props": {
    "children": [
```

Until the braces and brackets close, a strict JSON parser has nothing useful to hand to React. This does not mean JSON can never be streamed. You can stream JSONL, emit a series of complete JSON objects, or use a tolerant parser with repair logic. The point is narrower: one big nested JSON object is awkward if you want to render meaningful intermediate UI states while the object is still unfinished.

In that setup, the application can buffer tokens, show a loading state, or start inventing partial-JSON repair rules. I have never seen that third option stay pleasant for long.

OpenUI Lang is structured around statements instead:

```txt
root = Stack([header, stats])
header = CardHeader("Usage this week", "Live system metrics")
stats = Card([metric1, metric2])
metric1 = TextContent("Requests", "18,240")
metric2 = TextContent("Errors", "12")
```

Each statement can become useful as soon as it is complete. Forward references such as `header` and `stats` are allowed to be missing for a while, then filled in when those statements arrive.

That choice explains a lot of the parser design.

## The Streaming Parser

The streaming entry point is exported from `@openuidev/lang-core` as `createStreamingParser`. In the current repo, `packages/lang-core/src/parser/index.ts` re-exports it from the parser module, and `packages/react-lang/src/hooks/useOpenUIState.ts` creates one parser per component library:

```ts
const sp = useMemo(
  () => createStreamingParser(library.toJSONSchema(), library.root),
  [library],
)
```

The `Renderer` passes the raw response string into `useOpenUIState`, and `useOpenUIState` calls:

```ts
return sp.set(response)
```

The parser's `set(fullText)` method expects the common streaming shape: the response string keeps getting longer. If the new response still starts with the previous buffer, it only processes the delta. If the text was replaced instead of appended, it resets and reparses. That is a small detail, but it matters in a UI that may update on every chunk.

Inside `packages/lang-core/src/parser/parser.ts`, `createStreamParser` keeps:

- `buf`: the full accumulated stream buffer
- `completedEnd`: the point already scanned for complete statements
- `completedStmtMap`: parsed statements that are complete and cached
- `firstId`: the first statement seen, used as a fallback root

The parser scans for depth-zero newlines. A newline inside `(...)`, `[...]`, `{...}`, a string, or a multi-line ternary does not end a statement. A newline at depth zero does. So the parser can cache completed statements and keep reparsing only the messy bit at the end of the stream.

The most practical streaming behavior is this block:

```ts
const { text: closed, wasIncomplete } = autoClose(cleaned)
const stmts = split(tokenize(closed))
```

`autoClose` lives in `packages/lang-core/src/parser/statements.ts`. It walks the pending text, tracks open strings and brackets, and appends the missing closing quote/bracket characters. That turns a partially streamed statement into something the parser can at least try to parse.

For example, if the model has only emitted:

```txt
root = Card("Revenue
```

`autoClose` can temporarily treat it like:

```txt
root = Card("Revenue")
```

The parser still knows the result was incomplete. The useful part is that the UI may have something reasonable to render instead of going blank.

Here is a small trace of what changes over time:

```txt
chunk 1:
root = Stack([summary, chart])

parser result:
root exists, but both children are unresolved -> render nothing useful yet

chunk 2:
summary = CardHeader("Latency", "p95 over time")

parser result:
root -> Stack([CardHeader(...)]), chart still unresolved -> render the summary

chunk 3:
chart = LineChart("Latency", data=

parser result:
autoClose can attempt the pending chart statement -> render the best available tree

chunk 4:
chart = LineChart("Latency", data=latencySeries)

parser result:
root -> Stack([CardHeader(...), LineChart(...)]) -> React reconciles the larger tree
```

That is the beginner-friendly version of the idea: OpenUI is not waiting for a perfect final document. It keeps asking, "What is the best tree I can honestly build from the text I have right now?"

## Statements Become a Component Tree

After tokenization and expression parsing, OpenUI classifies each statement. In `parser.ts`, `classifyStatement` splits the stream into the parts the runtime cares about:

- value statements such as `root = Card(...)`
- state declarations such as `$count = 0`
- query declarations such as `data = Query(...)`
- mutation declarations such as `save = Mutation(...)`

Then `buildResult` chooses an entry statement. It prefers a statement named `root`, then the library's configured root name, then the first component statement.

The parser materializes the chosen statement with `materializeValue` from `packages/lang-core/src/parser/materialize.ts`. This is the point where OpenUI Lang stops being syntax and becomes a typed `ElementNode` tree.

Materialization handles several stream-friendly cases:

- It resolves references from the symbol table.
- It detects cycles and unresolved references.
- It maps positional arguments to named props using the component schema.
- It applies defaults.
- It drops unresolved or invalid component refs from children arrays.
- It preserves dynamic runtime expressions for later evaluation.

This is the mechanism behind forward references. If the model starts with:

```txt
root = Stack([summary, chart])
summary = CardHeader("Latency", "p95 over time")
```

The first render may only contain `summary`. When `chart = LineChart(...)` arrives later, the parser returns a larger tree. React does the boring but important work after that: reconcile from the old tree to the new one.

The test suite captures this behavior directly in `packages/lang-core/src/parser/__tests__/parser.test.ts`:

```ts
const sp = createStreamParser(schema)
const p1 = sp.push('root = Stack([t1, t2])\nt1 = Title("first")\n')
expect((p1.root?.props?.children as any[]).length).toBe(1)
const p2 = sp.push('t2 = Title("second")\n')
expect((p2.root?.props?.children as any[]).length).toBe(2)
```

That is the progressive-rendering contract in miniature: partial trees are allowed to be useful, and later chunks can complete them.

## Renderer: From ElementNode to React

The React-specific renderer lives in `packages/react-lang/src/Renderer.tsx`.

The public component accepts:

```ts
export interface RendererProps {
  response: string | null
  library: Library
  isStreaming?: boolean
  onAction?: (event: ActionEvent) => void
  onStateUpdate?: (state: Record<string, unknown>) => void
  initialState?: Record<string, any>
  onParseResult?: (result: ParseResult | null) => void
  toolProvider?: ...
  queryLoader?: React.ReactNode
  onError?: (errors: OpenUIError[]) => void
}
```

The `Renderer` delegates parsing and state to `useOpenUIState`, then renders:

```tsx
<OpenUIContext.Provider value={contextValue}>
  <div style={{ position: "relative" }}>
    {isQueryLoading && (queryLoader ?? <DefaultQueryLoader />)}
    <div style={{ opacity: isQueryLoading ? 0.7 : 1 }}>
      <RenderNode node={result.root} />
    </div>
  </div>
</OpenUIContext.Provider>
```

`RenderNode` looks up the React component by `node.typeName`:

```tsx
const Comp = library.components[node.typeName]?.component
```

Then `RenderNodeInner` calls the registered component renderer:

```tsx
return <Comp props={el.props} renderNode={renderNode} statementId={el.statementId} />
```

This is an important boundary: the model never emits arbitrary React. It emits component calls in OpenUI Lang. The application decides which component names exist, what props they accept, and how those props render.

The recursive `renderDeep` helper lets component props contain nested `ElementNode`s or arrays of nodes. Component authors receive a `renderNode` function, so they can render child nodes without caring how the parser built them.

## "Last Good State" During Streaming

The renderer also protects the UI from transient failures. `Renderer.tsx` defines an `ElementErrorBoundary` with a very deliberate behavior: if a component render fails, it shows the last successfully rendered children instead of blanking the UI.

The code comment is explicit:

```ts
// This "show last good state" behavior prevents the UI from going blank
// during streaming or transient evaluation errors, and auto-recovers when
// new valid children arrive.
```

That matters because streamed UI is inherently provisional. A later chunk can fix what an earlier chunk made temporarily awkward. A normal error boundary would often replace the UI with an error fallback. OpenUI keeps the last usable render on screen and tries again when new children arrive.

`useOpenUIState` also suppresses render error reporting while `isStreaming` is true. Once streaming stops, parser, validation, runtime, render, and query errors are gathered and reported through `onError`. That gives host apps enough information to run a correction loop without treating harmless mid-stream incompleteness as a finished failure.

## Dynamic Props, State, Queries, and Actions

OpenUI's renderer is not just a string-to-component mapper. `useOpenUIState` also evaluates dynamic props and manages runtime state.

Key pieces:

- `createStore()` holds `$bindings` and form state.
- `createQueryManager()` executes `Query(...)` and `Mutation(...)` declarations through the provided tool provider.
- `evaluateElementProps()` resolves runtime expressions into concrete component props.
- `triggerAction()` turns component actions into host events, mutations, URL opens, state changes, or assistant continuations.

This is what lets a streamed component tree become an interactive surface after rendering. During streaming, form interactions are disabled via the `isStreaming` flag. After streaming, the same rendered components can update state, call actions, and trigger host callbacks.

Queries and mutations have another streaming guard. In `useOpenUIState`, the effects that evaluate query statements and register mutation statements both return early while `isStreaming` is true. That keeps half-written tool calls from firing just because the parser was able to temporarily auto-close an incomplete statement. Once the stream finishes, the hook evaluates the final query and mutation declarations against the current state and query snapshot.

The architecture keeps parsing separate from runtime evaluation:

- The parser turns OpenUI Lang into a typed tree and metadata.
- The runtime evaluates dynamic expressions against state and query results.
- The React renderer maps final `ElementNode`s to registered React components.

That separation is also why the same language core can sit underneath React, Vue, and Svelte packages in the repo.

## How the Example Chat App Streams Into the Renderer

The Next.js example app is a useful sanity check because it shows the full transport path rather than just the renderer in isolation.

In `examples/openui-chat/src/app/page.tsx`, the `FullScreen` chat UI sends messages to `/api/chat` and passes:

```tsx
streamProtocol={openAIAdapter()}
componentLibrary={openuiChatLibrary}
```

The API route in `examples/openui-chat/src/app/api/chat/route.ts` calls OpenAI with `stream: true`, forwards `delta.content` chunks as Server-Sent Events, and ends with `data: [DONE]`.

The client adapter consumes that stream and accumulates the assistant response. The renderer sees a changing `response` string, not isolated tokens. Each update calls `sp.set(response)`, the streaming parser computes the newest parse result, and React reconciles the newest component tree.

So the renderer does not need a special model API. It needs a text stream whose content is OpenUI Lang.

## Failure Modes Are First-Class

Streaming UI needs failure handling in more than one place. OpenUI has several layers:

- `stripFences` accepts code fenced responses and even handles incomplete fences during streaming.
- `stripComments` removes `//` and `#` comments outside strings because LLMs often include them.
- `autoClose` repairs incomplete strings and brackets for the pending statement.
- unresolved references are tracked in `meta.unresolved` rather than treated as fatal during streaming.
- unknown components and prop errors are recorded in `meta.errors`.
- invalid children can be dropped from arrays while valid siblings continue rendering.
- render errors use last-good-state behavior.
- `onError` receives structured errors once streaming stops.

This is the part I like most about the design. It does not pretend streamed model output is always valid. It keeps rendering what is valid, tracks what is not, and exposes enough diagnostics for the host app to correct the model or show a useful developer signal.

## The Tradeoff

OpenUI's progressive renderer gives developers faster time-to-first-UI and more resilient intermediate states, but it changes how you design model output.

The model needs to write in a component language rather than free-form prose. The app needs a carefully defined component library. Component props need schemas. Hosts need to decide how strict to be with validation errors after streaming completes.

That is the trade: more upfront structure in exchange for a UI stream that can be parsed, validated, rendered, and eventually interacted with incrementally.

For applications that only need text, this is unnecessary machinery. For agents that need to produce dashboards, forms, comparisons, analysis panels, workflow UIs, or data tools, the machinery is the point. The renderer gives React something meaningful to reconcile while the model is still writing.

## Mental Model

The shortest mental model I would keep is:

```txt
OpenUI Lang text stream
  -> cache completed statements
  -> auto-close pending statement
  -> materialize best available component tree
  -> evaluate runtime props
  -> render registered React components
  -> preserve last good UI during transient failures
```

That loop runs repeatedly as the response grows.

The user does not wait for a completed JSON object. The application does not need to invent a partial JSON parser. React gets a sequence of increasingly complete component trees, and the interface grows into place.

Source note: I checked the code paths above against OpenUI commit `9c60c4baf43083bab9cd9ae189d42658c959fec7`.
