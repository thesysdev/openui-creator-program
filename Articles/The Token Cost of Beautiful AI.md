# The Token Cost of Beautiful AI: OpenUI Lang vs. AI SDK vs. JSON

Generative UI has an awkward cost problem: the prettier the interface, the more
structure the model has to emit.

A text-only assistant can answer with a paragraph. A UI-generating assistant has
to describe cards, tables, fields, actions, layout, validation hints, and
sometimes component state. If that structure is verbose, every generated
interface quietly increases latency and model spend.

This is why output format matters. A team can have the right model, a good
component library, and a thoughtful interaction design, then still pay
unnecessary token tax because the model is asked to generate repeated JSON keys
for every node in the component tree.

This article compares three common ways to represent generated UI:

- Raw JSON component trees.
- AI SDK-style tool output that gets mapped to React components.
- OpenUI Lang as a compact, streaming-oriented UI language.

The goal is not to declare one option universally better. JSON is still the best
default for many APIs. AI SDK UI is a practical way to wire tool results into
React. OpenUI Lang is strongest when the model itself needs to compose an
interface and stream it progressively.

The question is narrower: when the output is UI, what are you actually paying
for?

## The Three Shapes

Let's use a simple support dashboard as the running example. The assistant needs
to return two metrics, a table, and one action card.

In a raw JSON component tree, the model often emits something like this:

```json
{
  "component": "Dashboard",
  "props": {
    "title": "Escalation risk",
    "children": [
      {
        "component": "MetricCard",
        "props": {
          "label": "Open tickets",
          "value": 42,
          "trend": "up",
          "change": "+18%"
        }
      },
      {
        "component": "Table",
        "props": {
          "columns": ["Account", "SLA", "Owner", "Next action"],
          "rows": [["Acme", "2h overdue", "Rina", "Escalate to success lead"]]
        }
      }
    ]
  }
}
```

This is explicit and easy to parse, but the model pays for every repeated
`"component"`, `"props"`, quote, colon, and wrapper object. The more deeply
nested the UI becomes, the more those repeated tokens dominate the response.

AI SDK UI takes a different route. The model calls a tool. Your application
executes the tool, receives structured data, and maps the result to a React
component. The AI SDK docs describe this as connecting tool-call results to
React components in the chat UI.

That shape is excellent when the interface is known ahead of time:

```json
{
  "toolName": "renderSupportDashboard",
  "toolCallId": "call_support_001",
  "state": "output-available",
  "input": {
    "accountSegment": "enterprise",
    "includeActionCard": true
  },
  "output": {
    "openTickets": 42,
    "atRiskAccounts": 7,
    "rows": [
      {
        "account": "Acme",
        "sla": "2h overdue",
        "owner": "Rina",
        "nextAction": "Escalate to success lead"
      }
    ]
  }
}
```

The model does not have to invent arbitrary layout. It chooses a tool, fills the
parameters, and the application owns rendering. This makes AI SDK UI a good fit
for product teams that want controlled interfaces with predictable component
boundaries.

OpenUI Lang is aimed at the case where the model is composing the UI directly
from a known component vocabulary. The same response can be much more compact:

```text
dashboard "Escalation risk" {
  metric "Open tickets" 42 trend=up change="+18%"
  metric "At-risk accounts" 7 trend=up change="+3"
  table columns=["Account","SLA","Owner","Next action"] [
    ["Acme","2h overdue","Rina","Escalate to success lead"]
    ["Northwind","45m left","Mateo","Send workaround"]
    ["Globex","3h left","Ari","Confirm patch ETA"]
  ]
  actionCard "Recommended action"
    body="Notify owners for Acme and Northwind before the next standup."
    action="Draft owner update"
}
```

The renderer still needs to validate, map, and constrain this output. The
difference is that the model no longer has to repeat a full object envelope for
every component.

## How I Measured It

I added a small benchmark script in this PR:

```bash
npx -y -p js-tiktoken -c "node benchmarks/token-cost-comparison.mjs"
```

The script defines three equivalent UI scenarios:

- A support dashboard with metrics, a table, and an action card.
- A plan comparison UI with three pricing cards.
- An incident intake form with validation hints.

For each scenario, it counts tokens for:

- A raw JSON component tree.
- An AI SDK-style tool-output payload.
- An OpenUI Lang representation.

