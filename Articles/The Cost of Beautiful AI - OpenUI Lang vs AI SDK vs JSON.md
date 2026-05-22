# The Token Cost of Beautiful AI: OpenUI Lang vs. AI SDK vs. JSON — What You're Actually Paying For

Ask a model to generate a support dashboard, a checkout form, or a settings panel, and the first answer most teams reach for is JSON.

That instinct is reasonable. JSON is explicit. It is easy to validate. It maps cleanly to component props. It looks like the natural transport layer between a model and a renderer.

It is also expensive.

Not philosophically expensive. Literally expensive: more output tokens, longer decode time, more chances for malformed output, and more surface area to stream before a user sees the interface they asked for.

Generative UI is often discussed as a product experience problem: text is not enough, users need controls, tables, charts, forms, and actions. That framing is true, but incomplete. Once you let a model generate UI, the representation format becomes part of your cost model. The same visual interface can be cheap or costly depending on how many tokens the model must emit to describe it.

OpenUI Lang is interesting because it treats UI as something closer to a compact language than a verbose object tree. Instead of asking the model to serialize nested JSON for every component and prop, it asks the model to produce a line-oriented DSL that the renderer can parse progressively.

That design choice has real economic consequences.

There is one caveat before looking at numbers: "AI SDK" and "JSON" are not the same kind of comparison.

Vercel's AI SDK RSC path is an application architecture. It lets a server action stream React Server Components to the client through APIs such as `streamUI`. The official docs currently describe AI SDK RSC as experimental and recommend AI SDK UI for production. JSON, by contrast, is only an output representation. You can use JSON inside many architectures, including an AI SDK app.

So this article compares the cost of the generated representation, then treats AI SDK as a product/runtime tradeoff: powerful if you want Next.js and RSC-native streaming, less directly comparable if the question is "how many tokens does the model need to describe this UI?"

## The Benchmark Setup

OpenUI includes a benchmark suite that compares four ways to encode the same generated UI:

- OpenUI Lang: a compact line-oriented DSL generated directly by the model.
- YAML: a structured `root` / `elements` payload.
- Vercel JSON-Render: a JSON Patch stream using RFC 6902-style operations.
- Thesys C1 JSON: a normalized component tree with `component` and `props` envelopes.

That "Vercel JSON-Render" row is not the same thing as AI SDK RSC. It is a useful proxy for a JSON-patch-style streamed UI representation, not a full measurement of the AI SDK runtime. I am using it for the representation-cost part of the analysis because it gives us an apples-to-apples token comparison over the same generated interface.

This is not an independent third-party benchmark. It is OpenUI's own reproducible benchmark, and that matters. The useful part is that the method is inspectable: same prompts, one generated OpenUI Lang output, one parsed AST, multiple serializations, then one token-counting path. If your component vocabulary is very different, you should rerun the benchmark against your own schemas before treating any percentage as universal.

The benchmark uses seven common UI scenarios:

- simple table
- chart with data
- contact form
- product analytics dashboard
- pricing page
- settings panel
- e-commerce product page

The important part is that the comparison is not between different UIs. OpenUI Lang is generated once, parsed into an AST, and then projected into the other formats. That means the benchmark is measuring representation overhead, not whether one prompt happened to produce a simpler interface than another.

Token counts are measured with `tiktoken` using the `gpt-5` model encoder. Latency is estimated at a fixed 60 output tokens per second. That fixed-rate assumption is useful because it isolates a basic truth: if one format requires twice as many output tokens to describe the same interface, it will usually take meaningfully longer to stream.

The headline result:

| Format | Total output tokens across seven scenarios |
| --- | ---: |
| OpenUI Lang | 4,800 |
| YAML | 9,122 |
| Thesys C1 JSON | 9,948 |
| Vercel JSON-Render | 10,180 |

Across the full benchmark, OpenUI Lang used:

- 47.4% fewer tokens than YAML
- 51.7% fewer tokens than Thesys C1 JSON
- 52.8% fewer tokens than Vercel JSON-Render

That is not a small optimization. It is the difference between treating generated UI as a practical runtime primitive and treating it as a premium feature that gets throttled the moment usage grows.

It is also not a claim that every JSON implementation will always be 52.8% more expensive. A hand-minimized JSON payload with short keys, fewer nested envelopes, and no repeated descriptions will narrow the gap. The reason the official benchmark is still useful is that production schemas rarely stay minimal. Once you add validation states, accessibility labels, variants, actions, nested children, and enough component metadata for a model to use the schema reliably, verbosity returns.

## Why JSON Gets Large So Quickly

JSON pays for clarity by repeating structure.

A component tree usually needs repeated keys:

```json
{
  "component": "Card",
  "props": {
    "title": "Revenue",
    "children": [
      {
        "component": "Metric",
        "props": {
          "label": "MRR",
          "value": "$82,400"
        }
      }
    ]
  }
}
```

That shape is friendly to machines, but not to token budgets. Every component repeats `component`, `props`, braces, quotes, commas, and nested envelopes. The deeper the UI gets, the more the format spends on scaffolding rather than semantic content.

