# The Token Cost of Beautiful AI: OpenUI Lang vs. AI SDK vs. JSON — What You're Actually Paying For

At some point in evaluating a generative UI framework, someone on your team asks the cost question.

Not the "is this a good idea" question. The budget question. "If we generate UI on every response, what does that do to our API bill?"

It's the right question to ask, and most framework comparisons don't answer it concretely. They show you demos, explain the developer experience, maybe share a benchmark or two. But the mechanics of *why* one approach costs more than another — and how that gap changes based on what you're building — rarely get a clear treatment.

Three approaches, what each one actually asks the model to generate, and the token tradeoffs that follow.

---

## The three approaches

Before any numbers, it helps to understand what each approach actually does at the wire level. They differ in more than syntax.

### Raw JSON

Your system prompt describes a schema. The model fills it out. You write a renderer that maps the resulting JSON to React components.

A metric card looks something like this in the model's output:

```json
{
  "type": "card",
  "props": {
    "title": "Monthly Revenue",
    "value": "$142,300",
    "trend": {
      "direction": "up",
      "percent": 12.4,
      "label": "vs last month"
    },
    "variant": "metric"
  }
}
```

No external dependencies. You control everything. You're also responsible for everything — the schema, the renderer, the validation, and keeping all three in sync as your component library grows.

### Vercel AI SDK (streamUI / RSC)

The RSC layer in the AI SDK lets you define tools the model can call to render UI. Each tool has a Zod schema. When the model decides to use a tool, the `generate` function maps the parsed arguments to a React component.

```typescript
const result = await streamUI({
  model: openai("gpt-4o"),
  tools: {
    showMetricCard: {
      description: "Display a KPI metric with trend direction",
      parameters: z.object({
        title: z.string(),
        value: z.string(),
        trend: z.object({
          direction: z.enum(["up", "down", "flat"]),
          percent: z.number(),
          label: z.string(),
        }),
        variant: z.enum(["metric", "summary"]),
      }),
      generate: async (args) => <MetricCard {...args} />,
    },
  },
});
```

The model receives a serialized JSON schema for each tool in the request payload. Every call carries that weight. Worth noting: `streamUI` is currently marked experimental in the AI SDK docs, and the team recommends `useChat` with tool calls for production generative UI work. That distinction matters for how the streaming behavior actually holds up.

### OpenUI Lang

OpenUI uses a custom DSL designed specifically for UI generation. Instead of JSON, the model produces something closer to named function calls:

```
root = Stack([header, kpiRow])
header = Card([CardHeader("Monthly Revenue", "April 2025")])
kpiRow = Stack([revenueCard, growthCard], "row", "m", "stretch")
revenueCard = Card([
  TextContent("Revenue", "small"),
  TextContent("$142,300", "large-heavy"),
  Tag("↑ 12.4% vs last month", null, "md", "success")
], "card", "column", "s", "start")
```

The system prompt is generated from your registered component library via `openuiLibrary.prompt()`. The renderer parses OpenUI Lang incrementally and renders components as each statement completes — not after the full output arrives.

---

## Why format determines token count

This isn't a subtle effect.

JSON requires structural characters on every value: quotes around keys, quotes around strings, braces around objects, brackets around arrays. A nested component tree compounds this fast. The schema description in your system prompt — the part that tells the model what to generate — is itself JSON, which means it pays the same overhead.

OpenUI Lang looks like code, not data. Keys don't need quoting. Component names and arguments are positional. The structure comes from the language grammar, not repeated characters. Models generate it reliably because their training corpus is saturated with code that looks exactly like this — function calls, named assignments, argument lists.

I suspect this is part of why models tend to stay more consistent with code-like syntax than with deeply nested schemas, though that's genuinely hard to measure in isolation. What does show up clearly is the token count and the structural failure rate — both of which are concrete.

---

## The benchmark numbers

