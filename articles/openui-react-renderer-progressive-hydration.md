# OpenUI's React Renderer Explained: How Progressive Hydration Works with Streamed Model Output

When a language model generates a dashboard, it doesn't output the whole thing at once. Tokens arrive one at a time — a component name, then a prop, then a value, then the next component. The user is staring at a blank screen the entire time the model is thinking.

Unless the renderer is built for streaming.

OpenUI's React renderer solves this by rendering components progressively as tokens arrive. The first card appears while the model is still generating the third chart. Props fill in as they're parsed. Error boundaries catch malformed output without crashing the page. The result is an interface that feels responsive even when the model takes seconds to finish.

This article breaks down how that works — from raw token stream to interactive React components on screen.

## The Streaming Problem

Traditional UI rendering assumes you have the complete data before you start. A REST API returns JSON, you parse it, you render. But LLM output breaks this assumption in two ways:

1. **Tokens arrive sequentially.** The model generates left-to-right, one token at a time. You might have `MetricCard label="Revenue"` before the model has decided what the value prop will be.

2. **The structure is incomplete at every point.** With JSON, you can't render until you get the closing brace. An unclosed `{"components": [{"type": "MetricCard"` is invalid JSON — you can't parse it, let alone render it.

This is why OpenUI doesn't use JSON as its output format. It uses OpenUI Lang — a format designed from the ground up for streamability.

## Why OpenUI Lang Is Streamable (And JSON Isn't)

JSON requires matching delimiters. An object needs `{}`, an array needs `[]`, strings need closing quotes. If the model has generated half a JSON structure, the parser can't produce a valid tree — it's stuck waiting for closing tokens that haven't arrived.

OpenUI Lang uses a line-oriented format where each statement is independently parseable:

```
header = Header("Dashboard", "Real-time metrics")
revenue = MetricCard("Revenue", "$142K", trend="up")
chart = LineChart("Revenue Trend", data=revenueData)
```

Each line is a complete statement. The parser can produce a valid AST from the first line before the second line has started generating. No closing delimiters to wait for.

This isn't just a cosmetic choice — it's a fundamental architectural decision that makes progressive rendering possible.

## The Parsing Pipeline

OpenUI's parser (`lang-core`) processes the token stream through four stages:

### Stage 1: Lexer

The lexer (`lexer.ts`) converts raw text into tokens. It handles identifiers, string literals, numbers, operators, state variables (`$count`), and structural tokens (parentheses, brackets, braces). Newlines are significant — they're token boundaries that separate statements.

The key property: the lexer is incremental. It processes whatever text is available and produces tokens for complete lexemes. A half-received string literal stays in the buffer until the closing quote arrives.

### Stage 2: Statement Splitting

Raw tokens are split into statements at newline boundaries (`statements.ts`). The `autoClose` function handles the critical edge case: what if the model is mid-statement when we need to render?

Auto-close examines unclosed delimiters (parentheses, brackets, braces) and synthesizes closing tokens to produce a syntactically complete statement from incomplete input. This is what lets the parser produce a valid AST even when the model is halfway through generating a component's props.

### Stage 3: Expression Parsing

Each statement's tokens are parsed into an AST node (`expressions.ts`). The AST is a discriminated union with node types for every construct:

- `Comp` — component calls like `MetricCard("Revenue", "$142K")`
- `Str`, `Num`, `Bool` — literal values
- `Arr`, `Obj` — arrays and objects
- `StateRef` — reactive state variables (`$count`)
- `Ternary`, `BinOp` — expressions for conditional rendering

The parser classifies each statement as a value declaration, state declaration, query, or mutation. This classification drives how the renderer handles the node.

### Stage 4: Result Assembly

The parser produces a `ParseResult` with:
- `root` — the root AST node (the component tree)
- `meta.incomplete` — flag indicating the stream is still in progress
- `meta.errors` — validation errors (unknown components, missing props)
- `stateDeclarations` — reactive state bindings
- `queryStatements` / `mutationStatements` — data-fetching declarations

