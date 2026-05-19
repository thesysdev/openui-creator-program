# The Token Cost of Beautiful AI: A Reproducible OpenUI Benchmark

Generative UI has a simple promise: a model should not be limited to paragraphs
when the user needs a table, a form, a chart, a card, or a workflow surface.

That promise is attractive. It is also easy to overstate.

The moment an AI product starts asking a model to describe UI, token cost
becomes part of the product architecture. A text answer might be 120 tokens. A
small interface description might be 300. A full dashboard with repeated JSON
keys, action metadata, validation state, and tool-call envelopes can grow much
faster than the team expects.

So the useful question is not:

> Is OpenUI always cheaper than JSON?

The useful question is:

> What exactly are you paying for when a model returns UI?

I built a small benchmark harness for this article so the answer is inspectable.
The fixture set compares three ways to represent the same generated interface:

- OpenUI Lang,
- compact JSON,
- and an AI SDK-style tool-call envelope.

The numbers are intentionally modest. That is the point. Token cost should be
measured with fixtures that look like your product, not accepted as a slogan.

## The Three Shapes Being Compared

There are many ways to build generative UI, but most implementations fall into
one of three response shapes.

The first is a UI-native language. In OpenUI Lang, the model emits a compact
component-oriented description. The output looks closer to JSX than to a raw
data tree:

```jsx
<Panel title="Renewal risk review">
  <Metric label="At-risk ARR" value="$184k" tone="warning" />
  <Table columns={["Account","Risk","Reason","Action"]} rows={[
    ["Northstar","High","No exec sponsor","Schedule call"],
    ["Luma","Medium","Usage down 23%","Send playbook"]
  ]} />
</Panel>
```

The second is compact JSON. This is the baseline many teams already understand:

```json
{"component":"Panel","props":{"title":"Renewal risk review","children":[{"component":"Metric","props":{"label":"At-risk ARR","value":"$184k","tone":"warning"}}]}}
```

The third is a tool-call envelope. This is common when teams build generated UI
through an orchestration layer. The model does not just return the interface;
it calls a tool that renders the interface:

```json
{"toolCallId":"call_renewal_review","toolName":"renderComponent","args":{"component":"Panel","props":{"title":"Renewal risk review"}}}
```

That envelope is useful. It gives the runtime a declared action boundary. It can
carry IDs, schemas, and tool metadata. But those wrapper fields are not free.

## Methodology

The benchmark in `benchmarks/token_cost_comparison.py` uses `tiktoken` with the
`o200k_base` encoding. It compares three equivalent fixtures:

1. A renewal-risk review surface with a metric, table, and actions.
2. An onboarding checklist with a nested invite form.
3. A support triage board with a summary, kanban columns, and an escalation
   button.

The JSON fixtures are minified before counting. That matters. Pretty-printed
JSON would exaggerate the difference, and teams should not make architecture
decisions from artificially padded examples.

You can reproduce the counts with:

```bash
python3 -m pip install tiktoken
python3 benchmarks/token_cost_comparison.py
```

The current output is:

| Fixture | OpenUI Lang | Compact JSON | AI SDK-style tool envelope |
| --- | ---: | ---: | ---: |
| Renewal risk review | 114 | 123 | 156 |
| Onboarding checklist | 84 | 82 | 132 |
| Support triage | 102 | 117 | 123 |
| **Total** | **300** | **322** | **411** |

Across this fixture set, OpenUI Lang is:

- 6.8% smaller than compact JSON,
- and 27.0% smaller than the AI SDK-style tool envelope.

The most important part of that result is not the headline number. It is the
shape of the difference.

## Why Compact JSON Is Harder to Beat Than People Think

If JSON is carefully minified and the payload is small, it can be surprisingly
competitive. In the onboarding checklist fixture, the compact JSON version is
slightly smaller than the OpenUI Lang version.

That does not make JSON the winner. It means "JSON is verbose" is an incomplete
argument.

JSON becomes expensive when the output repeats object keys:

- `component`,
- `props`,
- `children`,
- `type`,
- `label`,
- `status`,
- `action`,
- `metadata`.

A table represented as an array of objects repeats the same keys on every row. A
nested component tree repeats `component` and `props` at every level. A tool-call
format adds `toolName`, `toolCallId`, `args`, and usually more schema metadata
around the actual UI.

OpenUI Lang is cheaper when the same structure can be expressed positionally or
as component syntax. Tables can use arrays. Components do not need repeated
`component` and `props` keys. The model output can be closer to the thing being
rendered.

But if your JSON is already compact, flat, and sparse, the savings may be
modest. That is a feature of an honest benchmark, not a problem for OpenUI.

