# OpenUI's React Renderer Is a Stability Contract for Streaming UI

The hard part of generative UI is not rendering a component after a model finishes writing it.

The hard part is rendering something useful while the model is still writing, without letting half-formed syntax, missing references, slow tools, or transient component errors blank the interface. That is the difference between "the assistant is streaming text" and "the product is progressively becoming usable."

OpenUI's React renderer is interesting because it treats streamed model output as a stability problem. The model emits OpenUI Lang. The parser turns that text into statements. The renderer evaluates those statements into component props and React nodes. Along the way, OpenUI keeps the app from doing the two things users hate most in AI interfaces: waiting on a blank area, or watching a working interface disappear because the next token was temporarily invalid.

This article walks through that path from streamed text to React UI, using the current OpenUI source as the reference point. The useful mental model is:

> OpenUI does not hydrate one finished UI. It continuously repairs a partial program into the best renderable component tree it has so far.

## Why Normal React Rendering Is Not Enough

React is very good at reconciling state changes. Give it a valid component tree, update props, and it will preserve as much DOM and component state as it can.

A language model stream is messier than that. It does not naturally emit a valid component tree at every byte boundary. It may be in the middle of:

- a string literal
- a component call
- a nested array
- a query declaration
- a reference to a statement that has not arrived yet
- an action payload that is only half written

If the renderer waits for the final response, the user gets the familiar chatbot experience: a spinner, then a sudden full answer. If the renderer naively parses every chunk as complete code, small syntax gaps become user-visible failures.

OpenUI takes a third path. It designs the language and runtime around statements.

Instead of treating the model output as one giant JSON object, OpenUI Lang is a sequence of named statements:

```txt
root = Page([header, table])
header = TextContent("Pipeline risk")
table = Table([...])
```

That structure gives the streaming runtime something stable to hold onto. A statement can be complete even if later statements are still arriving. The root can reference child statements before those definitions appear. This lets the interface reveal top-down: first the shell, then content, then data-backed details.

## The Parser Keeps Completed Statements Stable

The core parser lives in `@openuidev/lang-core`. A complete parse path is straightforward: preprocess the input, auto-close incomplete brackets or strings if needed, split it into statements, parse each expression, classify statements, and build a `ParseResult`.

The streaming path adds a more important behavior: it caches completed statements.

In `createStreamParser`, OpenUI keeps:

- an internal text buffer
- a `completedEnd` watermark
- a map of completed statements
- the first statement id

As new text arrives, the parser scans from the last completed boundary. A newline at bracket depth zero marks the end of a statement. That means a newline inside an array or object does not accidentally split the expression.

The current pending text is handled differently from completed text. Completed statements are cached. The pending statement is cleaned, auto-closed, and parsed as a provisional expression.

That distinction is the renderer's first safety rail.

If the model has already emitted:

```txt
root = Page([summary, details])
summary = TextContent("Revenue is down 8%.")
```

and is currently streaming:

```txt
details = Table([
```

OpenUI does not throw away `root` and `summary`. It auto-closes the pending `details` expression enough to ask, "is there a useful partial statement here?" If not, the completed cache still provides a usable result.

The parser also protects completed statements from being corrupted by pending text. When it merges completed statements with the pending parse, pending statements cannot overwrite ids that are already completed. That matters during edit-style streams where the model may begin emitting a statement name that already exists but has not finished the replacement yet. Until the replacement is complete, the old stable statement continues to win.

This is a practical tradeoff. The user sees older but valid UI instead of a broken intermediate state.

## Auto-Close Is a Rendering Tool, Not Just Parser Convenience

OpenUI's `autoClose` function is small but important. It walks partial input, tracks whether the parser is inside a string, and tracks open brackets. If the current text is incomplete, it appends the matching quote or closing brackets so the parser can attempt a provisional parse.

That does not mean the model's output is considered final. The parse result carries the idea that the input was incomplete. But it gives the renderer a chance to turn:

```txt
root = Card(title: "Pipeline
```

into a syntactically testable candidate instead of an immediate failure.

This is where OpenUI differs from a strict full-document parse. A strict parser is correct once the document is done. A streaming parser has to be useful before that. Auto-close gives the runtime a temporary shape so it can continue producing the best available tree.