The `incomplete` flag is what the renderer uses to distinguish "still streaming" from "done with errors."

## How the React Renderer Works

The `Renderer` component (`react-lang/Renderer.tsx`) takes the raw response text and a component library, and produces React elements. Here's the flow:

### Parse on Every Update

Every time new tokens arrive (the `response` prop changes), the renderer re-parses the entire source. This sounds expensive, but the parser is fast — it's pure string processing with no network calls. And it has to re-parse because new tokens can change the structure of earlier statements (a new line might complete an auto-closed expression).

### Recursive Element Rendering

The parsed AST is a tree of `ElementNode`s. The `RenderNode` component recursively walks this tree:

1. Look up the component name in the library
2. Resolve props (materializing AST nodes into values)
3. Recursively render children
4. Pass everything to the library's component renderer

The library is a mapping from component names to React components. When the parser sees `MetricCard("Revenue", "$142K")`, the renderer looks up `MetricCard` in the library and renders it with those props.

### The isStreaming Prop

The `Renderer` accepts an `isStreaming` boolean that signals whether the model is still generating. During streaming:

- Form interactions are disabled (the model might be about to change the form structure)
- The `incomplete` flag in the parse result is expected and not treated as an error
- Components render with whatever props are available so far

When streaming ends, the final parse happens, forms become interactive, and any remaining errors are reported.

## Progressive Hydration in Practice

Here's what "progressive hydration" looks like concretely during a streaming response:

**T=200ms** — Model has generated: `header = Header("Q2 Dashboard")`
- Parser produces AST with one Comp node
- Renderer renders: a Header component with title "Q2 Dashboard"
- User sees: the header, everything below is empty

**T=400ms** — Model adds: `revenue = MetricCard("Revenue", "$142K", trend="up")`
- Parser re-parses entire source (two statements now)
- Renderer renders: Header + MetricCard
- User sees: header and a revenue card, rest still loading

**T=700ms** — Model adds: `chart = LineChart("Trend", data=` (incomplete)
- Parser auto-closes the incomplete statement
- Renderer renders: Header + MetricCard + LineChart with partial props
- User sees: header, revenue card, and a chart component (possibly with placeholder data)

**T=1200ms** — Model completes the chart and adds a table
- Full re-parse, all components render with complete props
- User sees: the complete dashboard

The user saw meaningful content at 200ms. The full dashboard took 1200ms. Without progressive rendering, they'd see nothing for 1200ms, then everything at once.

## Error Recovery: Show Last Good State

Streaming means errors are normal. A half-parsed prop, a component reference that doesn't exist yet, a type mismatch from incomplete data. The renderer needs to handle all of this without crashing.

OpenUI's approach is an `ElementErrorBoundary` — a React error boundary with a specific behavior: **when a component throws during render, show the last successfully rendered version of that component.**

```typescript
// Simplified from the actual implementation
class ElementErrorBoundary extends Component {
  private lastValidChildren = null;

  componentDidUpdate(prevProps) {
    if (!this.state.hasError) {
      // Save the last good render
      this.lastValidChildren = this.props.children;
    }
    if (this.state.hasError && prevProps.children !== this.props.children) {
      // New children arrived — try rendering again
      this.setState({ hasError: false });
    }
  }

  render() {
    if (this.state.hasError) {
      return this.lastValidChildren; // Show last good state
    }
    return this.props.children;
  }
}
```

This creates a graceful degradation chain:
1. Component renders successfully → save as "last good state"
2. New streaming tokens cause a render error → show the saved state
3. More tokens arrive → try rendering again
4. If the new render succeeds → update "last good state"

The user never sees a blank screen or a crash. At worst, they see a slightly stale version of a component for a fraction of a second.

### Structured Error Reporting

Beyond error boundaries, the renderer reports structured errors via the `onError` callback. These aren't just error messages — they're typed objects with enough context for an automated correction loop:

- `unknown-component` — the model referenced a component not in the library
- `missing-required-prop` — a component is missing a required prop
- `tool-not-found` — a Query/Mutation references a tool that doesn't exist
- `render-error` — a component threw during rendering