## The Bigger Cost Is the Runtime Contract

Token count is only one cost.

Raw JSON still leaves the application with a question: what does this JSON mean?
The answer usually becomes a private schema, a renderer, validation rules, error
handling, and custom action mapping. That work can be fine for one product. It
becomes expensive when every team invents a different UI description format.

AI SDK-style tool calls solve a different problem. They make the model's action
boundary explicit. That is useful for orchestration, logging, and safety. The
tradeoff is that the UI description sits inside a wrapper that may not be
optimized for visual output.

OpenUI's bet is that generated interfaces deserve their own language and
renderer. The token savings matter, but the larger value is the contract:

- the model emits a constrained UI description,
- the host app owns the component library,
- the renderer turns the description into real React components,
- actions still flow through application-owned handlers,
- and the output can stream before the whole response is complete.

That contract is what makes the token cost easier to reason about.

## Cost Projection

Small savings become meaningful at scale, especially when every assistant turn
can produce UI.

Using the benchmark totals:

- compact JSON costs 322 output tokens per generated UI,
- the AI SDK-style envelope costs 411 output tokens,
- OpenUI Lang costs 300 output tokens.

At one million generated UI responses, OpenUI saves 22 million output tokens
against compact JSON in this fixture set. Against the tool-call envelope, it
saves 111 million output tokens.

The dollar value depends on the model. The architecture point does not. If the
product emits generated UI constantly, the response representation becomes a
recurring infrastructure cost.

Teams should run this math with their own fixtures:

```txt
monthly_saved_tokens =
  monthly_ui_generations * (baseline_tokens - openui_tokens)
```

If the answer is small, choose based on developer experience and safety. If the
answer is large, the response language deserves the same attention as caching,
streaming, and model selection.

## Streaming Changes the Evaluation

Token count is not the whole performance story.

A JSON object often needs enough structure to be complete before the app can
parse and render it safely. A tool-call envelope may need the full tool call
before the renderer knows what to do. UI-native formats can be designed around
incremental rendering: components arrive, partial trees stabilize, and the app
can show useful state before the final token lands.

That does not mean every OpenUI response is magically instant. The app still
needs guardrails, error boundaries, component validation, and action validation.
But the format is aligned with the thing users actually see.

For users, that can matter more than the raw token count. A 300-token response
that starts rendering early can feel faster than a 250-token response that
renders only after validation succeeds.

## When Each Approach Wins

Use compact JSON when the UI is simple, internal, and tightly controlled. If the
product needs one or two generated cards, a custom JSON schema may be enough.

Use tool-call envelopes when orchestration is the main problem. If the model is
choosing among many tools and UI rendering is one side effect among several,
the extra wrapper fields may be worth the clarity.

Use OpenUI when the generated interface is the product experience. If the user
is expected to inspect, compare, approve, edit, or act on the response, a
UI-native representation gives the model a better output target and gives the
application a clearer rendering contract.

The strongest case for OpenUI is not "JSON bad." It is:

> Generated UI should have a first-class interface language, because UI is not
> just data.

## What to Benchmark Before Choosing

Before adopting any generated UI format, build fixtures from real product tasks.
Do not benchmark toy buttons.

Use at least these cases:

- a dense table with repeated rows,
- a form with validation and disabled states,
- a dashboard with metrics, charts, and actions,
- a review workflow with confidence and evidence,
- and a long-running task state with progress, errors, and recovery actions.

Then measure:

- output tokens,
- time to first visible UI,
- parse and validation failure rate,
- number of renderer fallbacks,
- model repair turns,
- and the complexity of action handling.

That last item is easy to ignore. It is also where many generated UI prototypes
become production liabilities. A cheap response that makes action validation
ambiguous is not actually cheap.

## The Takeaway

OpenUI Lang can reduce token cost, especially compared with tool-call wrappers
or verbose JSON trees. In the reproducible fixture set for this article, it
saved 27.0% against an AI SDK-style envelope and 6.8% against compact JSON.

The second number is deliberately sober. Compact JSON is a real baseline, not a
straw man.

But token count is only the visible part of the bill. The deeper cost is the
interface contract: how reliably a model can describe UI, how safely an app can
render it, and how quickly a user can act on it.

For teams building AI products where the answer often needs to become an
interface, OpenUI is worth evaluating because it treats generated UI as a
runtime contract, not a blob of data pretending to be one.

That is what beautiful AI actually costs: tokens, yes, but also structure,
validation, streaming behavior, and the discipline to make the model compose
interfaces the product can trust.
