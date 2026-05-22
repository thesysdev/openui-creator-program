# The Token Cost of Beautiful AI: The Carrying Cost of Generated UI

A generated interface has two prices.

The first price is obvious: output tokens. If the model has to produce 2,400 tokens instead of 1,200 tokens to describe the same dashboard, the response costs more and arrives later.

The second price is quieter: the carrying cost of the format. How much instruction do you have to put in the system prompt? How much syntax has to be repeated in every response? How much has to be buffered before the renderer can show anything useful? How often does the output need to be retried because the shape is valid text but invalid UI?

That second price is where generative UI formats start to separate.

OpenUI Lang, Vercel AI SDK-style tool output, and raw JSON can all produce structured interfaces. They do not have the same economic profile. The difference is not only "DSL shorter than JSON." It is about where each approach puts complexity: in generated output, in prompts, in runtime code, or in the application contract.

## The benchmark that matters first

OpenUI's public benchmark compares four representations of the same seven UI scenarios: YAML, Vercel JSON-Render, Thesys C1 JSON, and OpenUI Lang. The methodology is useful because the UI is held constant. The model generates OpenUI Lang once, the parsed AST is projected into the other formats, and the saved artifacts are counted with `tiktoken` using the GPT-5 encoder.

Here are the total output tokens across the seven scenarios:

| Format | Output tokens |
| --- | ---: |
| OpenUI Lang | 4,800 |
| YAML | 9,122 |
| Thesys C1 JSON | 9,948 |
| Vercel JSON-Render | 10,180 |

OpenUI Lang is 47.4% smaller than YAML, 51.7% smaller than Thesys C1 JSON, and 52.8% smaller than Vercel JSON-Render in that benchmark set.

The per-scenario numbers tell the same story. A contact form takes 294 OpenUI Lang tokens versus 893 Vercel JSON-Render tokens. A pricing page takes 1,195 versus 2,487. A dashboard takes 1,226 versus 2,247. The advantage is not limited to tiny examples where a DSL can look artificially compact.

That matters for cost, but it matters just as much for latency. At a simple 60-token-per-second decode rate, the benchmark's Vercel JSON-Render total is about 169.7 seconds of aggregate decode time across the seven generated interfaces. OpenUI Lang is 80.0 seconds. In a single request, that difference is the gap between "the UI starts to feel live" and "the user watches an answer slowly assemble."

## Why JSON gets expensive

JSON is not expensive because braces are morally bad. It is expensive because a UI tree repeats the same envelope over and over.

A component tree usually needs fields like:

```json
{
  "component": "Card",
  "props": {
    "title": "Renewal risk",
    "children": []
  }
}
```

That shape is easy for software to parse, but it forces the model to keep paying for names that the renderer already knows: `component`, `props`, `children`, `items`, `type`, `label`, `value`, and so on. The deeper the UI tree, the more the envelope dominates the content.

AI SDK-style tool calls add another layer. A tool call is a good orchestration primitive: it lets a model request a typed action and lets the application validate arguments. But if every rendered interface is wrapped as a tool invocation, the output has to carry tool-call metadata as well as the UI payload. That wrapper can be worth it when the UI is one step inside a larger agent workflow. It is less attractive when the job is simply "stream this interface."

OpenUI Lang moves the contract closer to how a developer describes a component call:

```txt
root = Card(header, body, actions)
header = TextContent("Renewal risk", "large-heavy")
body = Table([accountCol, riskCol, nextStepCol])
actions = Buttons([reviewBtn], "row")
reviewBtn = Button("Review accounts", "action:review", "primary")
```

The renderer still gets structure. The model still has constraints. The application still decides what `action:review` means. But the generated text is mostly component names, arguments, IDs, and content rather than repeated JSON scaffolding.

That is the immediate output-token win.

## The cost you do not see in the response

Output tokens are only part of the bill. A production generative UI system also pays input tokens for the component catalog and behavioral instructions.

With raw JSON, the prompt usually has to explain the allowed schema in detail. If the application supports cards, tables, forms, buttons, charts, and action descriptors, the model needs enough schema context to stay inside the renderer's contract. You can compress that schema, but compression has a tradeoff: fewer instructions often means more malformed output, more loose interpretation, or more application-side repair.

With an AI SDK tool approach, some schema moves into the tool definition. That is good engineering. The model sees a typed function boundary, and the application receives structured arguments. The cost is that the generated UI is coupled to the tool protocol. For simple transactional actions, that is usually perfect. For long progressive UI streams, the tool boundary can become a heavier envelope than the interface needs.

OpenUI's approach is different: define the component library, generate the model instructions from that library, then have the model emit OpenUI Lang constrained to those components. The schema is still real. It just does not have to be repeated inside every generated component instance.

This distinction matters at scale. If your catalog prompt is large but cacheable, it behaves differently from a verbose response format. Input prompt cost can often be cached, reused, or routed through cheaper models. Output tokens are generated every time, streamed to the user every time, and charged every time.

