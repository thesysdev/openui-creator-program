# The Token Cost of Beautiful AI: OpenUI Lang vs. AI SDK vs. JSON

Every model call has a price tag. When your AI generates a UI instead of text, the bill changes — sometimes dramatically.

I benchmarked three approaches to generative UI — OpenUI Lang, Vercel's json-render (RFC 6902 patches), and Thesys C1 JSON (nested component tree) — across seven real UI scenarios. The goal: give you actual numbers for what each format costs at scale, and the tradeoffs the numbers don't capture.

## The Setup

Three formats, same UI, same model. Here's what each looks like for a simple employee table:

**OpenUI Lang** (148 tokens):
```
root = Stack([title, tbl])
title = TextContent("Employees (Sample)", "large-heavy")
tbl = Table(cols, rows)
cols = [Col("Name", "string"), Col("Department", "string"), Col("Salary", "number"), Col("YoY change (%)", "number")]
rows = [["Ava Patel", "Engineering", 132000, 6.5], ["Marcus Lee", "Sales", 98000, 4.2], ["Sofia Ramirez", "Marketing", 105000, 3.1], ["Ethan Brooks", "Finance", 118500, 5.0], ["Nina Chen", "HR", 89000, 2.4]]
```

Five lines. Each one reads left to right — `identifier = Component(args...)`. References (`cols`, `rows`) flatten what would otherwise be deeply nested.

**Vercel json-render** (340 tokens):
```json
{"op":"add","path":"/root","value":"stack-1"}
{"op":"add","path":"/elements/textcontent-2","value":{"type":"TextContent","props":{"text":"Employees (Sample)","size":"large-heavy"},"children":[]}}
{"op":"add","path":"/elements/col-4","value":{"type":"Col","props":{"label":"Name","type":"string"},"children":[]}}
{"op":"add","path":"/elements/col-5","value":{"type":"Col","props":{"label":"Department","type":"string"},"children":[]}}
{"op":"add","path":"/elements/col-6","value":{"type":"Col","props":{"label":"Salary","type":"number"},"children":[]}}
{"op":"add","path":"/elements/col-7","value":{"type":"Col","props":{"label":"YoY change (%)","type":"number"},"children":[]}}
{"op":"add","path":"/elements/table-3","value":{"type":"Table","props":{"rows":[...]},"children":["col-4","col-5","col-6","col-7"]}}
{"op":"add","path":"/elements/stack-1","value":{"type":"Stack","props":{},"children":["textcontent-2","table-3"]}}
```

Each element is an RFC 6902 JSON Patch operation. The `op`, `path`, `value`, `type`, `props`, `children` keys repeat for every node.

**Thesys C1 JSON** (357 tokens):
```json
{
  "component": {
    "component": "Stack",
    "props": {
      "children": [
        {
          "component": "TextContent",
          "props": { "text": "Employees (Sample)", "size": "large-heavy" }
        },
        {
          "component": "Table",
          "props": {
            "columns": [
              { "component": "Col", "props": { "label": "Name", "type": "string" } },
              ...
            ],
            "rows": [["Ava Patel", "Engineering", 132000, 6.5], ...]
          }
        }
      ]
    }
  }
}
```

Traditional nested component tree. Every node carries `"component"` and `"props"` keys. Deep nesting adds braces, commas, and whitespace.

The token difference for this simple table: **148 vs 340 vs 357**. OpenUI Lang uses 56-59% fewer tokens. But does it hold up for complex UIs?

## The Numbers

I used OpenUI's own benchmark suite (7 scenarios, tiktoken with the `gpt-5` encoder, temperature 0). The methodology works like this: generate OpenUI Lang from the model, parse the AST, then mechanically convert that same AST into the other three formats. This ensures all formats represent _exactly the same UI_.

| Scenario           | YAML   | json-render | C1 JSON | OpenUI Lang | vs json-render | vs C1 JSON |
|--------------------|--------|-------------|---------|-------------|----------------|------------|
| simple-table       | 316    | 340         | 357     | 148         | **-56.5%**     | -58.5%     |
| chart-with-data    | 464    | 520         | 516     | 231         | **-55.6%**     | -55.2%     |
| contact-form       | 762    | 893         | 849     | 294         | **-67.1%**     | -65.4%     |
| dashboard          | 2,128  | 2,247       | 2,261   | 1,226       | **-45.4%**     | -45.8%     |
| pricing-page       | 2,230  | 2,487       | 2,379   | 1,195       | **-52.0%**     | -49.8%     |
| settings-panel     | 1,077  | 1,244       | 1,205   | 540         | **-56.6%**     | -55.2%     |
| e-commerce-product | 2,145  | 2,449       | 2,381   | 1,166       | **-52.4%**     | -51.0%     |
| **Total**          | 9,122  | 10,180      | 9,948   | 4,800       | **-52.8%**     | -51.7%     |

Three patterns stand out:

1. **Savings scale with component density, not total UI size.** The contact form (12 components, many FormControl wrappers) shows the biggest gap (67%). The dashboard (large but with fewer component layers) shows the smallest (45%).

2. **YAML is closer to OpenUI Lang than JSON.** YAML's lack of braces and shorter syntax narrows the gap to 42-61%. If your existing infra speaks YAML, the JSON→OpenUI Lang delta isn't the right comparison.

