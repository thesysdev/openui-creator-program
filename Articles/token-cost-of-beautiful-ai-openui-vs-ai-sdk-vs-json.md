# The Token Cost of Beautiful AI: OpenUI Lang vs. AI SDK vs. JSON

Generative UI has a boring cost center that becomes expensive fast: the model has to emit the interface before the user can see it.

If your model returns plain text, output size is usually a content problem. If your model returns UI, output size is also a product problem. Every repeated prop name, every nested object wrapper, and every patch operation has to be decoded, streamed, parsed, validated, and paid for. The format you ask the model to write is part of the latency budget.

This piece compares three practical ways teams represent model-generated interfaces:

1. **OpenUI Lang** — a compact line-oriented DSL that is parsed into typed components.
2. **Vercel AI SDK-style generative UI** — React/server-driven UI patterns where the model output usually coordinates tool calls, component selection, or structured data that application code renders.
3. **Raw JSON / JSON-render trees** — explicit component trees or JSON Patch streams.

The short version: OpenUI Lang is materially smaller for the same UI because it removes repeated JSON ceremony while keeping enough structure to parse and stream. In the current OpenUI benchmark set, it uses **4,800 tokens** across seven UI scenarios versus **9,122 tokens for YAML**, **10,180 for Vercel JSON-render patches**, and **9,948 for Thesys C1 JSON**. That is a **47–53% total token reduction** depending on the comparison format, with one scenario showing a **67.1% reduction** versus Vercel JSON-render.

The longer version is more nuanced: token count is not the only cost. Developer experience, runtime control, schema enforcement, streaming behavior, and design-system fit can matter more than raw output size. But token footprint is a useful forcing function because it exposes how much of your AI budget is being spent on describing the same buttons and cards over and over.

---

## What is actually being compared?

### OpenUI Lang

OpenUI Lang is designed as a model-friendly representation for UI. Instead of asking the model to emit a deeply nested JSON tree, it writes a compact syntax that maps to known components and props. A parser then turns that syntax into an AST and component structure.

That matters because LLMs are good at short, regular patterns. A line-oriented component DSL can avoid a lot of JSON overhead:

- repeated `component`, `props`, and `children` keys;
- repeated braces, quotes, commas, and patch paths;
- deeply nested object wrappers;
- verbose patch operations for streamed updates.

The tradeoff is that your app now depends on a parser, schema, and component vocabulary. That is a good trade when the UI surface is known and repeated. It is less compelling for one-off freeform structures where JSON is already accepted everywhere.

### Vercel AI SDK-style generative UI

The Vercel AI SDK is broader than a UI serialization format. It gives TypeScript developers a unified way to call models, stream output, generate structured objects, call tools, and build chat or generative UI flows across frameworks.

In many AI SDK applications, the model does not need to directly emit a full UI tree. It can call tools, choose components, stream text, or return structured data that your application renders. That can be cleaner than letting the model author every prop.

For apples-to-apples token benchmarks, though, you still need a representation of the UI state. OpenUI's benchmark uses a **Vercel JSON-render** comparison based on RFC 6902-style JSON Patch streams. That is a reasonable stress test for a JSON-first streaming UI representation: every update is explicit, but explicitness costs tokens.

### Raw JSON / normalized component trees

Raw JSON is the default because every model, API, validator, and engineer understands it. A normalized tree is easy to inspect and store:

```json
{
  "component": "Card",
  "props": {
    "children": [
      {
        "component": "TextContent",
        "props": {
          "children": "Revenue by month"
        }
      }
    ]
  }
}
```

That clarity is useful. It is also verbose. JSON repeats field names at every level, and large UI trees have many levels.

---

## The benchmark numbers

OpenUI's benchmark suite compares four formats across seven UI scenarios: YAML, Vercel JSON-render, Thesys C1 JSON, and OpenUI Lang. The benchmark method is important:

- the same seven UI prompts are used: simple table, chart with data, contact form, dashboard, pricing page, settings panel, and e-commerce product;
- OpenUI Lang is generated once per prompt;
- the parsed AST is projected into the other formats;
- tokens are counted with `tiktoken` using the `gpt-5` encoder;
- latency is estimated at 60 output tokens per second.

