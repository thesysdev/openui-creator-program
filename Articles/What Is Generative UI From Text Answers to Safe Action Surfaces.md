# What Is Generative UI? From Text Answers to Safe Action Surfaces

Most developers hear "generative UI" and picture the dangerous version first: a model inventing buttons, writing React, choosing layouts, and quietly turning your product surface into a slot machine.

That concern is reasonable. Production interfaces are not just pixels. They carry permissions, accessibility expectations, brand rules, analytics events, error states, billing actions, and user trust. Letting a model freely generate frontend code would be a strange way to protect any of that.

But that is not the useful definition of generative UI.

The useful definition is narrower and much more practical:

> Generative UI is a runtime contract where a model composes approved interface primitives, and the application validates, renders, and owns the resulting interaction.

The model is not the frontend engineer. It is closer to a layout planner working inside a constrained design system. Developers still own the component library, data access, action handlers, validation rules, permissions, and fallback behavior. The generated part is the composition: which approved components appear, with which props, in response to the user's current intent.

That distinction matters. It is the difference between "AI writes my app" and "AI picks the right working surface from a vocabulary I control."

## Why text output became the default

Text is the default output format for AI applications because it is simple, universal, and easy to stream. A model can answer almost anything as prose. The frontend only needs a text box, markdown renderer, and maybe a few code-block styles.

That works well for explanation:

- summarize this document,
- explain this error,
- draft this email,
- compare these tradeoffs,
- tell me what happened.

But many product workflows are not explanation workflows. They are inspection, selection, validation, approval, and action workflows.

If a support agent asks "which accounts need attention today?", a paragraph is not enough. They need a ranked list, account context, risk reasons, ownership, and next actions.

If a finance user asks "why did spend spike last week?", they need a chart, a segment table, outlier rows, and drilldowns.

If a developer asks an AI assistant to configure an integration, they need a form, validation, environment hints, and a review step before anything is saved.

Text can describe those interfaces. It cannot replace them.

Markdown tables are the usual halfway house, but they fail quickly. They do not sort. They do not preserve state. They do not validate input. They do not express disabled actions, required approvals, keyboard behavior, or follow-up tool calls. They look structured, but they are still just text.

Generative UI starts from the observation that many AI answers already have interface shape. The model is often saying:

- here are the options,
- here is the ranked evidence,
- here are the fields I need,
- here are the risky actions,
- here is the status of each step.

The missing piece is a safe way to turn that shape into real UI.

## The wrong mental model: generated screens

The most confusing way to think about generative UI is "the model generates a screen."

That framing creates two bad assumptions.

First, it makes the interface sound unconstrained. A screen can contain anything. A model that "generates screens" sounds like it can invent components, invent business rules, and invent flows.

Second, it makes developers imagine replacing their frontend code. If the model generates the screen, where do React components, design systems, accessibility checks, tests, and event handlers live?

A better mental model is: the model generates a component tree using a limited vocabulary.

The application gives the model a list of components it may use:

- `Card`,
- `Table`,
- `Col`,
- `Callout`,
- `Button`,
- `Form`,
- `TextContent`,
- `Stack`,
- `Chart`.

Each component has a contract. It accepts certain props, rejects invalid values, renders through application-owned code, and wires actions through application-owned handlers.

The model is not allowed to create arbitrary UI. It is allowed to compose from the available vocabulary.

That is the same design move that made SQL useful. A user can ask flexible questions, but the database still owns schemas, permissions, query execution, and constraints. Generative UI should work the same way: flexible composition over a governed substrate.

## The contract has four parties

A production generative UI system is not just a model and a renderer. It has at least four parts.

### 1. The component vocabulary

This is the set of UI primitives the model can use. It is where product and engineering teams encode what good output is allowed to look like.

For example, an internal operations assistant might expose:

- `IncidentSummary`,
- `EvidenceTable`,
- `OwnerBadge`,
- `SeverityTag`,
- `ApprovalPanel`,
- `RunbookStep`,
- `RollbackButton`.

A sales assistant might expose:

- `AccountCard`,
- `PipelineTable`,
- `RiskReasonList`,
- `NextBestAction`,
- `EmailDraftPreview`,
- `CRMUpdateButton`.

The vocabulary does not need to be huge. In fact, smaller is often better. A model with ten excellent primitives usually produces more trustworthy output than a model with a hundred loosely defined ones.

### 2. The model output format

The model needs a language for describing the component tree. Raw prose is too weak. Arbitrary code is too risky. JSON is familiar, but it is verbose and awkward for streaming because incomplete JSON is not valid JSON.