3. **Data-heavy content compresses less.** The `rows` array in a table or `data` in a chart is identical across all formats — it's raw values, no structural overhead. The savings come from component definitions, not data payloads.

## What This Costs at Scale

Let's turn tokens into dollars. Using current API pricing (April 2026):

| Model | Output $/1M tokens |
|-------|-------------------|
| GPT-4o | $10.00 |
| Claude 3.5 Sonnet | $15.00 |
| GPT-4o-mini | $0.60 |

For a generative UI app serving 10,000 users/day, each user triggering 5 UI generations averaging the benchmark's total across all 7 scenarios:

| Daily cost | OpenUI Lang | json-render | Savings |
|-----------|-------------|-------------|---------|
| GPT-4o | $2.40 | $5.09 | **$2.69/day** |
| Claude 3.5 Sonnet | $3.60 | $7.64 | **$4.04/day** |
| GPT-4o-mini | $0.14 | $0.31 | **$0.16/day** |

**Annualized on GPT-4o: ~$982 saved.** Meaningful for a startup watching runway, negligible for an enterprise. On GPT-4o-mini, the absolute savings are $59/year — not the reason you'd switch formats.

The cost argument gets sharper at higher volume. At 100K daily users on GPT-4o, the gap is ~$9,800/year. At that scale, it starts to matter.

## The Methodology Question

One thing the benchmark README is transparent about: the model generates OpenUI Lang only, then the AST is mechanically converted to the other formats. This is fair for measuring _representation efficiency_ — same information, fewer bytes.

But it sidesteps a real question: would a model prompted to generate JSON directly produce as many tokens as the mechanical conversion? LLMs can be terse or verbose depending on their system prompt. A well-tuned JSON generation prompt might produce leaner output than a literal AST-to-JSON mapping.

The counterargument: even if you could coax a model into producing minimal JSON, you'd be fighting the format's structural overhead (braces, quotes, key repetition) with every response. OpenUI Lang avoids that overhead at the format level.

I'd call the claimed 67% a ceiling for the best scenario. The aggregate 52% savings is more representative. And for any real deployment, running your own benchmark with your component library and your prompts is the only number that matters.

## What the Numbers Don't Tell You

### Learning curve
OpenUI Lang is a new DSL. JSON is universal. Every developer on your team already reads JSON. OpenUI Lang requires learning positional argument semantics (`FormControl("Label", Input(...))` — which arg is which?), reference-based composition (`nameField = ...` then use `nameField`), and a schema that maps positions to names.

If your team is two people building fast, learning a DSL is 30 minutes. If you're integrating into a 50-person org with existing JSON tooling, it's a migration project.

### Streaming behavior
Both formats support streaming, but differently. OpenUI Lang renders progressively — each line is a complete assignment that can be rendered as soon as it's parsed. json-render sends RFC 6902 patches, each adding an element. C1 JSON must be fully received before parsing (no incremental parsing of nested JSON).

In practice, OpenUI Lang's streaming advantage compounds with the token savings: fewer tokens means faster completion, and line-by-line parsing means earlier first render.

### Error recovery
When a model hallucinates invalid syntax mid-stream, the recovery story differs:
- **OpenUI Lang**: A malformed line breaks parsing at that line. Previous lines are valid and already rendered.
- **json-render**: A malformed JSON patch breaks that patch. Previous patches are valid.
- **C1 JSON**: A malformed closing brace can invalidate the entire tree. No incremental recovery.

For production systems, the partial-failure behavior of line-oriented and patch-oriented formats is materially better than monolithic JSON.

### Ecosystem and tooling
json-render (Vercel) has 13K+ stars and renderers for React, Vue, Svelte, Solid, and React Native. OpenUI currently supports React. If you're building for multiple frameworks, json-render's ecosystem is broader today.

## When Each Approach Wins

**Choose OpenUI Lang when:**
- Token cost is a line item you're tracking (>10K daily users on a premium model)
- You're building a streaming-first experience where time-to-first-render matters
- Your team is small and can adopt a new DSL without organizational friction
- You're already in the React ecosystem

**Choose json-render when:**
- You need multi-framework support (Vue, Svelte, React Native)
- Your team has existing JSON tooling and pipelines
- You want the largest community and most battle-tested library
- The absolute cost difference doesn't justify learning a new format

**Choose C1 JSON (or similar nested trees) when:**
- You're building a custom component system that doesn't map to either library
- Your model interactions are batch (not streaming), so incremental parsing doesn't matter
- You need complete control over the wire format

## Running the Benchmark Yourself

The benchmark is fully reproducible:

```bash
git clone https://github.com/thesysdev/openui.git
cd openui/benchmarks
pnpm install
export OPENAI_API_KEY=sk-...
pnpm generate   # calls OpenAI, generates all format samples
pnpm bench       # counts tokens, prints tables
```

Swap the scenarios in `generate-samples.ts` for your own UIs to get numbers specific to your component library and typical prompts.

---

*All benchmarks use tiktoken with the `gpt-5` model encoder, generated by GPT-5.2 at temperature 0. Token counts are deterministic given the same model output. Cost projections use publicly listed API prices as of April 2026. The companion repo with all samples and the independent analysis script is at [companion-repo-url].*