Here are the published token counts:

| Scenario | YAML | Vercel JSON-render | Thesys C1 JSON | OpenUI Lang | OpenUI vs YAML | OpenUI vs Vercel | OpenUI vs C1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| simple-table | 316 | 340 | 357 | 148 | -53.2% | -56.5% | -58.5% |
| chart-with-data | 464 | 520 | 516 | 231 | -50.2% | -55.6% | -55.2% |
| contact-form | 762 | 893 | 849 | 294 | -61.4% | -67.1% | -65.4% |
| dashboard | 2,128 | 2,247 | 2,261 | 1,226 | -42.4% | -45.4% | -45.8% |
| pricing-page | 2,230 | 2,487 | 2,379 | 1,195 | -46.4% | -52.0% | -49.8% |
| settings-panel | 1,077 | 1,244 | 1,205 | 540 | -49.9% | -56.6% | -55.2% |
| e-commerce-product | 2,145 | 2,449 | 2,381 | 1,166 | -45.6% | -52.4% | -51.0% |
| **Total** | **9,122** | **10,180** | **9,948** | **4,800** | **-47.4%** | **-52.8%** | **-51.7%** |

Two observations stand out.

First, OpenUI Lang's advantage is consistent. This is not one tiny example where JSON happens to be noisy. All seven scenarios show a large reduction.

Second, the reduction is smaller on large pages than on small forms. The contact form has the biggest relative win because form JSON repeats a lot of structural keys. Dashboards and product pages still save tokens, but the actual content and data take up a larger share of the output.

---

## What this means for latency

If a model decodes at roughly 60 output tokens per second, total benchmark output time looks like this:

| Format | Total tokens | Approx. decode time |
|---|---:|---:|
| OpenUI Lang | 4,800 | 80.0s |
| YAML | 9,122 | 152.0s |
| Thesys C1 JSON | 9,948 | 165.8s |
| Vercel JSON-render | 10,180 | 169.7s |

Do not treat these as exact user-facing latencies. Real apps stream, models vary, network time matters, and many systems generate partial UI or use tool calls instead of a single full page output.

But the direction is hard to ignore. If the model has to emit the whole structure, halving the output token count can nearly halve the decode portion of latency. For interactive UI, that is the difference between "the interface is forming" and "the user is waiting."

---

## What this means for API cost

Output pricing changes by provider and model, so the safest way to reason about cost is to use a formula:

```text
monthly output cost = generations × output_tokens_per_generation / 1,000,000 × output_price_per_1M_tokens
```

Using the benchmark averages:

- OpenUI Lang average: `4,800 / 7 = 686` output tokens per UI
- YAML average: `9,122 / 7 = 1,303` output tokens per UI
- Vercel JSON-render average: `10,180 / 7 = 1,454` output tokens per UI
- Thesys C1 JSON average: `9,948 / 7 = 1,421` output tokens per UI

At 1 million generated UIs per month, the difference between OpenUI Lang and Vercel JSON-render is about:

```text
(1,454 - 686) × 1,000,000 / 1,000,000 = 768M fewer output tokens
```

If output tokens cost `$10 / 1M`, that is roughly `$7,680/month` saved. If they cost `$20 / 1M`, it is `$15,360/month`. If you only generate 10,000 UIs per month, the same difference is about 7.68M output tokens, or `$76.80` at `$10 / 1M`.

That range is the real lesson. For prototypes, format efficiency is nice. For high-volume interfaces, it becomes infrastructure cost.

---

## Developer experience: where each approach wins

### OpenUI Lang wins when the UI vocabulary is known

OpenUI Lang is strongest when your app has a defined component library and you want the model to produce UI directly against that library.

Good fits:

- dashboards with repeated cards, charts, tables, and forms;
- internal tools where speed matters more than pixel-perfect hand design;
- AI agents that need to stream structured task results;
- product surfaces where model output must stay inside a known component grammar.

