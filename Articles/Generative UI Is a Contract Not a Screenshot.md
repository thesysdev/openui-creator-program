# Generative UI Is a Contract, Not a Screenshot

The phrase "generative UI" can sound vague if you have only seen polished demos. A user asks a question. The screen changes. Cards, charts, forms, and buttons appear. It feels like the model made an app on the fly.

That framing is exciting, but it is also misleading.

The useful version of generative UI is not a model inventing arbitrary screens. It is a model composing approved interface pieces inside rules your application controls. The UI is generated, but the authority stays with the product.

That is the difference between a screenshot trick and a real architecture.

## Text was the first interface

Most AI products started with text because text is the simplest output contract. The model receives a prompt and returns a response. The app renders that response in a chat bubble.

For many tasks, that is enough. If the user asks for an explanation, a summary, a draft email, or a short answer, text works well.

The limitation appears when the answer has structure:

- multiple options to compare,
- fields to fill,
- data to inspect,
- actions to approve,
- steps to track,
- or errors to recover from.

Text can describe those things, but it cannot make them easy to work with. A paragraph about three pricing plans is not the same as a comparison table. A list of required onboarding fields is not the same as a validated form. A recommendation to approve a risky action is not the same as an explicit approval panel.

Generative UI begins where generated text stops being the right final format.

## The bad definition: AI makes the frontend

The most dangerous definition is this: "Generative UI means the AI creates the interface."

That can lead teams toward raw code generation, arbitrary HTML, unbounded component props, and model-controlled actions. It may look impressive in a prototype, but it is not how product software should work.

If the model can invent the UI, it can also invent:

- unavailable components,
- off-brand layouts,
- invalid props,
- inaccessible color combinations,
- unsafe actions,
- misleading confirmations,
- and screens your product team never approved.

That does not mean generative UI is a bad idea. It means the boundary is wrong.

The model should not own the frontend. The application should own the frontend. The model should be allowed to compose within it.

## The better definition: AI composes a contract

A practical definition is:

> Generative UI is an interface pattern where a model returns a structured description of UI using a bounded component contract, and the application renders that description with components, validation, state, and actions it controls.

That definition has four important parts.

First, the model returns structure, not just prose. The output can represent cards, tables, forms, charts, or action groups.

Second, the model is bounded. It cannot use components your app did not register.

Third, the output is validated. Component props have schemas, required fields, enums, and composition rules.

Fourth, the application owns rendering and execution. The model can describe a button, but the app decides what clicking it means.

OpenUI follows this pattern. You define components with schemas and React renderers, create a library, generate prompt instructions from that library, receive OpenUI Lang from the model, and render it through `<Renderer />`.

## A small example

Suppose a support assistant needs to respond to:

```txt
Show me what is wrong with this customer's failed checkout and what I should do next.
```

The text-only answer might be:

```txt
The checkout failed because the payment gateway timed out. The customer
has retried twice. I recommend asking them to retry in 10 minutes and
opening an internal incident if failures continue.
```

That is readable, but it is not a workspace.

A generative UI response could instead describe an approved support surface:

```txt
root = SupportCase("Payment gateway timeout", severity, evidence, actions)
severity = SeverityBadge("high")
evidence = EvidenceList([retryCount, gatewayStatus])
retryCount = EvidenceItem("Customer retries", "2 failed attempts in 6 minutes")
gatewayStatus = EvidenceItem("Gateway health", "Timeout rate elevated")
actions = ActionGroup([messageCustomer, openIncident])
messageCustomer = Action("Send retry guidance", "send_retry_guidance")
openIncident = Action("Open incident if failures continue", "open_incident")
```

The app renders this through its own support components. It decides how a high severity badge looks. It decides whether the current user can open an incident. It logs actions through normal product systems.

The model composed the interface. It did not become the application.

## Why a component library matters

The component library is the heart of generative UI.

In a normal frontend, components are mostly for developers. They make implementation reusable and consistent. In generative UI, components also become the model's vocabulary.

If your library includes `PricingComparison`, the model can express a pricing decision. If it includes `DeploymentChecklist`, the model can express a rollout plan. If it includes `ApprovalPanel`, the model can express a decision gate.

The names, descriptions, prop schemas, and examples shape what the model can produce.

This is why a good generative UI library should be smaller than your full design system. The model does not need every low-level primitive. It needs components that represent meaningful product concepts.

For example:

```tsx
const ApprovalPanel = defineComponent({
  name: "ApprovalPanel",
  description: "Displays an approval decision with risks and final actions.",
  props: z.object({
    title: z.string(),
    riskLevel: z.enum(["low", "medium", "high"]),
    risks: z.array(z.string()),
    approveAction: z.string(),
    declineAction: z.string(),
  }),
  component: ({ props }) => <ApprovalPanelView {...props} />,
});
```

The model can choose the title, risk level, and risk list. It cannot choose arbitrary styles or bypass the product's action handler.

## Streaming changes the experience

Traditional generated UI approaches often wait for a full JSON object or code block before rendering. That creates a blank state while the model completes the entire response.

OpenUI Lang is designed for streaming. The model can emit a root statement first, then define referenced children as more tokens arrive. The renderer can parse the current response and progressively render what is valid.

That matters because generative UI should feel responsive. If a user asks for an incident summary, the severity and headline can appear before the full timeline finishes. If a user asks for a comparison, the table shell can appear before every row is complete.

Streaming is not just a performance trick. It makes the interface feel like it is being assembled around the user's question rather than dumped onto the screen after a long wait.

## Actions are where trust is won or lost

Generated UI becomes serious when it can trigger actions.

That is also where teams need to be strict.

The model should not execute business logic. It should not decide that a refund is allowed, a deployment is approved, or a payment should be sent. It can render an action surface that asks the user to decide.

The application should handle:

- permissions,
- confirmation,
- server-side validation,
- audit logging,
- idempotency,
- and error handling.

In this model, a generated button is a proposal. The app turns it into a real action only if the normal product rules pass.

That keeps generative UI from becoming a security hole disguised as a nice interface.

## When text is still better

Not every answer needs generated UI. A lot of AI output should remain text.

Use text when:

- the user asked for a short explanation,
- there is no structured data to inspect,
- no action is needed,
- the answer is mostly narrative,
- or the UI would add friction.

Use generated UI when:

- the answer has repeated structured items,
- the user needs to compare or filter,
- the user needs to provide input,
- the user needs to approve or execute an action,
- or the response should remain useful after the conversation moves on.

Generative UI is not a replacement for text. It is the next layer when text stops carrying the workflow.

## The mental model

The simplest mental model is:

- Text explains.
- UI organizes.
- Product code decides.

The model can explain in prose and organize through OpenUI Lang. But product code should decide what gets rendered, what actions are legal, what data is trusted, and what happens after a click.

That division of responsibility makes generative UI much less mysterious. It is not a model drawing screens. It is a typed interface between reasoning and rendering.

## The takeaway

Generative UI matters because AI products are outgrowing the chat bubble.

Users do not only want answers. They want comparison surfaces, forms, dashboards, checklists, approval flows, and actions that fit the task in front of them.

The safe way to build that is not to let the model become the frontend. The safe way is to give it a contract: a component library, schemas, examples, streaming rules, and app-owned actions.

That is where OpenUI is interesting. It treats generated UI as a controlled runtime surface, not a screenshot. The model can adapt the interface to the user's intent, while the application keeps ownership of design, state, permissions, and execution.

That is the version of generative UI worth building.