OpenUI Lang pushes in the opposite direction. It relies on a component library and a parser so the model can emit a compact representation:

```text
card1 = Card("Revenue", [
  metric1 = Metric("MRR", "$82,400")
])
```

The exact syntax depends on the component schema, but the principle is the same: the model should spend tokens on the UI, not on repeatedly explaining that every node has props.

That is why the gap widens on larger examples.

In the benchmark, a simple table is already cheaper in OpenUI Lang:

| Scenario | YAML | Vercel JSON-Render | Thesys C1 JSON | OpenUI Lang |
| --- | ---: | ---: | ---: | ---: |
| simple table | 316 | 340 | 357 | 148 |

But the more realistic screens show why this matters in production:

| Scenario | YAML | Vercel JSON-Render | Thesys C1 JSON | OpenUI Lang |
| --- | ---: | ---: | ---: | ---: |
| dashboard | 2,128 | 2,247 | 2,261 | 1,226 |
| pricing page | 2,230 | 2,487 | 2,379 | 1,195 |
| e-commerce product page | 2,145 | 2,449 | 2,381 | 1,166 |

These are the kinds of interfaces where generative UI becomes useful: not a single button, but a full response with layout, data display, and actions. They are also where verbose encodings become most expensive.

## Token Cost Becomes Latency

For generated UI, output token count is not just an invoice number. It is also the time before the user sees the finished interface.

Assume 60 output tokens per second:

| Format | Total tokens | Approximate decode time |
| --- | ---: | ---: |
| OpenUI Lang | 4,800 | 80.0s |
| YAML | 9,122 | 152.0s |
| Thesys C1 JSON | 9,948 | 165.8s |
| Vercel JSON-Render | 10,180 | 169.7s |

That table sums all seven benchmark screens, so no single user would wait that full duration. The ratio is what matters. For the same set of UIs, the JSON-family encodings require roughly twice the output stream.

On a single dashboard response, the difference is easier to feel:

| Format | Dashboard tokens | Approximate decode time at 60 tok/s |
| --- | ---: | ---: |
| OpenUI Lang | 1,226 | 20.4s |
| YAML | 2,128 | 35.5s |
| Thesys C1 JSON | 2,261 | 37.7s |
| Vercel JSON-Render | 2,247 | 37.5s |

In a chat UI, 17 seconds is not an implementation detail. It changes how the product feels. The user is not evaluating your internal architecture. They are watching a response appear, or fail to appear, and deciding whether the system is responsive enough to trust.

Progressive rendering helps, but it does not erase token cost. A stream that can render incrementally still has to generate the tokens. If the representation is twice as long, the renderer either waits longer for later components or shows a partial interface for longer.

## Progressive Rendering Changes the UX Budget

OpenUI's React renderer accepts raw OpenUI Lang text and renders it through a component library:

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

The renderer is designed for streamed output. As chunks arrive, the parser reruns. Forward references can resolve once later statements arrive. Invalid or unresolved items can be dropped instead of blocking the whole render. Errors are structured enough to feed back into an automated correction loop.

That design makes token efficiency more valuable, not less.

If the response format is compact, the useful parts of the interface arrive sooner. A chart, a card, or a form has fewer surrounding syntax tokens to wait behind. Progressive rendering is not only about whether streaming is possible. It is about how quickly the stream reaches meaningful UI.

This is where a DSL has an advantage over a raw JSON tree. JSON is strict about complete syntax. A partially streamed object is often not useful until enough braces and brackets have arrived. A line-oriented UI language can be parsed in smaller semantic units.

For a user, that can be the difference between:

- a blank assistant message that eventually becomes a dashboard, and
- a dashboard that starts taking shape while the model is still finishing the response.

## Cost at Product Scale

The per-response cost difference looks abstract until you multiply it.

Suppose an AI product generates 100,000 rich UI responses per month, and the average response is similar to the benchmark mix.

The benchmark average per UI is:

| Format | Average output tokens per UI |
| --- | ---: |
| OpenUI Lang | 686 |
| YAML | 1,303 |
| Thesys C1 JSON | 1,421 |
| Vercel JSON-Render | 1,454 |

At 100,000 UI responses:

| Format | Monthly output tokens |
| --- | ---: |
| OpenUI Lang | 68.6M |
| YAML | 130.3M |
| Thesys C1 JSON | 142.1M |
| Vercel JSON-Render | 145.4M |

Even if output tokens are cheap, the difference compounds. At any given model price, the JSON-style approaches spend roughly twice as much of the output-token budget to describe the same screens.

That changes product decisions:

- Do you allow generative UI on every support response, or only on premium plans?
- Do you let agents build full dashboards, or restrict them to smaller cards?
- Do you stream UI during exploration, or only after the user confirms intent?
- Do you use a faster, cheaper model for UI generation because the format is compact enough?

A verbose format turns these into cost-control questions. A compact format gives you more room to make the product decision based on UX.

## Where AI SDK Fits

AI SDK RSC approaches generative UI from the React side. Instead of making the model emit a compact UI language that a renderer parses, the application defines tools and server-side generation functions that can stream React components. That is a different bet.