The OpenUI benchmark suite compares output token counts across seven UI scenarios: [github.com/thesysdev/openui/tree/main/benchmarks](https://github.com/thesysdev/openui/tree/main/benchmarks)

| Scenario | OpenUI Lang | YAML | Vercel JSON-Render | C1 JSON |
|---|---|---|---|---|
| Simple table | 148 | 316 | 340 | 356 |
| Chart with data | 231 | 462 | 521 | 516 |
| Contact form | 294 | 760 | 893 | 851 |
| Settings panel | 540 | 1,078 | 1,244 | 1,207 |
| Pricing page | 1,195 | 2,220 | 2,490 | 2,390 |
| E-commerce product | 1,166 | 2,139 | 2,453 | 2,381 |
| Dashboard | 1,226 | 2,147 | 2,247 | 2,263 |
| **Total** | **4,800** | **9,122** | **10,180** | **9,964** |

Across all seven scenarios, OpenUI Lang uses 4,800 tokens to Vercel's 10,180. That's 52.8% fewer output tokens on average.

The contact form gap is the starkest — 67.1%. In JSON, every field carries its own metadata repeatedly: labels, placeholders, validation rules, enum values, nesting. OpenUI Lang represents the same field in a fraction of the characters because the component's defaults live in the component definition, not in every instance. As forms grow longer, the gap widens further.

---

## The cost people usually miss

Output tokens get the attention. Input tokens show up on every request.

Your system prompt describes what components the model can use. In a JSON-based approach, that description is a JSON schema — verbose by necessity, with full type definitions, enum lists, and nested property objects for every component. In the Vercel AI SDK approach, each tool definition is serialized as a JSON schema and attached to the payload on every call.

OpenUI generates the system prompt from your registered library via `openuiLibrary.prompt()`. The resulting description is compact — structurally closer to the OpenUI Lang the model outputs than to a verbose JSON schema.

At low volume, this difference is noise. At high volume, it compounds. Every request pays for input tokens. A 500-token reduction in system prompt length at 1M requests per month is 500M fewer input tokens — how much that costs depends on the model, but the math is the same regardless of the rate.

---

## Streaming behavior

This is where the architectural differences start to matter beyond cost.

OpenUI Lang is parsed statement by statement. Each completed line renders immediately. The user sees the first component as soon as the model finishes its first statement — not after the full output validates.

JSON doesn't stream cleanly. A JSON object is invalid until the final closing brace. You can stream characters, but most renderers buffer until the full object is complete before rendering anything. Partial JSON is not JSON. This means a complex dashboard rendered via JSON may keep users waiting through the full generation before anything appears on screen, even if streaming is technically enabled.

The AI SDK's RSC approach renders component-by-component as each tool call completes. Better than buffering the full JSON, but each component still waits until its tool's arguments are fully generated and parsed. You get staggered rendering rather than continuous streaming.

For a simple card, the difference is imperceptible.

For a dashboard with six panels, it changes the perceived performance of the product.

---

## Reliability: the cost that doesn't show up in benchmarks

Every token the model generates is an opportunity to produce output that doesn't match what the renderer expects.

At 893 tokens of JSON for a contact form, the model has 893 chances to introduce structural invalidity — a missing quote, an extra comma, a field name that doesn't match the schema, a type mismatch. JSON parsers don't recover from these. The renderer throws, logs an error, and the user sees a fallback or nothing.

The ugly part is debugging malformed nested schemas in production. One enum value drifting between the renderer and the system prompt, or a new component added without updating the schema definition — these are the kinds of failures that show up at the worst times and take longer to trace than they should.

OpenUI Lang's compact format reduces that surface area. Thesys reported taking their invalid output rate from 3% down to under 0.3% after switching from JSON to OpenUI Lang. ([Thesys, OpenUI launch](https://www.thesys.dev/blogs/openui))

A 3% invalid rate across 1 million renders is 30,000 failures a month. Those aren't just a cost — they're user-visible errors. The token savings pay for the switch; the reliability difference is what actually changes the user experience in production.

---

## Maintenance cost: what you're signing up for

Token efficiency is a one-time calculation. Maintenance cost runs forever.

**With raw JSON**, you own everything. Adding a component means updating the schema, updating the renderer, and keeping the system prompt in sync — manually. Fine at ten components. Its own engineering tax at fifty. The schema and the prompt drift apart quietly, and you don't find out until something renders wrong.

**With Vercel AI SDK**, adding a component means a new tool with a Zod schema and a `generate` function. More structured than raw JSON, and the schema stays attached to the code rather than floating in a prompt string. For teams already deep in the AI SDK ecosystem, this fits naturally. For teams adopting it primarily for generative UI, it's overhead that needs to be budgeted per component.

**With OpenUI**, you add a component to your library and call `openuiLibrary.prompt()`. The system prompt regenerates from the library automatically. The model's component vocabulary stays synchronized without a separate step. At scale, this is the biggest practical difference — not the per-token cost, but the ongoing maintenance overhead per component added.

---

## When each approach makes sense

**Raw JSON** makes sense when your component surface is small — five or fewer types, limited nesting — and you want zero external dependencies. It's also the right call for prototypes or internal tools where scale doesn't matter yet. The overhead is manageable when the UI is narrow. A chatbot that renders one of three card types doesn't need a specialized output language.

**Vercel AI SDK** makes sense when you're already building in the Next.js / RSC ecosystem and tool-calling semantics match your architecture. It works well for a small number of high-specificity components that map cleanly to distinct tools. It starts to break down as the vocabulary grows — twenty tools is manageable, fifty with overlapping concerns is not.

**OpenUI** makes sense when token cost is a real variable in your budget, your component library is large or expected to grow, you care about progressive streaming, and you can't absorb a 3% invalid output rate in a customer-facing product. The tradeoff is the dependency and the OpenUI Lang learning curve. For a prototype, neither is worth it. For a production product at scale, both pay off.

---

## What the numbers actually mean

The 52.8% average token reduction isn't theoretical. It's the difference between a contact form costing 893 tokens to generate and costing 294. Across a product generating thousands of UI responses daily, that compounds into real API spend — plus faster generation, better streaming, and fewer production failures.

Whether that justifies the switch depends on where you are in the build, how large your component surface is, and what a 3% error rate costs you today.

The benchmark suite is open source and runnable. If your components look different from OpenUI's test scenarios, run it with your own schemas and see where your stack lands — not just OpenUI's headline number.

---

*Benchmark data: [OpenUI benchmark suite](https://github.com/thesysdev/openui/tree/main/benchmarks). Invalid output rate reduction: [Thesys OpenUI launch](https://www.thesys.dev/blogs/openui). AI SDK RSC experimental status: [ai-sdk.dev docs](https://ai-sdk.dev/docs/ai-sdk-ui/generative-ui). OpenUI docs: [openui.com](https://www.openui.com/).*
