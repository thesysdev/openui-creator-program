# OpenUI's React Renderer Explained: How Progressive Rendering Works with Streamed Model Output

When developers first see Generative UI, it is easy to imagine the model returning a complete JSON object, the application parsing it, and React rendering the final interface in one pass.

OpenUI takes a different approach.

Instead of treating model output as plain text or waiting for a fully completed JSON payload, OpenUI uses **OpenUI Lang**: a compact language for describing model-generated interfaces. The model emits structured UI text, and the React renderer turns that response into a live component tree.

The practical result is that users do not have to wait for the entire response before the interface starts taking shape. The UI can progressively become visible and useful while the model is still generating.

This article explains the rendering path, why OpenUI Lang is a better fit for streamed component output than plain JSON, and what tradeoffs React developers should understand before building on this architecture.

---

## The basic OpenUI pipeline

At a high level, OpenUI turns a component library into a language model contract.

The application defines which components are available. OpenUI uses that library to guide the model. The model responds in OpenUI Lang, and the client-side renderer parses that response into React UI.

```text
Component Library
  ->
System Prompt
  ->
LLM
  ->
OpenUI Lang Response / Stream
  ->
Renderer
  ->
Live React UI
```

This is the key idea: the model is not simply writing prose. It is producing a structured UI description that maps to components the application already knows how to render.

A simplified React usage looks like this:

```tsx
import { Renderer } from "@openuidev/react-lang";
import { openuiLibrary } from "@openuidev/react-ui";

export function AssistantMessage({
  content,
  isStreaming,
}: {
  content: string | null;
  isStreaming: boolean;
}) {
  return (
    <Renderer
      library={openuiLibrary}
      response={content}
      isStreaming={isStreaming}
    />
  );
}
```

The important inputs are:

- `response`: the raw OpenUI Lang text produced by the model.
- `library`: the component library the renderer is allowed to use.
- `isStreaming`: whether the model response is still arriving.

That last prop matters because a streamed response is often incomplete. During generation, the renderer may see partial statements, unresolved references, or a component tree that is still being assembled.

---

## Why streamed UI is hard

Traditional React rendering usually starts from complete application state:

```text
Data is ready
  ->
React renders the component tree
  ->
User interacts with the complete UI
```

Model-generated UI is different. The model emits output incrementally:

```text
First tokens arrive
  ->
A partial UI statement appears
  ->
More statements arrive
  ->
The component tree becomes more complete
  ->
The final interface stabilizes
```

If the app waits for the entire response, users stare at a loading state even when parts of the answer are already usable.

If the app renders too early, it risks rendering broken UI.

OpenUI’s renderer sits between those two extremes. It lets the application render the best valid version of the interface available so far, while still accounting for the fact that the model may not be finished.

---

## Why not just stream JSON?

JSON is familiar, widely supported, and easy to validate after it is complete. A UI response could theoretically look like this:

```json
{
  "type": "Stack",
  "children": [
    {
      "type": "TextContent",
      "props": {
        "text": "Sales report"
      }
    },
    {
      "type": "Button",
      "props": {
        "label": "View details"
      }
    }
  ]
}
```

JSON can be streamed with specialized parsers, so the correct claim is not “JSON cannot stream.” It can. The problem is that JSON is awkward for progressive component rendering by default.

A normal JSON parser expects a complete document before returning a usable object. During generation, the client may temporarily receive this:

```json
{
  "type": "Stack",
  "children": [
    {
      "type": "TextContent",
      "props": {
        "text": "Sales
```

That is not valid JSON yet. A custom incremental parser could buffer and recover from this, but then the developer has to define partial validation, recovery behavior, component boundaries, and rendering rules.

OpenUI Lang is designed closer to the thing the app actually needs: a streamable description of components.

---

## OpenUI Lang as a component-oriented format

A simple OpenUI Lang response might look like this:

```text
root = Stack([header, report])
header = TextContent("Sales report", "large-heavy")
report = Card([
  TextContent("Revenue increased by 12% this month."),
  Button("View details")
])
```

The important pieces are:

- `root` defines the entry point.
- Other statements define named pieces of UI.
- The renderer resolves those names against the component library.
- The output maps to real React components, not arbitrary HTML.

During streaming, the renderer might first receive only this:

```text
root = Stack([header, report])
header = TextContent("Sales report", "large-heavy")
```

At that moment, `header` is known, but `report` is still unresolved.

A streaming-aware renderer can still understand part of the shape:

```text
root
└── Stack
    ├── header -> TextContent("Sales report", "large-heavy")
    └── report -> unresolved
```

When more text arrives:

```text
report = Card([
  TextContent("Revenue increased by 12% this month."),
  Button("View details")
])
```

the unresolved reference can become a complete subtree:

```text
root
└── Stack
    ├── header -> TextContent("Sales report", "large-heavy")
    └── report -> Card
        ├── TextContent("Revenue increased by 12% this month.")
        └── Button("View details")
```

That is the core advantage: the UI does not have to be treated as one all-or-nothing payload.

