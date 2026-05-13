# Generative UI Is a Runtime Contract

Most AI products still treat the model as a very smart paragraph machine. A user
asks a question, the model answers with text, and the application wraps that
answer in a chat bubble. If the answer contains numbers, the model writes a
list. If it contains choices, the model writes recommendations. If it contains
next steps, the model writes instructions.

That pattern is useful, but it has a ceiling. Text can describe an interface,
but it cannot behave like one. A paragraph cannot sort a table, validate a form,
expose a safe action, update a chart, or preserve a user's partial input while
new model output streams in.

Generative UI is the response to that ceiling. The important shift is not that
"AI designs screens." That framing is too loose. The practical shift is this:
the model produces a structured interface description inside a controlled
runtime, and the application renders that description with real components, real
state, and real permissions.

In other words, generative UI is a runtime contract between:

- the components your product exposes,
- the data and actions the model is allowed to use,
- the structured language the model emits,
- the renderer that turns that structure into UI,
- and the guardrails that keep the result usable, safe, and accessible.

That contract is what makes generative UI different from a chatbot that happens
to output nicer Markdown.

## Text Is a Report, Not an Interface

Text is good for explanation. It is bad at operation.

Imagine asking an operations assistant:

> Which production incidents need attention right now?

A text-only response might say:

```txt
There are three incidents that need attention:

1. Checkout latency is elevated in us-east-1. Severity: high.
2. Search indexing is delayed. Severity: medium.
3. Billing webhook retries are increasing. Severity: high.

I recommend checking checkout first.
```

That is readable, but the user still has work to do. They have to scan, compare,
remember what "high" means, open another tool, copy an incident ID, and decide
what to click next.

A better AI response would be an interface:

- a severity-ranked incident table,
- live status chips,
- a sparkline for each metric,
- a button to acknowledge an incident,
- a link to logs,
- a follow-up form for the mitigation note,
- and a confidence explanation that stays attached to the relevant row.

The model's job is not only to say what matters. It should help create the right
surface for acting on what matters.

That is the difference between a report and an interface.

## What Generative UI Actually Means

Generative UI means an AI system can generate a structured UI tree at runtime,
within a vocabulary of components and constraints defined by the application.

The model does not receive unlimited permission to invent arbitrary HTML or
execute arbitrary code. A production generative UI system should work more like
this:

1. The developer defines safe components such as `MetricCard`, `IncidentTable`,
   `ActionButton`, `Form`, `Chart`, or `Timeline`.
2. Each component has typed props, validation rules, and rendering behavior
   owned by the application.
3. The model is instructed to compose only those components.
4. The model emits a structured UI format.
5. A renderer parses the model output and renders actual application components.
6. User actions flow back into trusted application code, not arbitrary
   model-generated scripts.

That means the model controls composition, not authority. It can decide that a
table plus action tray is better than a paragraph, but it cannot bypass the
product's permission model or invent a destructive operation.

This distinction matters because "AI-generated UI" can otherwise mean too many
things. It can mean a screenshot mockup, a design-to-code tool, a template
picker, a static page generator, or an LLM that writes JSX. Generative UI for
live applications is narrower and more useful: runtime composition of trusted
components from model output.

## The Spectrum From Text to Generated Interfaces

It helps to see generative UI as one point on a spectrum.

Plain text is the simplest output. The model explains the answer and the user
manually acts on it. This works for summaries, advice, and simple questions.

Markdown adds structure. Lists, headings, code blocks, and tables improve
readability, but they are still mostly inert. A Markdown table cannot validate
edits or call a backend action by itself.

Tool calling lets the model ask the app to do something. The model can call
`getInvoices()` or `createTicket()`, and the application can render the result.
This is a major improvement, but the UI is usually still predetermined by the
developer.

Template selection lets the model choose between prebuilt views. This is useful
when the product has a known set of flows, but it breaks down when the user's
context changes faster than the template library.

Generative UI lets the model compose a fit-for-purpose interface from safe
primitives. The app still owns the primitives. The model chooses the
arrangement, emphasis, and supporting context.

The last step is the interesting one. It changes the developer's job from
"prebuild every answer screen" to "design the component vocabulary and runtime
constraints that make good answers renderable."

## A Small Example

Suppose you are building a support copilot. A customer asks:

> Why was my last invoice higher than usual?

A text response can explain the reason:

```txt
Your invoice increased because your team added 12 seats on May 4
and crossed the usage tier for API calls.
```

A generative UI response can show:

- the invoice delta,
- the exact seat-change event,
- the usage threshold crossing,
- a line chart of daily API calls,
- a button to email the billing owner,
- and a dispute form if the customer thinks the data is wrong.

The developer might define a billing-focused library:

```tsx
import { z } from "zod";
import { createLibrary, defineComponent } from "@openuidev/react-lang";

const InvoiceDelta = defineComponent({
  name: "InvoiceDelta",
  props: z.object({
    previousAmount: z.number(),
    currentAmount: z.number(),
    currency: z.string(),
    reason: z.string(),
  }),
  component: ({ props }) => <InvoiceDeltaCard {...props} />,
});

const UsageChart = defineComponent({
  name: "UsageChart",
  props: z.object({
    metric: z.string(),
    points: z.array(
      z.object({
        date: z.string(),
        value: z.number(),
      }),
    ),
  }),
  component: ({ props }) => <UsageChartView {...props} />,
});

const BillingAction = defineComponent({
  name: "BillingAction",
  props: z.object({
    label: z.string(),
    actionId: z.enum(["email_owner", "open_dispute", "download_invoice"]),
  }),
  component: ({ props }) => <BillingActionButton {...props} />,
});

export const billingLibrary = createLibrary({
  root: "BillingExplanation",
  components: [InvoiceDelta, UsageChart, BillingAction],
});
```