The script uses `js-tiktoken` with the `gpt-4o` tokenizer family. The exact
numbers are not meant to replace production traces, because your real prompt,
component names, field names, and validation strategy will differ. The point is
to make the comparison reproducible and easy to challenge.

Here is the measured output:

- `support-ticket-summary`: 177 JSON tokens, 143 AI SDK-style tokens, and 137
  OpenUI Lang tokens. That is 22.6% fewer than JSON and 4.2% fewer than the AI
  SDK-style payload.
- `plan-comparison`: 133 JSON tokens, 147 AI SDK-style tokens, and 97 OpenUI
  Lang tokens. That is 27.1% fewer than JSON and 34.0% fewer than the AI
  SDK-style payload.
- `incident-intake-form`: 160 JSON tokens, 184 AI SDK-style tokens, and 97
  OpenUI Lang tokens. That is 39.4% fewer than JSON and 47.3% fewer than the AI
  SDK-style payload.
- `total`: 470 JSON tokens, 474 AI SDK-style tokens, and 331 OpenUI Lang tokens.
  That is 29.6% fewer than JSON and 30.2% fewer than the AI SDK-style payload.

This benchmark is intentionally conservative. It does not use an especially deep
component tree, and the JSON examples are reasonably compact. OpenUI's own
benchmark page reports larger savings in broader comparisons, including up to
67.1% fewer tokens than Vercel JSON-Render and 65.4% fewer than Thesys C1 JSON.
The smaller number here is still meaningful because it comes from everyday UI
shapes, not a best-case stress test.

## What That Means in Dollars

OpenAI prices GPT-4.1 mini output at $1.60 per 1 million tokens at the time of
writing. Using that price only as a simple cost model, the combined
three-scenario payloads would cost:

- Raw JSON component tree: 470 tokens per combined response, or $752.00 at 1
  million responses per month.
- AI SDK-style tool output: 474 tokens per combined response, or $758.40 at 1
  million responses per month.
- OpenUI Lang: 331 tokens per combined response, or $529.60 at 1 million
  responses per month.

That is about $222 per month saved per million generated UI responses in this
small benchmark.

The absolute number may not matter for a prototype. It matters quickly when:

- You generate UI for every chat turn, not just occasional tool results.
- Your component trees include nested cards, charts, filters, forms, and tables.
- You serve high-volume support, commerce, analytics, or internal operations
  workflows.
- You stream partial UI and care about time-to-first-render.

Token cost is not just cloud spend. Fewer output tokens usually also means less
time waiting for the model to finish describing the interface.

## Why JSON Gets Expensive

JSON is great at being unambiguous. It is less great at being terse.

A component tree encoded as JSON repeats the same structural words constantly:

- `component`
- `props`
- `children`
- `type`
- `label`
- `value`
- `items`

Those keys are useful to a parser, but they are not useful to a user. Once the
renderer already knows the component vocabulary, the model does not need to
restate the full schema shape every time.

The repeated envelope becomes especially expensive in nested layouts. A card
inside a tab inside a panel inside a dashboard can require four or five layers
of objects before the model emits the actual user-facing data.

JSON also has a streaming problem. It can be streamed as bytes, but a partial
JSON document is not a valid JSON document until enough closing brackets arrive.
You can build an incremental parser, but now your application is compensating
for the format.

OpenUI Lang is line-oriented and designed for progressive UI output. The syntax
makes it easier for the renderer to work with partial statements and completed
component boundaries as the model generates them.

## Where AI SDK UI Wins

AI SDK UI should not be dismissed as "more JSON." It solves a different problem.

The AI SDK generative UI pattern works well when your product already knows the
UI variants. For example:

- Weather card.
- Stock quote card.
- Order tracking card.
- Calendar availability picker.
- Customer profile panel.

In those cases, the model's job is to decide which tool to call and provide
typed inputs. Your app owns the component. That gives you strong control over
design, accessibility, auth boundaries, and error handling.

The token cost can also be excellent when the tool result is small. If the model
only says "call `displayWeather` with `location=San Francisco`," the expensive
UI tree never appears in model output.

The cost rises when tool output becomes the UI description itself. If your tool
payload starts carrying large arrays of rows, field configs, nested card
definitions, or dynamic layout metadata, it begins to look like another JSON UI
tree.

So the practical rule is:

- Use AI SDK UI when the model chooses among known interface types.
- Use a compact UI language when the model composes the interface itself.

These patterns can also coexist. A product can use AI SDK tools for high-trust
actions and OpenUI Lang for low-risk, dynamic presentation.