---

## Token stream to component tree

A useful mental model is to think of the response as a growing text buffer.

```text
Model stream
  ->
Growing OpenUI Lang response
  ->
Parser attempts to understand the current response
  ->
Renderer resolves known components
  ->
React displays the current best UI
```

A simplified rendering loop looks like this:

```text
Chunk 1 arrives
  ->
Parse what is currently available
  ->
Render known valid pieces

Chunk 2 arrives
  ->
Parse again
  ->
Resolve more references
  ->
Render a more complete tree

Chunk 3 arrives
  ->
Parse again
  ->
Replace unresolved sections
  ->
Render the final UI
```

This is different from classic server-side hydration, where HTML already exists on the page and React attaches behavior afterward. In this OpenUI context, “progressive hydration” is better understood as progressive rendering and progressive usability: the interface becomes more complete as model output arrives.

---

## Where React fits

React is good at reconciling changing trees. If the parsed UI representation changes, React can update the screen without the developer manually rebuilding the DOM.

A generated dashboard might move through stages like this:

```text
Stage 1: loading shell
Stage 2: title appears
Stage 3: summary card appears
Stage 4: chart or table appears
Stage 5: controls become usable
```

For example, the model might first emit:

```text
root = Stack([title])
title = TextContent("Customer health dashboard", "large-heavy")
```

Then continue with:

```text
summary = Card([
  TextContent("Churn risk is elevated for enterprise accounts.")
])
```

Then later add a chart or table.

The renderer’s job is to keep turning the current best OpenUI Lang response into a React tree. React’s job is to reconcile that tree as it grows.

---

## Why the component library matters

OpenUI does not ask the model to invent arbitrary UI. The application exposes a component library, and the renderer resolves generated component names against that library.

That gives the developer a boundary:

```text
Approved components
  ->
Model instructions
  ->
OpenUI Lang response
  ->
Renderer
  ->
Known React components
```

This matters for reliability and design consistency. If the library contains approved components like text blocks, cards, buttons, forms, charts, and tables, the model can be guided toward those instead of hallucinating random JSX.

It also means teams can expose their own design-system components. The generated UI can use the same visual building blocks as the rest of the application.

---

## Failure modes in streamed UI

Progressive rendering improves perceived speed, but it introduces failure modes developers need to handle.

### 1. Incomplete statements

The stream may stop in the middle of a statement:

```text
header = TextContent("Revenue
```

The renderer should not crash the whole app because one statement is incomplete during streaming.

### 2. Unresolved references

The root may reference a component that has not arrived yet:

```text
root = Stack([header, chart])
header = TextContent("Revenue")
```

Here, `chart` is unresolved. That might be temporary, not a final error.

### 3. Invalid component names

The model may produce a component that is not in the library:

```text
root = MagicRevenueWidget()
```

The component library is the source of truth. Unknown components should fail safely.

### 4. Malformed props

The model may start producing chart data and stop halfway:

```text
chart = LineChart({
  data: [
    { month: "Jan", revenue:
```

The renderer needs to avoid treating malformed partial props as final application state.

### 5. Layout instability

Because the UI changes as chunks arrive, developers should think about placeholders, stable layout containers, and avoiding excessive layout shift.

---

## Tradeoffs

OpenUI’s approach has real benefits, but it is not free.

### Benefits

- Faster time to first visible UI.
- Better fit for streamed model output than waiting for full JSON.
- A clear boundary between model output and approved components.
- A natural path for rich generated UI such as cards, charts, tables, and forms.
- Stronger design-system alignment than arbitrary generated HTML.

### Costs

- The renderer must handle partial and malformed output.
- Developers need to understand streaming states and unresolved references.
- Debugging streamed UI can be harder than debugging one complete payload.
- Frequent re-rendering can create visual instability if the app is not designed carefully.
- Output quality still depends on the prompt, the model, and the component library.

---

## Practical advice for developers

When building with this pattern, it helps to design for partial UI from the start.

Use clear loading states for unresolved areas. Keep component props simple where possible. Prefer components that can render with partial data. Add error boundaries around complex visualizations. Treat the model output as untrusted until it has been parsed and resolved against the component library.

Most importantly, remember that the component library is the contract. The more clearly the library defines what the model can use, the more predictable the rendered UI becomes.

---

## Conclusion

OpenUI’s React renderer matters because it bridges two very different worlds.

On one side, the model produces probabilistic streamed text. On the other side, React needs deterministic components and props.

OpenUI Lang gives the model a compact way to describe UI. The renderer turns the current best version of that description into a React component tree. React reconciles the result as more output arrives.

JSON can still be useful, and specialized JSON streaming is possible. But for generated component trees, OpenUI Lang is closer to the thing the app actually needs: a streamable UI description grounded in a known component library.

That is why progressive rendering is central to OpenUI’s developer experience. It lets AI-generated interfaces appear sooner, recover from partial output, and stay connected to real application components instead of treating the model response as one giant blob of text.