This is where a UI-specific language helps. [OpenUI](https://github.com/thesysdev/openui) uses OpenUI Lang: a compact, streaming-oriented way for the model to describe interface composition. The important idea is not just syntax. It is that the model output is meant to be parsed as UI intent, not executed as code.

A simple generated response can look like this:

```txt
root = Stack([title, summary, table, actions])
title = TextContent("Accounts needing review", "large-heavy")
summary = Callout("3 renewals are at risk this week.", "warning")
table = Table([accountCol, ownerCol, riskCol])
accountCol = Col("Account", accounts)
ownerCol = Col("Owner", owners)
riskCol = Col("Risk", risks)
accounts = ["Northstar Labs", "Kepler Finance", "Brightline Health"]
owners = ["Mina", "Jules", "Ari"]
risks = ["Legal blocker", "Security review overdue", "No executive sponsor"]
actions = Buttons([exportBtn, notifyBtn], "row")
exportBtn = Button("Export CSV", "action:export-csv", "secondary")
notifyBtn = Button("Notify owners", "action:notify-owners", "primary")
```

That is not React. It is not a privileged script. It is a description that the host application can parse, validate, and render through components it already controls.

### 3. The renderer

The renderer is the boundary between model output and product UI. Its job is to turn the generated description into real components without handing control to the model.

This boundary should be boring in the best way:

- unknown components are rejected,
- invalid props are handled safely,
- actions are namespaced and validated,
- rendering errors fall back gracefully,
- partial streams can render progressively,
- previous good UI can stay visible while new output is still arriving.

In a mature system, the renderer is also where teams can add accessibility wrappers, analytics instrumentation, error boundaries, and design-system defaults. The model can ask for a table. The application decides how tables behave.

### 4. The action layer

Generated UI becomes truly useful when it can do more than display information. Users need to click, approve, edit, submit, filter, and continue.

This is also where safety matters most.

A generated button should never be treated as permission to perform a sensitive operation. It should emit a structured action payload that the application validates:

```ts
type GeneratedAction =
  | { type: "export_csv"; tableId: string }
  | { type: "notify_owners"; accountIds: string[] }
  | { type: "request_approval"; workflowId: string; reason: string };
```

The model may propose `action:notify-owners`. The application decides whether the current user can notify owners, which account IDs are valid, whether a confirmation step is required, and what audit event should be recorded.

Generative UI should make actions easier to review, not easier to bypass.

## A concrete example: the same answer as text and UI

Imagine a user asks:

> Which renewal accounts need attention before Friday?

A text-only assistant might answer:

```txt
Three accounts need attention. Northstar Labs has a legal blocker,
Kepler Finance has an overdue security review, and Brightline Health
does not have an executive sponsor. You should notify the owners and
export the list for the weekly renewal review.
```

The answer is accurate, but the user still has work to do. They need to identify owners, copy account names, decide what to send, and maybe ask another follow-up question.

A generative UI response can preserve the same reasoning while giving the user a better surface:

- a warning summary,
- a table of accounts,
- owner and risk columns,
- a filter for severity,
- an export button,
- a "notify owners" action that opens a review step instead of firing immediately.

The model is not making a product decision on its own. It is presenting a structured review surface. The application still controls the dangerous parts.

This is where generative UI earns its keep. It reduces the gap between "the model knows what matters" and "the user can safely act on it."

## What developers still own

Generative UI does not remove frontend work. It changes where the leverage is.

Developers still need to own the component library. If a generated `ApprovalPanel` is confusing, that is not the model's fault. The primitive needs better design, clearer props, stronger defaults, or a narrower use case.

Developers still need to own data boundaries. The model should not decide what records a user can see. Tool calls and API responses should already be permissioned before they become UI input.

Developers still need to own accessibility. A generated interface still needs semantic headings, keyboard behavior, focus management, live-region rules, and text alternatives. The renderer and component library are the right places to enforce those patterns.

Developers still need to own tests. Exact-match snapshots will often be too brittle, but structural tests are still valuable:

- only approved components appear,
- required props exist,
- actions match a typed schema,
- destructive actions require confirmation,
- tables have headers,
- forms have labels,
- unsupported components fail closed.

In other words, generative UI moves frontend work from page-by-page assembly toward contract design.

## When generative UI is worth it

Generative UI is not the right default for every answer.

Plain text is still better for short explanations, creative writing, conversational coaching, and anything where the user simply wants a narrative response.

Fixed UI is still better for high-frequency workflows where the same screen is used every day and must be extremely predictable: checkout, login, account settings, audit logs, core admin flows.

Generative UI is most useful when the output is:

- structured,
- variable,
- action-oriented,
- data-heavy,
- role-specific,
- or hard to anticipate in advance.

Good candidates include analytics exploration, support triage, agent approval queues, incident response, compliance review, product comparison, workflow setup, and internal tools where users ask situational questions.

If the user keeps asking follow-up questions because the text answer is not enough to act on, that is a signal. The answer probably wants an interface.

## The production bar

The standard for generative UI should not be "the demo looked cool." The production bar is higher:

- Can the generated UI be validated before render?
- Can actions be audited?
- Can a user tell what is model-generated and what is system-verified?
- Can the same interaction be replayed for debugging?
- Can the interface degrade to text or a safe fallback?
- Can accessibility and keyboard behavior be preserved?
- Can the component vocabulary evolve without breaking old prompts?

OpenUI is interesting because it points directly at that production layer. It treats generated UI as a language and rendering problem, not as a gimmick. The model describes approved components. The renderer turns that description into real React UI. The application remains responsible for tools, state, and action execution.

That is the healthy version of generative UI: not a replacement for frontend engineering, but a new contract between intent and interface.

## The real shift

The old chatbot contract was:

> User asks. Model answers with text.

The generative UI contract is:

> User asks. Model composes an interface from approved primitives. Application validates, renders, and controls the interaction.

That contract is more complicated than text, but it is also more honest about what many AI products are trying to become. They are no longer just answer boxes. They are becoming adaptive work surfaces.

The question for developers is not whether models should generate arbitrary frontend code. They should not.

The better question is: what interface vocabulary should your product expose to the model, and what contracts make that vocabulary safe enough to use?

That is where generative UI becomes practical. Not as magic. Not as a replacement for design systems. Not as a way to dodge product thinking.

As a way to let AI assemble the right interface for the moment, while the application keeps ownership of everything that matters.

## References

- [OpenUI GitHub repository](https://github.com/thesysdev/openui)
- [OpenUI documentation](https://www.openui.com/)
- [Why We're Open Sourcing OpenUI](https://www.thesys.dev/blogs/openui)
- [OpenUI Product Hunt launch](https://www.producthunt.com/products/thesys/launches/openui-2)
