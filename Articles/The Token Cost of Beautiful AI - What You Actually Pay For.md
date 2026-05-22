# The Token Cost of Beautiful AI: What You Actually Pay For

Most teams evaluate generative UI by looking at the rendered result. That is the fun part. The interface feels alive, the model picked the right component, and the user did not have to read another wall of text.

But the bill is not based on how beautiful the result looks. It is based on tokens.

When an LLM generates UI, every bracket, prop name, repeated key, wrapper object, tool-call envelope, array delimiter, and partially streamed update becomes part of the cost model. That is why "the same UI" can have very different economics depending on whether the model emits OpenUI Lang, a JSON component tree, or a tool-call shape that later renders through the AI SDK.

This is not an argument that one format is always better. JSON is still the easiest format to inspect, validate, and pass between systems. The AI SDK is a strong orchestration layer for messages, tools, streams, and framework integration. OpenUI Lang is optimized for a narrower job: let a model describe approved UI components with fewer structural tokens and render them progressively.

The right question is not "which one is coolest?" It is:

> How many tokens do we pay for every time a model has to describe an interface?

## The three cost surfaces

There are three token buckets to separate before comparing formats.

**Input tokens:** the system prompt, component documentation, schema, conversation history, and user request. These can dominate early experiments, especially if you paste a large component registry into every call. Prompt caching can help, but it does not make this bucket disappear.

**Output tokens:** the UI payload the model generates. This is where format choice matters most. A line-oriented DSL, a compact JSON tree, and a tool-call envelope can all render the same UI, but they do not cost the same to produce.

**Repair tokens:** retries, validator feedback, and follow-up prompts after malformed output. This is the quiet line item. A format that saves 30% on happy-path output can still lose if it fails often and requires repair turns.

This article focuses mostly on output tokens because they are the easiest to benchmark locally and the most directly affected by OpenUI Lang vs. JSON vs. AI SDK-style envelopes.

## What the formats are actually doing

OpenUI Lang is a compact, line-oriented language for model-generated UI. The model composes a known component vocabulary:

```txt
root = Stack([title, table, actions])
title = TextContent("Renewal risk review", "large-heavy")
table = Table([account, owner, risk])
account = Col("Account", ["Northwind", "Globex"])
owner = Col("Owner", ["Mina", "Raj"])
risk = Col("Risk", [87, 74], "number")
actions = Buttons([save], "row")
save = Button("Save view", "action:save", "primary")
```

A JSON component tree usually says the same thing with more structural vocabulary:

```json
{
  "component": "Stack",
  "props": {
    "children": [
      {
        "component": "TextContent",
        "props": {
          "text": "Renewal risk review",
          "size": "large-heavy"
        }
      }
    ]
  }
}
```

An AI SDK-style generative UI implementation often uses tool calls or message parts to decide when custom React components should render. That is useful architecture. The model can call a tool, the app can render the result, and the client can show typed states for loading, output, and errors. The extra envelope is not "bad." It is part of the orchestration contract.

The tradeoff is that if the model is also emitting the UI structure inside that envelope, you pay for both the UI and the wrapper.

## The official OpenUI benchmark

OpenUI's benchmark page compares the same generated interfaces across OpenUI Lang, YAML, Vercel JSON-Render, and Thesys C1 JSON. The docs report seven scenarios and count output tokens with `tiktoken`.

The headline numbers are blunt:

| Format | Total output tokens across seven scenarios |
| --- | ---: |
| OpenUI Lang | 4,800 |
| YAML | 9,122 |
| Vercel JSON-Render | 10,180 |
| Thesys C1 JSON | 9,948 |

In that benchmark, OpenUI Lang uses up to 67.1% fewer tokens than Vercel JSON-Render on the contact form scenario, and 52.8% fewer tokens than Vercel JSON-Render across the total set.

Those numbers do not mean every app gets exactly that savings. They do show the underlying mechanism: JSON-like UI formats repeat keys. OpenUI Lang spends more of the output on values that affect the interface and less on structural scaffolding.

## A small reproducible check

I added a small offline benchmark script with this article:

```bash
uv run --with tiktoken python benchmarks/token_cost_budget.py
```

It compares three equivalent generated UI payloads:

- a renewal risk dashboard,
- a validated onboarding form,
- and a support triage queue.

The script counts output tokens with `tiktoken` using `o200k_base`. It does not call an LLM, so the numbers are auditable and deterministic.

```txt
| Scenario | OpenUI Lang | Compact JSON | AI SDK-style envelope |
| --- | ---: | ---: | ---: |
| Renewal risk dashboard | 217 | 364 | 419 |
| Validated onboarding form | 132 | 246 | 325 |
| Support triage queue | 124 | 188 | 269 |
| **Total** | **473** | **798** | **1013** |

Savings vs compact JSON: 40.7%
Savings vs AI SDK-style envelope: 53.3%
```

This is not a replacement for OpenUI's full benchmark. It is a smaller sanity check that shows the same pattern on simpler fixtures: the UI is equivalent, but the payload shape changes the bill.

## The cost projection