The consequence for developers is subtle: streaming UI quality depends on statement order. OpenUI's prompt generation explicitly tells models to emit the root statement first. The shell appears immediately, and unresolved references can fill in later. If the model emits leaf data first and `root` last, the renderer has nothing useful to show until the end.

So progressive rendering is not only a renderer feature. It is a language, prompt, parser, and component-library contract.

## Materialization Turns References Into a Component Tree

After parsing, OpenUI has statements and expressions. It still needs a renderable tree.

The materialization layer resolves references from the symbol table and lowers known component calls into `ElementNode` objects. It also tags element nodes with their source statement id. That id becomes useful later when actions, queries, errors, or component state need to point back to the statement that produced them.

References are where OpenUI's streaming model becomes visible.

If `root` references `details` before `details` exists, the materializer can mark the reference unresolved for now. When the `details` statement arrives later, the same root shape can resolve into a fuller component tree. This enables top-down reveal without forcing the model to inline everything inside one enormous expression.

The materializer also treats `Query()` and `Mutation()` as runtime references rather than normal inline values. They are declarations that the runtime can evaluate through a tool provider. This keeps data fetching and side effects out of the parser itself.

That separation is important:

- parser: understand OpenUI Lang
- materializer: resolve statements and component shapes
- evaluator: resolve runtime expressions, state, query results, and mutation references
- renderer: turn evaluated element nodes into React components

Each layer has a smaller job, which is why the runtime can degrade gracefully when one part is not ready.

## `useOpenUIState` Is the Renderer Pipeline

The React renderer delegates most of the runtime pipeline to `useOpenUIState`.

That hook creates a streaming parser from the current library schema, calls `sp.set(response)` when the response text changes, manages form and state bindings, owns a query manager, evaluates component props, and prepares the context that components use at render time.

There is a useful ordering here:

1. Parse the latest OpenUI Lang response.
2. Initialize or restore state.
3. Build an evaluation context for `$state`, query results, and mutation results.
4. Defer `Query()` and `Mutation()` evaluation while `isStreaming` is true.
5. Evaluate element props into concrete values.
6. Surface structured errors only after streaming stops.
7. Return the evaluated result and context to `<Renderer />`.

The deferred query behavior is especially important. During streaming, the model may be writing a query name, args, defaults, dependencies, and dependent components. Firing tools against that half-finished declaration would create noisy network calls and unstable UI. OpenUI waits until streaming stops before submitting query and mutation declarations to the `QueryManager`.

That does not mean the interface must be blank during tool fetches. `Query()` declarations can provide defaults, and the query manager preserves prior settled data while refetching. Components can render from defaults first, then update when the tool result arrives.

The result is a two-phase stability model:

- During model streaming, prefer renderable structure and avoid side effects.
- After streaming, evaluate tools and surface fixable errors.

That is the right default for production UI. Users can watch the interface appear without accidentally triggering tool calls from incomplete model text.

## The Renderer Is Deliberately Boring

Once `useOpenUIState` has done its work, the public React `Renderer` is intentionally simple.

It receives:

- `response`
- `library`
- `isStreaming`
- action and state callbacks
- optional initial state
- optional tool provider
- optional error handler

If there is no renderable root, it returns `null`. Otherwise it provides `OpenUIContext`, shows a query loader when query work is in flight, and renders the root node.

The recursive render function handles primitives, arrays, and element nodes. For an element node, it looks up the component by `typeName` in the library and calls the registered component renderer with evaluated props.

That simplicity is the point. React components do not need to know the parser grammar. They receive normal props and helper context. Component authors can focus on product behavior: tables, buttons, forms, charts, validation, and actions.

OpenUI's design keeps the weirdness of streamed model syntax out of everyday component implementation.

## Last-Good-State Prevents Blank UI

The React renderer includes an error boundary around each rendered element. Its behavior is not the usual "show fallback UI" pattern. It intentionally stores the last successfully rendered children and returns that last good state when a render error occurs.

That is a good fit for streaming generative UI.

Imagine a model has already produced a valid table. Then the next chunk changes a nested cell renderer, but the props are temporarily malformed. A conventional error boundary might replace the table with an error card. OpenUI's element boundary keeps the last valid children on screen and auto-recovers when new valid children arrive.

This turns transient model/runtime mistakes into non-events for the user.

It also narrows error reporting. `useOpenUIState` skips render-error reporting while `isStreaming` is true, because those errors may disappear on the next chunk. Once streaming ends, it collects parser errors, validation errors, runtime evaluation errors, render errors, and query/mutation tool errors into structured `OpenUIError` objects.

