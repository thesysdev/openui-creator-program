# 5 Things That Look Terrible as Plain Text (And How OpenUI Fixes Them)

Most AI product demos still end the same way: the model returns a wall of text, the user scans it, and the product quietly hopes the answer was simple enough to read.

That works for a paragraph, a short summary, or a quick command. It falls apart when the answer has structure.

Ask an assistant to compare plans, build an itinerary, explain a bug report, or collect shipping details, and plain text starts pretending to be an interface. It uses bullets where the product needs cards. It uses Markdown tables where the user needs sorting, filtering, and actions. It uses prose where the next step should be a button.

Generative UI changes the output contract. Instead of only generating words about an interface, the model can generate a structured interface that your app renders with real components. [OpenUI](https://www.openui.com/) gives that contract a practical shape: you define the components the model is allowed to use, OpenUI turns that library into model instructions, the model responds in OpenUI Lang, and the renderer parses that output into UI as it streams.

Here are five common AI responses that look bad as plain text, and what they become when the model can respond with OpenUI.

## 1. Product comparisons

Product comparison is one of the fastest ways to expose the weakness of text-only responses.

The user does not want a paragraph. They want to compare tradeoffs, scan attributes, notice missing information, and act on the winning option.

### Plain text version

```text
Option A is cheaper at $19 per month and includes 5 seats, but it does not include audit logs.
Option B is $49 per month and includes 20 seats, SSO, and audit logs.
Option C is $99 per month and includes unlimited seats, SSO, audit logs, and priority support.

For a small team, Option B is probably the best fit because it includes security features while staying below the enterprise price.
```

This is readable, but it is not usable. The important data is trapped inside sentences. If the user wants to compare only seat count or security features, they have to reread the whole answer.

Markdown tables help, but only a little:

```markdown
| Plan | Price | Seats | SSO | Audit logs |
|---|---:|---:|---|---|
| A | $19 | 5 | No | No |
| B | $49 | 20 | Yes | Yes |
| C | $99 | Unlimited | Yes | Yes |
```

That is better for scanning, but it is still static text. There is no selected recommendation, no upgrade action, no warning state, and no way to collapse details.

### OpenUI version

With OpenUI, the answer can be rendered as a comparison surface:

- Three plan cards with price, seat count, and feature badges
- A highlighted recommendation
- Inline caveats for missing requirements
- A "Select plan" action on each card
- A compact table view for users who want density

The model output is no longer just a description of the decision. It becomes the decision UI.

At a high level, the app might expose components like this:

```tsx
const PlanCard = defineComponent({
  name: "PlanCard",
  props: z.object({
    name: z.string(),
    price: z.string(),
    seats: z.string(),
    features: z.array(z.string()),
    missing: z.array(z.string()).optional(),
    recommended: z.boolean().optional(),
  }),
  component: ({ props }) => <PlanCardView {...props} />,
})
```

Now the model is choosing from product-safe building blocks. It can output a comparison, but the final UI still comes from your design system.

The difference is not cosmetic. It changes the work the user has to do. Instead of converting prose into a decision, the user starts from a decision-ready layout.

## 2. Forms and intake flows

Forms are especially awkward in plain text because the model can describe the fields, but the user still has to move somewhere else to complete the task.

### Plain text version

```text
To create the support ticket, I need:

1. Your account email
2. The affected workspace
3. The issue category
4. A short description
5. Whether this is blocking production

Please reply with those details.
```

This is the chatbot equivalent of handing someone a clipboard with no boxes on it.

The user has to format the response correctly. The app has to parse the response later. If the user skips a field, the assistant has to ask again. If the user types "yes" ambiguously, the app has to infer what that means.

### OpenUI version

The assistant can render the intake step as an actual form:

- Email input
- Workspace selector
- Category dropdown
- Textarea
- Production-blocking toggle
- Submit button

The result is faster and less error-prone because the UI constrains the answer before it becomes data.

The OpenUI component library controls the available field types:

```tsx
const SupportTicketForm = defineComponent({
  name: "SupportTicketForm",
  props: z.object({
    categories: z.array(z.string()),
    defaultPriority: z.enum(["low", "normal", "high"]).optional(),
  }),
  component: ({ props }) => <SupportTicketFormView {...props} />,
})
```

The model can decide that a support ticket form is the right response, but it cannot invent arbitrary client-side code. That boundary matters. Generative UI should not mean "let the model execute whatever it wants." It should mean "let the model compose approved UI primitives."

This is where OpenUI's approach is practical: the component definitions act as a contract between the model and the application.

## 3. Search results and recommendations

Search results are another place where plain text creates unnecessary friction.

Imagine asking an internal assistant:

```text
Find docs about our billing retry behavior.
```

### Plain text version

```text
I found three relevant documents:

1. Billing retries overview - explains retry timing and dunning emails.
2. Payment provider error codes - lists card and bank transfer failures.
3. Subscription state machine - describes how accounts move from active to past_due to canceled.

The first one is probably the best starting point.
```

This tells the user what exists, but it does not behave like search.

Real search results need metadata. They need timestamps, owners, relevance, source systems, snippets, and actions. A paragraph hides all of that.

### OpenUI version

An OpenUI response can render a result list:

- Document title
- Matched snippet
- Owner or team
- Last updated date
- Confidence or relevance indicator
- "Open", "Copy link", and "Summarize" actions

The assistant can also adapt the surface to the query. A troubleshooting query might show runbooks first. A policy query might emphasize version dates. A code search query might group results by repository.

This is a better fit for how people actually use search. They rarely consume every result in order. They scan, filter, compare, and branch.

Plain text makes the model narrate the result set. Generative UI lets the model arrange the result set.

## 4. Data dashboards

Dashboards are almost never improved by being flattened into prose.

### Plain text version

```text
Revenue increased from $82,000 in January to $91,000 in February and $104,000 in March.
Churn also increased from 2.1% to 2.8%.
Expansion revenue is up 18%.
The main concern is that churn is rising while revenue is growing.
```

This is a useful summary, but it is a poor dashboard.

The user cannot see the trend shape. They cannot compare churn and revenue visually. They cannot inspect outliers. They cannot switch time ranges. They cannot tell whether the assistant is describing a stable pattern or one noisy month.

### OpenUI version

The same answer can become:

- KPI tiles for revenue, churn, expansion, and net retention
- A line chart for monthly recurring revenue
- A warning badge on churn
- A short generated insight beside the chart
- A time-range control
- A drill-down action for accounts that churned

The prose still matters, but it becomes commentary attached to the data instead of the only way to access it.

This is the important design pattern: OpenUI does not remove language. It moves language into the right role.

Text is good at explaining why something matters. UI is good at showing what changed, what can be clicked, and what the user should inspect next.

When the output is a dashboard, text should not carry the whole interface.

## 5. Multi-step plans

AI assistants are often asked to produce plans: migration plans, launch plans, onboarding plans, incident response plans, and learning plans.

Plain text can list steps, but it struggles with progress, ownership, dependencies, and state.

### Plain text version

```text
Here is a migration plan:

1. Inventory current API routes.
2. Identify routes that depend on legacy auth.
3. Add compatibility middleware.
4. Move one low-risk route first.
5. Run regression tests.
6. Roll out route groups gradually.
7. Remove legacy auth once usage reaches zero.
```

This is fine as a note. It is weak as an operating surface.

The moment the user asks "what is blocked?" or "which step should I do today?", the assistant has to regenerate more text.

### OpenUI version

A generated plan can render as:

- A timeline
- Task cards with owners
- Dependency indicators
- Risk labels
- Checkboxes or status controls
- A "generate implementation issue" action

That changes the plan from something the user reads into something the user can run.

For example, a migration plan component might accept structured steps:

```tsx
const MigrationPlan = defineComponent({
  name: "MigrationPlan",
  props: z.object({
    title: z.string(),
    steps: z.array(
      z.object({
        label: z.string(),
        owner: z.string().optional(),
        risk: z.enum(["low", "medium", "high"]),
        blockedBy: z.array(z.string()).optional(),
      })
    ),
  }),
  component: ({ props }) => <MigrationPlanView {...props} />,
})
```

Again, the model composes. Your product renders. The user gets an interface that carries state.

## Why plain text keeps showing up anyway

Plain text is the default because it is easy.

Every model can produce it. Every chat box can display it. Every developer can ship it without designing a rendering contract.

But once AI output becomes part of a real workflow, plain text starts creating downstream work:

- Users manually copy values into forms.
- Developers write brittle parsers for model responses.
- Product teams add custom renderers one use case at a time.
- Assistants explain actions instead of presenting actions.
- Structured data gets flattened and then reconstructed later.

That is the hidden cost of text-only AI interfaces. The implementation starts simple, but the workflow grows around it until the team is maintaining a pile of special cases.

Generative UI is a way to make the structure explicit earlier.

## What OpenUI adds

OpenUI is not just "prettier chatbot output."

The useful part is the contract:

1. You define a component library.
2. OpenUI generates model instructions from that library.
3. The model responds in OpenUI Lang.
4. The renderer parses and renders the UI progressively.

That contract gives product teams a middle ground between two bad options:

- Free-form text that cannot reliably drive an interface
- Arbitrary generated code that is too risky to run directly

With OpenUI, the assistant can generate structured UI while the application keeps control over the components, props, styling, state, and actions.

That is why the "after" examples above are not just nicer layouts. They are safer and more maintainable product primitives.

## When text is still the right answer

Not every response needs UI.

If the user asks "what does this error mean?", a direct explanation is often best. If they ask for a summary, a paragraph might be perfect. If they ask for a command, a code block is probably enough.

The mistake is treating those cases as proof that every answer should be text.

A better rule is:

- Use text for explanation.
- Use UI for comparison.
- Use UI for input.
- Use UI for state.
- Use UI for actions.
- Use both when the user needs context and control.

That is where generative UI feels less like a novelty and more like the natural next layer of AI application design.

## The takeaway

Plain text is a good output format for language.

It is a bad output format for interfaces.

The moment an AI response contains products, forms, search results, dashboards, or plans, the model is already describing a UI. OpenUI lets your application render that UI directly, using components you define and control.

That is the shift: not from text to decoration, but from text-only answers to workflow-ready interfaces.

The best AI apps will still talk. They will just stop forcing every answer to look like a paragraph.

## Further reading

- [OpenUI website and playground](https://www.openui.com/)
- [OpenUI GitHub repository](https://github.com/thesysdev/openui)
- [OpenUI documentation](https://www.openui.com/docs)
