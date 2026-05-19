# What Is Generative UI? Interfaces Models Can Compose, Not Code They Invent

Most AI products still have a familiar shape: the user asks a question, the model does some work, and the result comes back as text.

That is fine when the answer is a sentence, a summary, or a small explanation. It breaks down the moment the answer wants to become a working surface.

Ask an assistant to compare three plans and you get a paragraph. Ask it to help triage incidents and you get a bulleted list. Ask it to analyze revenue and you get a markdown table. The model may have retrieved structured data, ranked options, called tools, and reasoned through tradeoffs, but the final interaction is still squeezed through prose.

Generative UI is the next layer after that. It means the model does not only generate content. It composes an interface from components the application already trusts.

The important word is composes. A production generative UI system should not let a model invent arbitrary frontend code. It gives the model a controlled vocabulary of components, data shapes, and actions, then asks it to assemble the right interface for the user's current task.

That distinction is what separates a useful architecture from a flashy demo.

## Text Is a Narrow Output Format

Text is the natural default for language models because it is easy to stream, inspect, log, and debug. It is also universal. Every client can display a paragraph.

But text has obvious limits as an application surface.

It cannot preserve much state. It is hard to sort, filter, compare, or edit. It makes the user scan sentences for values that should have been rendered as controls, charts, cards, or tables. It also forces the model to describe an action instead of giving the user a safe way to take that action.

Consider a support agent that finds three refund requests requiring approval. A text response can say:

> Three refunds need review. The first is $129.00 and looks eligible. The second is missing proof of purchase. The third exceeds the auto-approval threshold.

That is readable, but it is not a workflow. The user still has to copy IDs, open another screen, remember the reasoning, and avoid approving the wrong row.

A better response is a small interface:

- a table of refund requests,
- eligibility status per row,
- confidence and reason fields,
- approve, reject, and request-info actions,
- and a detail panel for the selected request.

The model's reasoning becomes easier to audit because it is attached to specific interface elements. The user can act without translating prose back into product state.

That is the basic case for generative UI: when the answer has structure, interaction, or follow-up work, it should not end as a wall of text.

## Generative UI Is Not "AI Writes React"

The easiest misunderstanding is to imagine a model generating React components on demand. That sounds powerful, but it is the wrong mental model for most real products.

Generated code creates security, consistency, and maintenance problems. It can ignore your design system, call functions it should not call, mishandle accessibility, leak state, or produce code that works once and becomes impossible to reason about later.

Production generative UI should be closer to this:

1. The product defines a component library.
2. Each component has a schema for its allowed props.
3. The model receives instructions describing that library.
4. The model returns a structured UI description.
5. The renderer maps that description to real application components.
6. The host app validates actions before anything mutates state.

The model is allowed to arrange approved pieces. It is not allowed to become the frontend build system.

That makes generative UI less magical, and much more useful.

## The Interface Contract

A good way to think about generative UI is as a contract between the model and the application.

The contract answers three questions:

1. What components can the model use?
2. What data is the model allowed to pass into those components?
3. What actions can the user take from the generated interface?

If any of those are vague, the system becomes brittle.

Suppose you are building an AI analytics assistant. You might give the model these components:

- `MetricCard`
- `TrendChart`
- `DataTable`
- `InsightCallout`
- `SegmentFilter`
- `ActionButton`

Each component has props. `MetricCard` might require `label`, `value`, `delta`, and `tone`. `TrendChart` might require a data series with timestamps and numeric values. `ActionButton` might require an action ID from an allowlist, not arbitrary JavaScript.

Now the model can respond to a question like "Why did activation fall last week?" with a generated interface:

```txt
root = Stack([headline, summary, metric, chart, table, actions])
headline = TextContent("Activation dropped 8.4% last week", "large-heavy")
summary = TextContent("The largest drop came from mobile signups in the EU cohort.", "medium")
metric = MetricCard("Activation rate", "31.6%", "-8.4%", "danger")
chart = TrendChart("Activation by day", activationSeries)
table = DataTable(cohortRows)
actions = Buttons([openCohort, createFollowup], "row")
openCohort = Button("Open cohort", "action:open-cohort", "secondary")
createFollowup = Button("Create follow-up", "action:create-followup", "primary")
```

That output is not the final UI. It is a compact description of the UI. The application still owns the renderer, components, permissions, styling, and action handling.

This is the core shift: the model produces intent-shaped interface structure, while the app preserves control.

## Why Prebuilt Responses Are Not Enough

Many AI products already mix text with UI. A chatbot might show a weather card, a flight card, or a product carousel. That is useful, but it is usually template selection rather than generative UI.

The system detects a known intent and renders a prebuilt response. Weather intent gets weather card. Flight intent gets flight card. Product search gets carousel.

This works when the product team can predict the main intents. It fails when the useful interface depends on the exact question, user role, returned data, and next action.

For example, "show me pipeline risk" could mean different things to different users:

- A CRO may need a forecast summary by region.
- A sales manager may need a rep-level coaching view.
- A finance lead may need weighted revenue exposure.
- A support lead may need churn-risk accounts with open tickets.

Those are not four skins over the same card. They are different working surfaces. They share a component vocabulary, but the composition changes with context.

Generative UI is valuable when the interface cannot be fully selected from a small set of templates. The product defines the grammar. The model composes the sentence.