Using the current GPT-4.1 mini output price of $1.60 per 1M output tokens, the script projects the monthly output-token cost like this:

| Monthly generated UIs | OpenUI Lang | Compact JSON | AI SDK-style envelope |
| ---: | ---: | ---: | ---: |
| 10,000 | $7.57 | $12.77 | $16.21 |
| 100,000 | $75.68 | $127.68 | $162.08 |
| 1,000,000 | $756.80 | $1,276.80 | $1,620.80 |

The absolute dollars are model-dependent. If you use a more expensive model, multiply the gap. If you use a cheaper model, the gap shrinks. The ratio stays useful because it comes from the output shape, not from a specific vendor price.

At one million generated UIs per month in this small benchmark, OpenUI Lang saves about $520/month versus compact JSON output and about $864/month versus the AI SDK-style envelope. That is only output tokens. If your app frequently retries malformed JSON or asks the model to regenerate partial UI, repair tokens can matter as much as the first pass.

## The latency version of the same math

Token count is also latency pressure.

If a hosted model streams at 60 output tokens per second, the benchmark totals imply:

| Format | Total tokens | Approx generation time at 60 tok/s |
| --- | ---: | ---: |
| OpenUI Lang | 473 | 7.9s |
| Compact JSON | 798 | 13.3s |
| AI SDK-style envelope | 1,013 | 16.9s |

Real latency also includes time to first token, network overhead, model load, validation, rendering, and client work. Still, fewer output tokens usually means a shorter path to the final component.

Streaming makes the difference more visible. A JSON object often needs to become valid before a renderer can trust it. A patch stream can render incrementally, but it still repeats operation metadata. OpenUI Lang is designed to stream line by line, so the renderer can start doing useful work while the model is still generating later components.

## What the token count does not capture

Token count is important, but it is not the whole engineering decision.

**JSON wins on universality.** Every engineer can inspect it, every language can parse it, and every validation library supports it. If your generated UI surface is tiny, or if the response needs to be consumed by many non-React systems, JSON may be the boring correct choice.

**AI SDK wins on application orchestration.** The AI SDK gives you message state, stream helpers, tool calls, framework integrations, and patterns for rendering tool outputs as custom components. If your hard problem is conversation flow rather than UI payload size, that layer can be worth the wrapper cost.

**OpenUI Lang wins when the model repeatedly generates component-heavy UI.** The more often your app asks the model to build tables, forms, cards, dashboards, settings panels, or operational workflows, the more repeated JSON keys start to look like rent.

The best architecture may use more than one of these. You can use an orchestration SDK to manage the conversation and still choose a compact UI language for the payload the model emits. You can use JSON at API boundaries and OpenUI Lang between the model and renderer. The cost mistake is assuming the transport and the UI representation have to be the same thing.

## A practical measurement plan

Before picking a format, measure five things in your own app:

1. **Output tokens per successful UI.** Count only the UI payload first, then add the surrounding response envelope.
2. **Input tokens per request.** Include schema prompts, component docs, and conversation history. Then test prompt caching.
3. **Invalid-output rate.** Count repair turns, not just first-pass generations.
4. **Time to first meaningful render.** Not time to last token. Users care when the first useful component appears.
5. **Component growth curve.** Add ten more components to your library and remeasure. Some formats get expensive as the vocabulary grows.

Here is the rough formula I use:

```txt
monthly_cost =
  requests *
  (
    input_tokens * input_price_per_token * cache_miss_rate
    + output_tokens * output_price_per_token
    + repair_tokens * repair_rate * token_price
  )
```

The interesting part is not the formula. It is what happens when you replace `output_tokens` with real benchmark data. The difference between 473 and 1,013 tokens does not matter much for a prototype. It matters a lot once the UI response is a default path in production.

## What you are actually paying for

When you ask a model to generate UI, you pay for every token needed to describe the interface. Some of those tokens are product value: labels, values, options, table rows, button actions. Some are syntax overhead: repeated keys, wrapper objects, patch metadata, nested props, and message envelope fields.

OpenUI Lang reduces the second category. That is its economic argument.

The reason this matters is not that OpenUI Lang makes a small demo cheaper. It is that generative UI only becomes useful when it is common. Once users expect the assistant to return a form, table, dashboard, card set, or workflow whenever the task calls for it, UI generation moves from occasional novelty to recurring infrastructure cost.

At that point, "beautiful AI" is not just a design question. It is a unit economics question.

Use JSON where interoperability matters. Use the AI SDK where orchestration matters. Use OpenUI Lang when the model needs to describe rich interfaces often enough that syntax overhead becomes a line item.

That is what you are actually paying for.

## References

- [OpenUI benchmarks](https://www.openui.com/docs/openui-lang/benchmarks)
- [OpenUI GitHub repository](https://github.com/thesysdev/openui)
- [Vercel AI SDK multi-step and generative UI guide](https://vercel.com/academy/ai-sdk/multi-step-and-generative-ui)
- [GPT-4.1 mini model pricing](https://developers.openai.com/api/docs/models/gpt-4.1-mini)
