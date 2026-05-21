# The Token Cost of Beautiful AI: OpenUI Lang vs. AI SDK vs. JSON — What You're Actually Paying For

At some point someone on your team asks the cost question. Not "is generative UI a good idea" — the budget question. "If we generate UI on every response, what does that do to our API bill at scale?"

Most framework comparisons don't answer this. They show demos and benchmark screenshots. The mechanics of *why* one approach costs more, and by how much, rarely get a concrete treatment.

This is about that.

---

## Three approaches, briefly

They all solve the same problem — getting a model to describe a UI component tree — but they differ in what the model is actually asked to output.

### Raw JSON

You write a schema, you put it in the system prompt, the model fills it out. You write a renderer that maps the JSON to components.

```json
{
  "type": "card",
  "props": {
    "title": "Monthly Revenue",
    "value": "$142,300",
    "trend": { "direction": "up", "percent": 12.4, "label": "vs last month" },
    "variant": "metric"
  }
}
```

No dependencies. Full control. Also fully your problem when the schema drifts or the model produces something malformed.

### Vercel AI SDK (streamUI / RSC)

Define tools with Zod schemas. The model calls a tool, your `generate` function maps the args to a React component.

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

Worth knowing before you go deep on this: `streamUI` is currently marked experimental. The AI SDK team recommends `useChat` with tool calls for production work. That's not a dealbreaker, but it's the kind of thing that bites you six months in when the API changes.

### OpenUI Lang

OpenUI is framework-agnostic with first-party React support. The setup is: developers define a component library, OpenUI generates a system prompt from it, the model outputs in OpenUI Lang, the renderer parses that into components. OpenUI Lang is the wire format — developers don't write it, the model does.

What comes out of the model looks like this:

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

The renderer parses this statement by statement and renders incrementally as output streams in. Developers interact with the component library definition and the renderer API — not with OpenUI Lang directly.

---

## Why the format affects token count