This error channel enables a powerful pattern: the host application can feed errors back to the model and ask it to fix its output. The model sees "MetricCard requires a `value` prop" and regenerates with the missing prop.

## Stream Processing: From Network to Renderer

The `react-headless` package handles the connection between the streaming response and the renderer. The `processStreamedMessage` function reads from an SSE or WebSocket stream and produces message updates.

A key optimization: **updates are debounced with `requestAnimationFrame`.** The model might emit 20 tokens between frames. Rather than triggering 20 React re-renders (one per token), the stream processor batches updates to align with the browser's paint cycle:

```typescript
const debouncedUpdate = (msg) => {
  if (rafId !== null) cancelAnimationFrame(rafId);
  rafId = requestAnimationFrame(() => {
    updateMessage(msg);
    rafId = null;
  });
};
```

This means the renderer re-parses and re-renders at most once per frame (~60 times per second), regardless of how fast tokens arrive. Each re-render processes all tokens received since the last frame.

## The Component Library Contract

The library is the bridge between the model's output and your React components. `createLibrary()` takes a record of component definitions — each mapping a name to a React component with typed props.

The library defines what the model can output. If `MetricCard` isn't in the library, the model can write `MetricCard(...)` all day — the renderer will report an `unknown-component` error and skip it.

This is an intentional constraint. The component library is your design system boundary. The model operates within it, not outside it. You get the flexibility of AI-composed layouts with the consistency of a curated component set.

## Reactive State: Making Generated UI Interactive

Static rendering isn't enough for real applications. Users need to filter data, toggle views, fill forms. OpenUI handles this through reactive state declarations:

```
$selectedRegion = "US"
$dateRange = "7d"

regionFilter = Select("Region", options=regions, value=$selectedRegion)
chart = LineChart("Revenue", data=Query("getRevenue", region=$selectedRegion, range=$dateRange))
```

The `$` prefix marks a state variable. When the user changes the Select component, `$selectedRegion` updates, which triggers `Query("getRevenue", ...)` to refetch, which updates the chart. All declared in the model's output, all reactive at runtime.

The `useOpenUIState` hook manages this state. Form state is serializable — it can be persisted in the message history and restored when the user scrolls back to a previous AI response. The `initialState` prop on `Renderer` enables this hydration.

## Performance Characteristics

From the architecture, a few performance properties emerge:

**Time-to-first-render:** Determined by how fast the model generates the first complete statement. With a fast model (GPT-4o, Claude Sonnet), this is typically 150–300ms. The first component appears before the user registers that the page was loading.

**Re-parse cost:** The parser processes the entire source on every update. For typical AI responses (10–50 statements), this is sub-millisecond on modern hardware. The parser is pure synchronous computation — no async boundaries, no allocation-heavy operations.

**React reconciliation:** Because the renderer produces a tree of standard React elements, React's diffing algorithm handles efficient DOM updates. When a new statement arrives, only the new component's DOM nodes are created — existing components aren't re-mounted.

**Memory:** The stream processor holds the accumulating response text and the current parse result. No history of previous parse results is kept. The error boundary holds one reference to its last valid children. Memory grows linearly with response length, not with update count.

## Putting It Together

The full pipeline, from model token to pixel on screen:

1. Model generates a token → SSE stream delivers it to the browser
2. Stream processor appends to the response text, debounces via `requestAnimationFrame`
3. On the next frame, `Renderer` re-parses the full source
4. Parser produces AST with `incomplete: true` (still streaming)
5. `RenderNode` recursively maps AST nodes to library components
6. `ElementErrorBoundary` catches any render failures, falls back to last good state
7. React reconciles the new tree with the existing DOM
8. User sees the updated interface

This happens at 60fps. Each frame is a fresh parse and reconciliation pass. The user sees a smoothly growing interface, not a loading spinner followed by a page-sized content flash.

That's the core of how OpenUI makes generative UI feel responsive. The model takes seconds to generate a full layout. The renderer makes it feel instant by showing every intermediate state as a valid, interactive interface.