That shape is useful for an automated correction loop. The host app can pass those errors back to the model and ask for a patch instead of showing a generic failure.

## Actions Stay Behind Explicit Boundaries

Progressive rendering should not mean progressive side effects.

OpenUI keeps consequential work behind actions. A `Button` component, for example, uses `useIsStreaming()` and disables itself while streaming. For primary actions, it can validate the form before firing. When it does fire, it passes an action plan or user-friendly action message through the renderer's action callback.

`useOpenUIState` handles action plans by running steps such as:

- run a query or mutation
- continue the conversation
- open a URL
- set state
- reset state

Mutation steps halt on failure. Query invalidations go through the query manager. Form state is included with the action event.

This is one of the most important production details. The model can generate an interface that proposes an action, but the application still owns the handler, validation, tool provider, permissions, and final execution.

That makes the renderer safe enough to be dynamic. The model composes inside a component vocabulary; the product decides what any action actually means.

## Query Loading Is Not the Same as Model Streaming

Many AI apps collapse every kind of waiting into one spinner. OpenUI separates at least two kinds of waiting:

- the model is still streaming UI code
- declared queries are fetching data

In the renderer, `isStreaming` is passed into context so components can disable interactions or defer validation. Query loading comes from the `QueryManager` snapshot. The default renderer shows a small query loader and dims the rendered UI while query data is in flight.

Components can also respond to query loading themselves. The built-in table, for example, can show a table skeleton when a query is loading and no rows are available yet. Once prior data exists, the query manager can preserve settled data while refetching, which avoids replacing useful content with emptiness.

This is the right UX model for data-backed generative UI:

- streaming changes structure
- query loading changes data availability
- rendering should preserve useful prior state whenever possible

## The Architecture Tradeoff

OpenUI's renderer buys stability by adding structure.

The model does not emit arbitrary React. It emits OpenUI Lang statements. The host application provides a library. The parser knows the schema. The renderer maps type names to real components. Actions cross explicit callback boundaries.

That is more constrained than letting a model write arbitrary JSX. It is also much safer.

The benefits are practical:

- partially complete statements can be parsed
- completed statements can be cached
- unresolved references can fill in later
- props can be evaluated with runtime state and query results
- transient render failures keep the last good UI visible
- side effects wait for explicit actions
- errors can be reported in a structured correction loop

The cost is that developers must design the component vocabulary carefully. A poor library produces poor generated UI. Components need stable dimensions, validation behavior, loading states, accessible labels, and action semantics. The renderer can preserve stability, but it cannot rescue an unsafe component contract.

## What Developers Should Take Away

OpenUI's progressive rendering story is not just "stream tokens faster."

It is a layered stability contract:

- OpenUI Lang gives the model named statements instead of one fragile blob.
- The streaming parser caches completed statements and auto-closes pending ones.
- The materializer resolves references into element nodes as they become available.
- `useOpenUIState` evaluates props, state, queries, mutations, and errors.
- The React renderer maps evaluated nodes to approved components.
- Error boundaries preserve the last good render.
- Actions remain explicit and application-owned.

That is what makes streamed model output feel like an interface instead of a typing animation.

The best way to use it is to design for that contract. Put `root` first. Give components useful defaults. Use query defaults for initial render. Disable unsafe actions while streaming. Validate before mutation. Preserve prior data while refetching. Treat errors as repair signals, not just logs.

When those pieces line up, the user does not wait for a finished answer. They watch a usable interface assemble itself, stay stable under partial input, and become actionable only when the app says it is safe.

That is the real promise of OpenUI's React renderer: not magic hydration, but disciplined progressive UI under unreliable model output.

## References

- [OpenUI GitHub](https://github.com/thesysdev/openui)
- [OpenUI Docs](https://www.openui.com/)
- [Thesys OpenUI launch post](https://www.thesys.dev/blogs/openui)
- OpenUI source files referenced: `packages/lang-core/src/parser/parser.ts`, `packages/lang-core/src/parser/statements.ts`, `packages/lang-core/src/parser/materialize.ts`, `packages/react-lang/src/hooks/useOpenUIState.ts`, `packages/react-lang/src/Renderer.tsx`, and `packages/react-ui/src/components/OpenUIChat/GenUIAssistantMessage.tsx`
