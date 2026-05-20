# Progressive Rendering Is a Reliability Contract

When people talk about streamed AI interfaces, they usually focus on speed. A model starts answering, tokens arrive, and the user sees something before the full response is finished. That is valuable, but it is not the most interesting part.

The harder problem is reliability.

If the model is generating an interface instead of a paragraph, the frontend cannot wait for a perfectly complete object every time. It needs to handle partial output, late references, invalid nodes, and user actions without turning the page into a broken preview. Progressive rendering is not just a nicer loading state. It is the contract that lets model output become product UI while the output is still arriving.

OpenUI's React renderer is designed around that contract. The model writes OpenUI Lang. The parser reads it as a stream. The renderer maps the parsed element tree to your component library. The user sees a UI that can appear incrementally instead of a blank box that only becomes useful after the final token.

This article walks through the moving parts and the design decisions that make progressive rendering practical.

## The basic pipeline

An OpenUI app has four main pieces:

1. A component library that defines what the model is allowed to render.
2. A prompt generated from that library.
3. A streamed OpenUI Lang response from the model.
4. A React renderer that turns the parsed response into real components.

At the React layer, the entry point is intentionally small:

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

That component hides a lot of work. Every time the response changes, the parser can re-read the current text, validate what is available against the component library, and give the renderer a tree that is safe enough to display.

The important word is "current". During streaming, the current response is almost always incomplete.

## Why JSON is awkward for streamed UI

JSON is useful when the full object exists. It is less pleasant when the object is arriving token by token.

Imagine the model is generating a dashboard:

```json
{
  "component": "Dashboard",
  "props": {
    "cards": [
      { "label": "Revenue", "value": "$42k" },
```

Until the closing brackets arrive, the payload is invalid JSON. You can buffer it, try partial parsers, or ask the model to emit smaller JSON objects, but the runtime has to fight the format.

OpenUI Lang takes a different shape. It is line-oriented and reference-friendly:

```txt
root = Stack([summary, chart, actions])
summary = Card("Revenue is up 12%", "The West region drove most of the lift.")
chart = BarChart([west, east, central])
actions = Buttons([review, export])
```

The renderer does not need the entire future to start making progress. If `root` and `summary` are available, the UI shell and first child can render. If `chart` arrives later, the same response can re-parse and fill the missing piece.

This changes the user experience from "wait, then see everything" to "watch the interface become useful".

## The root component is the anchor

OpenUI libraries define a `root` component. That root is more than a naming convenience. It gives the model a predictable first statement and gives the renderer a stable top-level shape.

```tsx
export const incidentLibrary = createLibrary({
  root: "IncidentReview",
  components: [
    IncidentReview,
    SeverityBanner,
    Timeline,
    ActionChecklist,
  ],
});
```

If every generated program starts with `root = IncidentReview(...)`, the application knows where the rendered tree begins. This is especially useful during streaming because the root can appear before every child is fully defined.

For component authors, this means the root should be able to tolerate incomplete children. Avoid designs where the whole interface is useless until every nested prop arrives. Prefer a shell that can render a title, summary, or loading state while later sections fill in.

## Forward references let the model outline first

Forward references are one of the key tricks for good streamed UI.

The model can write:

```txt
root = IncidentReview(summary, [timeline, actions])
summary = SeverityBanner("High", "Payments are failing in EU region")
```

At the moment the root line arrives, `timeline` and `actions` may not exist yet. That should not force the whole UI to fail. A streaming-compatible parser can keep the reachable parts, resolve references as statements arrive, and avoid leaving unusable null holes in arrays.

That gives the model a natural writing pattern:

1. Declare the UI shape.
2. Fill in the most important content.
3. Add supporting sections.
4. Add actions after enough context exists.

It also gives the user a natural reading pattern. They see the headline and severity first, then details, then action controls.

## Invalid pieces should not poison the whole response

Model output is not trusted source code. It can miss a prop, use the wrong enum, or reference a component that does not exist in the current library.

The renderer contract should be fault-tolerant in a specific way: reject the broken piece, surface structured errors, and keep the valid UI alive.