In other words: put stable structure in the prompt and runtime; keep per-response output focused on the changing UI.

## A simple monthly cost model

The included script in this PR, `benchmarks/openui_token_carrying_cost.py`, uses the published OpenUI benchmark totals and projects monthly output-token cost at 100,000 generated UI responses.

At $10 per million output tokens, the benchmark totals imply:

| Format | Tokens per benchmark set | Monthly output cost at 100k generations |
| --- | ---: | ---: |
| OpenUI Lang | 4,800 | $4,800 |
| Thesys C1 JSON | 9,948 | $9,948 |
| Vercel JSON-Render | 10,180 | $10,180 |

At $30 per million output tokens, multiply those by three. At $0.60 per million output tokens, the absolute numbers shrink, but the ratio does not. A compact output format is still about half the output-token bill in this benchmark.

The real production delta can be larger when retries enter the picture. Suppose a verbose JSON renderer has a 5% retry or repair path because some responses stream into invalid intermediate states, miss required props, or fail validation. The nominal 10,180 tokens per response set becomes 10,689 effective tokens. That retry cost lands on top of the baseline verbosity.

This is why "the model is cheap now" is only half an answer. Cheap tokens make experiments easier. They do not remove latency, retry risk, or the engineering time spent making a verbose format feel interactive.

## Streaming changes the economics

Generative UI is not just serialized data. It is a user experience unfolding over time.

A raw JSON tree often has a validity problem while streaming: the application may not be able to parse or render the full object until enough closing braces arrive. Teams can work around this with partial parsers, JSON Patch, line-delimited objects, or tool-call deltas. Those are reasonable techniques, but they add protocol machinery.

OpenUI Lang is line-oriented. A renderer can parse meaningful units earlier because the response is shaped as assignments and component calls, not a single nested object that only becomes valid at the end. That does not mean every partial line is renderable, and it does not remove the need for error handling. It does mean the format is designed around incremental display rather than retrofitted into it.

This is where token count and UX meet. Fewer tokens reduce time to completion. A streamable grammar improves time to first meaningful render. Both matter.

If the user asks for a dashboard and sees the title, summary, and first table structure quickly, the system feels responsive even before every row or chart is finished. If the user waits for one large JSON object to close, the same model can feel slower even when total wall-clock time is acceptable.

## When each approach wins

Raw JSON is still a good choice when the UI surface is small, internal, and not heavily streamed. If you are returning a three-field configuration object or a fixed card schema, JSON is boring in the best way. Every language parses it. Every validation library understands it. Debugging is straightforward.

AI SDK-style tools are the right default when UI generation is part of a broader agent workflow. If the model needs to call `searchProducts`, then `showComparison`, then `createOrder`, typed tool boundaries are valuable. The tool call is the control plane. The UI is one payload inside that loop.

OpenUI Lang becomes compelling when generated UI is the product surface rather than a side effect. If your model regularly returns forms, cards, tables, dashboards, settings panels, and action groups, output verbosity compounds. If the interface should stream progressively, a line-oriented UI language is easier to justify. If design-system control matters, generating against a known component library is safer than asking the model for arbitrary markup or unconstrained JSON.

The practical decision is not "DSL or JSON." It is:

- How many generated UI responses do we expect per month?
- How complex is the average component tree?
- Does the user need progressive rendering?
- Can the component catalog be stable and reusable?
- Are tool calls the primary abstraction, or is the UI stream itself the primary artifact?

Those answers decide where the cost lands.

## What teams should actually measure

Before choosing a format, measure five things with your own component library:

1. Output tokens for equivalent UI responses.
2. Input tokens for the component catalog, system instructions, and examples.
3. Time to first meaningful render, not just final response time.
4. Validation failure and retry rate.
5. Developer time spent adding a new component or debugging malformed output.

The first metric is easy. The fifth is the one teams underestimate.

A format that saves 50% of output tokens but makes every component painful to register is not a win. A JSON schema that is verbose but already fits your infrastructure may be fine at low volume. A tool-call format may be ideal if your UI is inseparable from agent actions. OpenUI Lang is strongest when the component vocabulary is stable, the generated surface is rich, and the response stream is part of the user experience.

That is the honest version of the token-cost argument: OpenUI Lang is not cheaper because it has clever syntax. It is cheaper because it removes repeated per-response scaffolding and treats generated UI as a first-class stream.

For beautiful AI, that is what you are actually paying for: not just pixels, but the protocol that gets structured pixels from the model to the user quickly, reliably, and without carrying unnecessary syntax in every response.

## Sources

- [OpenUI benchmark methodology and results](https://github.com/thesysdev/openui/tree/main/benchmarks)
- [OpenUI documentation](https://www.openui.com/)
- [Vercel AI SDK documentation](https://sdk.vercel.ai/)