## Where OpenUI Lang Wins

OpenUI Lang is strongest when the UI is not just "show this one card." It is
strongest when the model needs to assemble a purpose-built interface from
components.

Examples:

- A support assistant that renders different dashboards depending on account
  risk.
- A sales assistant that builds a plan comparison from buyer constraints.
- An operations copilot that generates an incident form with validation and
  routing hints.
- A data assistant that chooses a chart, a table, and a short summary based on
  the user's question.

In those cases, JSON makes the model describe implementation scaffolding. OpenUI
Lang lets it describe the interface more directly.

The support dashboard from the benchmark is the clearest example. The raw JSON
response used 177 tokens. The OpenUI Lang response used 137. That is not a
dramatic win by itself, but it is enough to matter at scale, and the gap usually
widens as the UI gets more deeply nested.

The incident form showed a bigger difference: 160 JSON tokens vs. 97 OpenUI
tokens. Forms are full of repeated keys. Each field has a type, name, label,
required flag, options, and hints. A concise language can represent those
constraints without repeating the full object grammar each time.

## The Costs the Token Table Does Not Show

Token count is only one axis. It should not be the only architecture decision.

Raw JSON is easy to validate with standard tooling. If your team needs strict
schema validation, existing JSON Schema infrastructure, or compatibility with
non-React renderers, JSON may be worth the extra tokens.

AI SDK UI is ergonomic for React teams that already use the AI SDK. It keeps
rendering code close to the application and encourages controlled tool
boundaries. For many production apps, that is more important than shaving tokens
from the output.

OpenUI Lang asks you to adopt a dedicated language and renderer. That is a real
tradeoff. You need to define the component vocabulary, validate model output,
decide fallback behavior, and test malformed or partial responses.

The upside is that those are the same problems every serious generative UI app
has to solve anyway. OpenUI gives those problems a first-class representation
instead of hiding them in ad hoc JSON blobs.

## A Decision Framework

Use raw JSON when:

- Your schema is stable and shared across systems.
- Existing validators, logs, and contracts already expect JSON.
- The UI output is small enough that token overhead is irrelevant.
- You care more about interoperability than streaming UI composition.

Use AI SDK UI when:

- The model should call known tools.
- Your React components already exist.
- You want tight control over rendering.
- The model should not invent arbitrary layout.

Use OpenUI Lang when:

- The model needs to compose the interface from a component library.
- Responses include nested UI, tables, forms, dashboards, or workflows.
- Streaming and time-to-first-render matter.
- Token overhead is visible in cost or latency.

The wrong conclusion is "JSON bad, OpenUI good." The better conclusion is that
UI output has a shape, and the cheapest reliable shape depends on who owns
composition: the model, the tool layer, or the application.

## The Bottom Line

Beautiful AI interfaces are not free. Every generated card, field, table, and
action has to be represented somehow, and that representation becomes part of
your model bill.

In the benchmark included with this article, OpenUI Lang used 29.6% fewer tokens
than a compact JSON component tree and 30.2% fewer tokens than an AI SDK-style
tool-output payload across three common UI scenarios. OpenUI's published
benchmark numbers show even larger savings in broader UI representations.

That does not make OpenUI Lang the default for every app. It does make a strong
case for treating UI output format as an architecture decision, not an
implementation detail.

If your assistant only needs to call a weather tool and render a weather card,
AI SDK UI is a clean fit. If your assistant is building custom dashboards,
forms, comparisons, and workflows on the fly, the output language becomes part
of your product's performance profile.

The more your AI product looks like software instead of chat, the more expensive
it becomes to describe that software in a verbose format.

## References

- [OpenUI documentation][openui-docs]
- [OpenUI Lang benchmarks][openui-benchmarks]
- [AI SDK UI generative interfaces][ai-sdk-ui]
- [AI SDK RSC status][ai-sdk-rsc]
- [OpenAI GPT-4.1 mini model pricing][gpt-41-mini-pricing]

[openui-docs]: https://www.openui.com/docs
[openui-benchmarks]: https://www.openui.com/docs/openui-lang/benchmarks
[ai-sdk-ui]: https://ai-sdk.dev/docs/ai-sdk-ui/generative-user-interfaces
[ai-sdk-rsc]: https://ai-sdk.dev/docs/ai-sdk-rsc
[gpt-41-mini-pricing]: https://platform.openai.com/docs/models/gpt-4.1-mini