The specific component names here are illustrative, but the contract is the
point. The model gets a constrained set of interface pieces. The app owns how
those pieces render and what their actions are allowed to do.

That is safer and more useful than asking a model to produce raw JSX. It also
scales better than hardcoding every possible invoice explanation view.

## The Model Should Compose, Not Escape

The temptation with AI interfaces is to make the model too powerful. Let it
write markup. Let it write event handlers. Let it decide which API endpoint to
call. Let it produce arbitrary code.

That is usually the wrong boundary.

In a healthy generative UI system, the model should compose. The application
should execute.

The model can say:

```txt
Show an invoice delta, then a usage chart, then an action button for opening a dispute.
```

The application decides:

- whether the user can see billing data,
- which invoice records are available,
- what an `open_dispute` action actually does,
- whether the button is disabled,
- how the component behaves on mobile,
- how errors are shown,
- and how analytics or audit logs are recorded.

This keeps generative UI aligned with normal product engineering. The model adds
adaptability, but the app still owns trust.

## What Developers Still Own

Generative UI does not remove frontend engineering. It moves the hard parts.

Developers still own component design. If the component library is vague,
inconsistent, or too low-level, the model will compose awkward interfaces. A
model given `Div`, `Text`, `Button`, and `Input` has too much room to improvise.
A model given product-level components such as `ApprovalCard`, `InvoiceDelta`,
`RiskPanel`, and `DataTable` has a clearer vocabulary.

Developers still own state. Streaming UI has to handle partial output, loading
regions, stale data, retries, and action results. The model can propose an
action, but the application has to decide how the UI changes after the action
succeeds or fails.

Developers still own accessibility. A generated interface must still have usable
labels, focus order, keyboard behavior, color contrast, and predictable
semantics. Component constraints are the best place to enforce this.

Developers still own security. The model should not invent privileged
operations, leak hidden data into props, or turn a harmless summary into an
unsafe action. The renderer and action layer need explicit allowlists.

Developers still own product taste. Generated UI can be adaptive without being
chaotic. The more your components encode product decisions, the less the model
has to guess.

## Where OpenUI Fits

[OpenUI](https://github.com/thesysdev/openui) is useful because it treats
generative UI as an application runtime problem, not only a prompting trick. Its
public docs describe the core loop: define a component library, generate system
prompt instructions from that library, have the LLM respond in OpenUI Lang, then
parse and render the result as UI.

That loop matters because each step is a control point.

The component library defines what the model can use. The generated prompt keeps
the model aligned with that vocabulary. OpenUI Lang gives the model a compact
structured output format designed for streaming. The renderer turns that output
into real UI as tokens arrive.

The result is not "the model wrote your frontend." The result is closer to "the
model selected and arranged trusted frontend capabilities at runtime."

That framing is more practical for teams that already have a design system, a
backend, permissions, observability, and user workflows to protect.

## When Generative UI Is Worth It

Generative UI is strongest when the response shape depends heavily on context.

Use it for workflows where the user might need a chart in one case, a table in
another, and a form in a third. Use it when the model has to summarize, compare,
and propose action in the same surface. Use it when users ask open-ended
questions but still need structured next steps.

Good candidates include:

- internal copilots,
- analytics assistants,
- customer support tools,
- sales and CRM workflows,
- incident response surfaces,
- research assistants,
- onboarding flows,
- and agent review or approval interfaces.

Generative UI is less useful when the interface is already fixed. A checkout
page, account settings screen, or compliance report may benefit from AI
assistance, but it usually should not be dynamically composed by a model.
Predictability matters more than adaptability there.

A simple rule: if your team can name the exact screen ahead of time, build the
screen. If the right screen depends on the user's question, data shape,
permissions, and next action, generative UI becomes more interesting.

## The Failure Modes Are Different

Text-only AI has familiar failure modes: hallucinated facts, vague summaries,
missing citations, and overconfident recommendations.

Generative UI adds interface-specific failure modes:

- the model chooses the wrong component,
- important data is hidden in a secondary region,
- actions appear before the user has enough context,
- a streamed partial state looks final,
- a component prop fails validation,
- or the UI becomes too dynamic for users to build trust.

These are solvable, but they are not solved by prompting alone. They require
component validation, fallback rendering, design-system constraints, action
review, and observability.

That is why the runtime contract matters. The model is one part of the system,
not the whole system.

## How to Start Without Overbuilding

The easiest way to start is not to make your entire app generative. Pick one
response surface where text is already failing.

For example:

1. Take a current AI answer that often becomes a long explanation.
2. Identify the three interface pieces users wish they had.
3. Build those pieces as constrained components.
4. Let the model compose only those components.
5. Log invalid generations and user actions.
6. Add guardrails where the model makes poor layout or action choices.

Do not expose your whole design system on day one. Start with product-level
components that match a real workflow. A small component vocabulary produces
better outputs than a giant, generic one.

The goal is not novelty. The goal is to reduce the distance between
understanding and action.

## The Real Shift

The first wave of AI apps proved that models can answer questions. The next wave
has to prove that models can help users act.

Text will still matter. Explanations, summaries, and reasoning traces are not
going away. But many AI answers are trying to be interfaces while trapped inside
prose.

Generative UI gives those answers a better shape. It lets the model return an
interactive surface instead of a paragraph pretending to be one.

The best version of this future is not uncontrolled model-generated screens. It
is a disciplined runtime where developers define the vocabulary, the model
composes within it, and the application keeps ownership of state, actions,
permissions, and quality.

That is why generative UI is not just a new output format. It is a new contract
for AI application development.