The content being described is the same across all three — same component tree, same layout, same data. The benchmark methodology generates an AST for each scenario first, then serializes it into each format, so comparisons are apples-to-apples. ([OpenUI benchmarks](https://github.com/thesysdev/openui/tree/main/benchmarks))

The token difference is purely encoding.

JSON quotes every key. Every string. Every nested object needs braces, every array needs brackets. And the schema in your system prompt — the thing that tells the model what to output — is also JSON. So you pay that overhead twice: once in the input, once in the output.

OpenUI Lang encodes the same tree in something closer to code. No key quoting, positional arguments, structure from grammar rather than repeated characters. Models seem to handle this more reliably too — probably because their training corpus is full of code that looks exactly like this. I haven't seen a clean benchmark isolating that effect specifically, but the structural failure rate numbers are consistent with it.

---

## The actual numbers

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

4,800 vs 10,180. That's 52.8% fewer output tokens on average across the seven scenarios.

The contact form is the extreme case — 67.1% reduction. Every field in JSON carries its metadata inline: label, placeholder, input type, required flag, validation rules, all repeated per field. OpenUI Lang pushes that into the component definition rather than the output. As forms get longer, this compounds.

One honest caveat here: these numbers compare against Vercel's JSON-Render format, which is the full schema representation. Hand-minimized JSON closes the gap. Independent benchmarks against stripped-down JSON fixtures show savings in the 6–27% range depending on how aggressively you minimize. That's still real money at scale, but it's not the headline 52–67%. In practice, production schemas rarely stay compact once validation logic, enum lists, and nested types accumulate — but your mileage will vary.

---

## Input tokens: the part people miss

Every request pays for your system prompt, not just the output.

In a JSON-based approach, the system prompt includes a JSON schema describing every component — property types, enum values, nesting, required flags. In the AI SDK approach, each tool definition is serialized as a JSON schema attached to every request payload. OpenUI generates a compact prompt from your registered library via `openuiLibrary.prompt()`, which tends to be significantly shorter.

At low volume this is noise. At 1M requests per month, every 500 tokens you save from the system prompt is 500M fewer input tokens billed. The math is simple.

---

## Streaming is where raw JSON actually breaks

JSON doesn't stream cleanly. Partial JSON isn't JSON — a parser can't do anything with it until the closing brace arrives. Most renderers buffer the full output before rendering anything. So "streaming" with JSON usually means the user waits for the full generation, then sees everything at once. Calling that streaming is technically accurate and practically misleading.

The AI SDK tool-call approach is better. Each tool call renders when it completes. You get components appearing one at a time as the model finishes each tool invocation. That's staggered rather than progressive, but it's meaningfully better than batch rendering.

OpenUI Lang renders per statement. As soon as the model finishes one line, that component renders. For a simple card the difference is imperceptible. For a dashboard with six panels it's the difference between "this feels fast" and "this feels like it's loading forever."

This is probably the most underrated tradeoff in this space. Token counts are easy to benchmark. Time-to-first-meaningful-render is harder to measure but more visible to users.

---

## Reliability: the hidden cost

At 893 tokens of JSON for a contact form, the model has 893 chances to introduce something the parser can't handle — a missing quote, an extra comma, a field name that doesn't match the schema, a nested object where a string was expected. JSON parsers fail hard. The renderer throws, the user sees nothing or a fallback.

The annoying part isn't the failure itself. It's the debugging. An enum value that drifted between the renderer and the prompt. A new component added to the library without updating the schema. These failures don't always surface immediately — sometimes they show up only for certain component combinations or at higher output lengths. Tracing them back to the source takes longer than it should.

Thesys reported an invalid output rate drop from 3% to under 0.3% after switching from JSON to OpenUI Lang. ([Thesys OpenUI launch](https://www.thesys.dev/blogs/openui)) That's a 10x improvement. At 1 million renders a month, the difference between 3% and 0.3% is 27,000 fewer failed renders. Those failures aren't just wasted API calls — they're errors users see.

---

## Maintenance: what you're actually signing up for

Token efficiency is a one-time calculation. Maintenance cost runs forever.

**Raw JSON:** you own the schema, the renderer, and the system prompt. Adding a component means updating all three, manually, staying in sync. Fine at ten components. At fifty it becomes a real engineering tax. The drift is quiet — the schema and the prompt fall out of sync and you don't find out until something renders wrong in production at 2am.

**Vercel AI SDK:** each new component is a new tool definition — Zod schema plus `generate` function. The schema is attached to the code, which is better than a floating prompt string. For teams already deep in the AI SDK ecosystem this fits naturally. For teams not in that ecosystem, it's overhead per component that adds up.

**OpenUI:** add a component to the library, call `openuiLibrary.prompt()`, done. The system prompt regenerates from the library. The model's component vocabulary stays in sync automatically. At scale this is honestly the biggest practical difference — not the token savings, but not having to manually keep schemas and prompts synchronized as the library grows.

---

## When each approach wins

**Raw JSON** is fine when your component surface is small — three to five types, limited nesting — and you want zero additional dependencies. Prototypes, internal tools, early-stage products. The overhead is manageable when the UI is narrow.

That sounds nice until your component library hits twenty types and maintaining the schema becomes a part-time job.

**Vercel AI SDK** makes sense if you're already in the Next.js ecosystem and tool-calling semantics fit your architecture. Works well for a small number of high-specificity components. Gets awkward when component count grows and tool definitions start overlapping. Also worth tracking: RSC is still experimental, which matters for production planning.

**OpenUI** is the choice when token cost is a real budget variable, your component library is large or growing, and you need reliable streaming. The learning curve is around the framework — defining component libraries, understanding how the system prompt is generated. OpenUI Lang itself is generated by the model, so there's no DSL to learn.

---

## What the numbers mean in practice

The 52.8% average reduction is the vendor benchmark against their own verbose format. The realistic range for most codebases is probably 25–50% depending on how much metadata your schemas carry and how many components you're working with.

That's still meaningful. A contact form that costs 893 tokens costing 294 instead is real savings at scale — plus faster generation, better streaming, and fewer parse failures in production.

Whether it justifies the switch depends on where you are in the build. For a small prototype, probably not. For a product at scale with a growing component library and user-visible generation in the hot path, the case gets clearer.

The benchmark suite is open source if you want to run it against your own component shapes: [github.com/thesysdev/openui/tree/main/benchmarks](https://github.com/thesysdev/openui/tree/main/benchmarks).

---

*Sources: [OpenUI benchmarks](https://github.com/thesysdev/openui/tree/main/benchmarks) · [Thesys OpenUI launch](https://www.thesys.dev/blogs/openui) · [AI SDK RSC docs](https://ai-sdk.dev/docs/ai-sdk-ui/generative-ui)*