The developer workflow is: define components and schema, prompt the model to produce OpenUI Lang, parse it, render it, and validate failures at the format boundary.

### AI SDK-style patterns win when orchestration matters more than serialization

The Vercel AI SDK is usually the right mental model when the model is one part of a larger application workflow. You may want tool calls, server actions, model-provider abstraction, resumable streams, or React integration more than you want the smallest possible UI syntax.

Good fits:

- chat apps that sometimes render components;
- assistants that call tools and return structured results;
- apps already standardized on Next.js and React Server Components;
- teams that want provider abstraction and a mature TypeScript toolkit.

The cost question depends on what the model emits. If the model emits only a tool call and your app renders the UI deterministically, token cost can be lower than any full UI serialization. If the model emits a large JSON-render stream, the benchmark suggests OpenUI Lang is much smaller.

### JSON wins when portability and inspection matter most

JSON is still the safest interoperability layer. It is simple to log, diff, validate, and store. Every backend language can parse it. Every API client understands it.

Good fits:

- external APIs where consumers expect JSON;
- low-volume admin tools where cost is irrelevant;
- audit-heavy systems where explicit fields are more important than compactness;
- teams that do not want a DSL or parser dependency.

The downside is that the model pays for that explicitness every time.

---

## The hidden cost: invalid output

Token count is not the only output-format cost. Invalid output has a cost too:

- retrying a generation;
- repairing malformed JSON;
- falling back to text;
- showing a broken partial UI;
- adding defensive parsing code around every render path.

JSON has strong tooling, but LLMs still make annoying JSON mistakes: trailing commas, unescaped strings, missing brackets, or schema drift. Function calling and structured output modes reduce this, but not every streaming UI path can use them cleanly.

A compact DSL is not automatically safer. It must have a strict parser and useful error messages. The advantage of OpenUI Lang is that the grammar is narrow and component-aware: the model is writing UI in the shape the renderer expects, not filling a general-purpose object tree from scratch.

For production teams, the question is not "which format is prettier?" It is:

```text
How many generated outputs render correctly without repair, retry, or human intervention?
```

A format that saves tokens but increases failures is not cheaper. A format that saves tokens and reduces malformed output is a real platform advantage.

---

## A practical decision framework

Use **OpenUI Lang** if:

- the model should author UI directly;
- the app has a known design system or component library;
- output token cost and streaming latency matter;
- you want a compact format that still maps to typed components.

Use **AI SDK-style orchestration** if:

- the app needs provider abstraction, tools, agents, or server-side workflows;
- the model should decide *what* to show, while app code decides *how* to render it;
- you already live in the Next.js / TypeScript / React ecosystem.

Use **JSON** if:

- the UI output is low volume;
- portability beats token efficiency;
- the output needs to cross system boundaries as a public API;
- you want maximum compatibility with validators, logs, queues, and storage.

The strongest architecture may combine them: AI SDK for model orchestration, OpenUI Lang for compact generated UI payloads, and JSON at persistence or API boundaries.

---

## The bottom line

OpenUI Lang's token advantage is not a vague "DSLs are smaller" claim. In the benchmark set, it cuts total output tokens from roughly 9–10k down to 4.8k for the same seven generated interfaces. That is a meaningful reduction in both cost and decode latency when UI generation happens at scale.

But the best choice depends on where you want control.

If your application code should own rendering and the model should only call tools, use an orchestration-first approach. If the model needs to stream UI directly and repeatedly, OpenUI Lang is a strong fit. If you need a universal interchange format, JSON remains boring and useful.

Beautiful AI interfaces are not free. The interface description itself has a bill. Pick the format that spends tokens on product value, not syntax ceremony.

---

## Sources

- OpenUI benchmark README: `https://github.com/thesysdev/openui/tree/main/benchmarks`
- OpenUI benchmark methodology and sample scenarios: `benchmarks/README.md` in the OpenUI repository
- Vercel AI SDK documentation: `https://ai-sdk.dev/docs/introduction`
- OpenUI Creator Program issue #4 brief: `https://github.com/thesysdev/openui-creator-program/issues/4`