The upside is integration. If your application is already built around Next.js, Server Actions, and React Server Components, AI SDK RSC gives you a direct route from model/tool output to UI. You get to keep normal React components as the unit of composition. For many teams, that matters more than squeezing every token out of the generated representation.

The cost is that AI SDK is not a universal representation for generated UI. It is tied to the React/RSC execution model. It can be a strong fit for a Vercel/Next.js stack, but it is less natural if you want the same generated UI language to render across web, mobile, email, or a separate runtime.

That is why the cost question should be split in two:

- Representation cost: how many tokens does the model need to describe the interface?
- Runtime cost: how much framework, server, state, and rendering machinery does the application need to turn that output into UI?

OpenUI Lang optimizes the first question by making the generated representation compact. AI SDK RSC optimizes for React-native integration. Raw JSON optimizes for interoperability and simple validation. None of those choices is universally correct.

The mistake is treating them as interchangeable. If a team says "we use JSON because it is simple," they are usually talking about validation and debugging. If a team says "we use AI SDK because it streams UI," they are talking about application architecture. If a team says "we use OpenUI Lang because it is cheaper to generate," they are talking about the model-output surface itself.

Those are three different costs.

## A Practical Adoption Scorecard

The cleanest way to choose is to separate "can it render?" from "what does it cost to operate?"

| Question | Usually favors |
| --- | --- |
| Is this a prototype with three to five component types? | Raw JSON |
| Is the app already centered on Next.js, Server Actions, and React Server Components? | AI SDK RSC |
| Does the same generated UI need to render outside one React/RSC runtime? | OpenUI Lang or JSON |
| Is generated UI on the user-facing hot path, not an occasional admin feature? | OpenUI Lang |
| Will the component library keep growing over time? | OpenUI Lang |
| Do independent systems need to consume the payload without sharing a renderer? | Raw JSON |
| Is the main risk schema drift between prompt, renderer, and components? | OpenUI Lang or AI SDK |

My read is simple: JSON is the lowest-friction starting point, AI SDK is strongest when the app architecture is already aligned with Vercel's React tooling, and OpenUI Lang is strongest when generated UI becomes repeated product infrastructure. The moment teams care about cost per render, time to first meaningful component, and keeping a growing component vocabulary synchronized, the compact renderer contract becomes an advantage rather than extra machinery.

## The Tradeoff: Compactness Requires a Runtime Contract

OpenUI Lang is not free magic. The compactness comes from moving knowledge out of the generated text and into the runtime contract.

The model does not need to repeatedly describe what a component tree is because the renderer already knows the component library. The parser can map positional arguments to named props because it has the schema. The UI can stream progressively because the renderer understands the language.

That means OpenUI Lang is strongest when:

- you control the component library,
- you can provide a schema to the model,
- the renderer is part of the application architecture,
- and generated UI is a repeated product behavior, not a one-off experiment.

Raw JSON is still useful when interoperability is more important than token efficiency. If multiple systems need to consume the output without sharing a renderer contract, JSON may be the right compromise. YAML can be readable for humans. JSON Patch can be a reasonable way to represent incremental changes when you are already operating on a known document.

But if the task is "generate a UI for this chat response," the shared renderer contract is not a downside. It is the whole point. You already need a renderer, validation, component definitions, and action handling. OpenUI Lang uses that existing structure to reduce what the model has to say.

## What You Are Actually Paying For

When teams compare generated UI approaches, they often ask whether the output is expressive enough.

That matters, but it is not the only question.

You are also paying for:

- every repeated key in a component tree,
- every quote, brace, and nested `props` envelope,
- every token the model must decode before a useful component appears,
- every additional malformed-output opportunity,
- and every extra second a user waits while the interface streams.

OpenUI Lang's advantage is not just that it uses fewer tokens. It is that it aligns the representation with the job being done. A model generating UI should not have to serialize a generic data format from scratch every time. It should be able to speak in the vocabulary of the component system.

That is the core difference:

- JSON describes a UI as data.
- OpenUI Lang describes a UI as a compact program for a known renderer.

For occasional experiments, the distinction may not matter. For production AI interfaces, it does.

The more often your product generates real UI, the more token overhead becomes product overhead: higher cost, slower responses, and a tighter limit on what you are willing to render.

Beautiful AI is not just about whether the interface looks good. It is also about whether the format is efficient enough to use every day.

## References

- OpenUI benchmark methodology and results: [benchmarks/README.md](https://github.com/thesysdev/openui/tree/main/benchmarks) in the OpenUI repository.
- OpenUI React renderer documentation: [docs/content/docs/openui-lang/renderer.mdx](https://github.com/thesysdev/openui/blob/main/docs/content/docs/openui-lang/renderer.mdx) in the OpenUI repository.
- Vercel AI SDK RSC docs: [ai-sdk.dev/docs/ai-sdk-rsc](https://ai-sdk.dev/docs/ai-sdk-rsc).
- Vercel Generative UI with RSC template: [vercel.com/templates/ai/rsc-genui](https://vercel.com/templates/ai/rsc-genui).
- OpenUI creator program bounty issue: [thesysdev/openui-creator-program#4](https://github.com/thesysdev/openui-creator-program/issues/4).