## Why JSON Alone Feels Heavy

Structured UI generation is often built with JSON because every developer understands JSON. That is a reasonable starting point, but it has two problems for model output.

First, JSON is verbose. Component names, prop keys, and nested children repeat over and over. More output tokens mean higher latency and higher cost.

Second, JSON is awkward to stream as UI. A deeply nested object may not be valid until the model has finished generating it. The user waits for a complete tree before the app can confidently parse and render the result.

This is one reason OpenUI is interesting. OpenUI uses OpenUI Lang, a compact line-oriented language designed for streamed model-generated interfaces. The docs describe the flow as: define components, generate prompt instructions from the component library, ask the model to return OpenUI Lang, and progressively render each valid line through the React renderer.

OpenUI's published benchmarks compare OpenUI Lang with JSON-style UI formats across examples such as tables, charts, forms, dashboards, pricing pages, settings panels, and product cards. The claimed total is 4,800 tokens for OpenUI Lang versus 10,180 for one JSON rendering approach and 9,948 for another, with the docs summarizing the result as up to 67% more token efficient than JSON in specific cases.

The exact benchmark number matters less than the architectural point: UI output is not only about correctness. It is also about latency, streamability, and how quickly the user sees something useful.

## OpenUI's Role

OpenUI is a concrete implementation of the generative UI contract.

It includes:

- OpenUI Lang for compact, stream-friendly UI descriptions,
- `@openuidev/react-lang` for parsing, rendering, and prompt generation,
- `@openuidev/react-ui` for prebuilt chat layouts and component libraries,
- `@openuidev/react-headless` for chat state and streaming adapters,
- and a CLI for scaffolding applications.

The developer experience is built around a practical loop:

1. Define or reuse components.
2. Generate model instructions from those components.
3. Let the model respond in OpenUI Lang.
4. Render the output progressively.
5. Route user actions back through application-owned handlers.

That last step matters. If the generated UI includes a button, the button should not carry uncontrolled code. It should carry a declared action such as `action:create-followup` or `action:approve-refund`. The host app checks who the user is, what data the action applies to, and whether the action is allowed.

OpenUI gives the model a way to compose UI. It does not remove the need for normal application boundaries.

## The Three Boundaries That Keep It Safe

There are three boundaries every generative UI system needs.

The first is the component boundary. The model should choose from components the product team has designed, tested, and made accessible. If your design system has `Alert`, `Table`, `MetricCard`, and `Form`, the model can compose those. It should not invent a random interactive element because it sounds useful.

The second is the data boundary. Generated UI should be fed by trusted tool results, schemas, and server-owned state. The model can summarize and arrange data, but the application should validate that numeric values, IDs, and permissions come from real sources.

The third is the action boundary. User actions from generated UI should be structured payloads, not free-form commands. A refund approval, record update, or task creation should pass through the same authorization and validation path as any hand-built screen.

Those boundaries make generative UI feel less like "the model controls the app" and more like "the model helps assemble the right screen."

That is the version developers can ship.

## Where Generative UI Helps Most

Generative UI is not necessary for every response. If the user asks for a definition, text is enough. If the product has a stable, high-traffic workflow, a hand-designed page may be better.

It helps most when the output is structured, situational, and action-oriented.

Good candidates include:

- analytics assistants that need charts, tables, and filters,
- support workflows with triage queues and approval buttons,
- internal tools where each user role needs a slightly different view,
- voice agents that need visual feedback alongside speech,
- shopping or comparison flows with editable constraints,
- developer tools that return diffs, traces, logs, and remediation steps,
- onboarding flows where the next form depends on previous answers.

In all of these cases, plain text forces the user to do too much translation. Generative UI lets the system create a surface closer to the actual work.

## What Changes for Developers

Generative UI changes where frontend work happens.

Instead of designing every possible screen, developers design a controlled vocabulary of screen parts. Components become tools the model can call visually. Prop schemas become the safety rails. Renderers become interpreters. Prompts become part of the interface contract.

This does not make frontend engineering less important. It makes frontend engineering more central. The quality of the generated interface depends on the quality of the components the model is allowed to use.

If the component library is vague, the output will be vague. If the action model is unsafe, the generated UI will be unsafe. If the data layer is ungoverned, the interface will confidently display bad answers.

Generative UI does not replace product architecture. It exposes whether that architecture is ready for AI.

## A Useful Definition

Here is the definition I would give a developer who has heard the term but has not built with it yet:

Generative UI is an application pattern where an AI model composes a task-specific interface from a predefined component library, using structured output that the host app validates, renders, and connects to safe actions.

That definition keeps four ideas together:

- the interface is generated for the task,
- the components are predefined,
- the output is structured and validated,
- and the application keeps control over rendering and actions.

That is why text output is no longer enough. The best AI applications do not only answer. They help the user inspect, compare, decide, and act.

Text can explain the work. Generative UI can become the workspace.

## References

- [OpenUI documentation](https://www.openui.com/docs/openui-lang)
- [OpenUI GitHub repository](https://github.com/thesysdev/openui)
- [OpenUI benchmarks](https://www.openui.com/docs/openui-lang/benchmarks)
- [Why We're Open Sourcing OpenUI](https://www.thesys.dev/blogs/openui)