OpenUI's `<Renderer />` exposes `onError` for this reason:

```tsx
<Renderer
  library={incidentLibrary}
  response={content}
  isStreaming={isStreaming}
  onError={(errors) => {
    if (errors.length > 0) {
      reportGeneratedUiErrors(errors);
    }
  }}
/>
```

Those errors are useful for debugging, but they also matter for automated correction loops. If the model used `severity: "urgent"` and the schema only allows `low`, `medium`, `high`, and `critical`, the app can give the model a precise correction instead of a vague "render failed".

The product benefit is simple: one malformed child should not turn a useful generated response into an empty state.

## Progressive rendering changes component design

Once the UI can stream, component design changes.

Large deeply nested props become a liability. If a component requires a single huge object, the model has to finish that object before anything useful can render. Smaller referenced components make better streaming units.

Prefer this:

```txt
root = DeploymentPlan([summary, checks, rollback])
summary = PlanSummary("Ready with two warnings", "Database migration needs review")
checks = CheckList([lint, tests, migration])
rollback = RollbackCard("Use v42 image", "Keep old schema for 24 hours")
```

Over this:

```txt
root = DeploymentPlan({
  "summary": { ... },
  "checks": [ ... ],
  "rollback": { ... }
})
```

The first shape gives the parser and renderer more stable milestones. Each statement can be validated and rendered as it becomes available. The second shape tends to behave like a delayed blob.

## Queries and mutations need explicit loading behavior

Generated UI often needs data. A support assistant may need to list tickets. A finance assistant may need to fetch account balances. A project assistant may need to create a task.

OpenUI's renderer can receive a `toolProvider` for `Query()` and `Mutation()` calls:

```tsx
<Renderer
  library={appLibrary}
  response={content}
  isStreaming={isStreaming}
  toolProvider={{
    list_tickets: async (args) => {
      const response = await fetch("/api/tickets", {
        method: "POST",
        body: JSON.stringify(args),
      });
      return response.json();
    },
  }}
  queryLoader={<span>Loading data...</span>}
/>
```

This is where progressive rendering and product reliability meet. The UI should be able to show a shell while the model streams, then show a local loading state while a query resolves, then render the data-driven child when the result exists.

Do not hide all of this behind a single page spinner. If the assistant has already generated a table frame and is waiting on one query, the user should still be able to understand what is happening.

## Actions are part of the streamed interface

Rendering is only half of the story. A generated interface may include buttons, forms, and follow-up actions.

OpenUI's renderer exposes an `onAction` callback so the app can receive structured action events:

```tsx
<Renderer
  library={appLibrary}
  response={content}
  isStreaming={isStreaming}
  onAction={(event) => {
    if (event.type === "continue_conversation") {
      sendFollowUp(event.humanFriendlyMessage, event.formState);
    }
  }}
/>
```

This keeps the model out of the execution path. The model can describe an action surface. The application decides what the action means, whether it is allowed, and what server-side checks are required.

For streamed UI, that boundary is crucial. A button can appear before the whole response finishes, but it should not become an unsafe shortcut around authorization or confirmation.

## What users actually feel

Users do not care that a parser reran or a reference resolved late. They care that the interface feels alive without feeling unstable.

Good progressive rendering feels like this:

- The first useful section appears quickly.
- Later sections fill in without layout chaos.
- Partial output does not flash broken component names.
- Invalid model output does not erase valid content.
- Loading states are local and understandable.
- Actions remain safe even when generated.

That is the difference between a streamed demo and a product feature.

## The takeaway

Progressive rendering is often described as a performance improvement. In generative UI, it is also a trust mechanism.

The user is watching a model produce interface structure in real time. The application has to keep that process bounded: only approved components, typed props, recoverable parsing, structured errors, controlled tools, and safe action callbacks.

OpenUI's renderer gives React apps that last-mile layer. It does not make model output magical. It gives the model a constrained language and gives the frontend a way to render partial work without giving up control.

That is why progressive rendering matters. Not because it eliminates waiting, but because it lets the interface become useful while still staying inside the product's rules.
