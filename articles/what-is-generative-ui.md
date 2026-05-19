# What Is Generative UI? (And Why Text Output Is No Longer Enough)

Ask an LLM to compare three pricing plans and you get a wall of text. Bullet points, maybe. Markdown tables if you're lucky. But not a pricing card layout with buttons you can click.

That gap between what AI *knows* and what it can *show* is where generative UI lives.

## The Text Ceiling

Every developer building with LLMs hits the same wall. The model understands your data perfectly — it can analyze a spreadsheet, compare options, walk through a multi-step process. But the output is always the same: text.

Text works for conversation. It fails for:

**Data comparison.** A model describing the differences between three database options in paragraphs vs. a comparison table with sortable columns. The information is identical. The comprehension time is not.

**Multi-step workflows.** "First, enter your name. Then, select a plan. Then, enter payment details." Three sentences. Or: a stepper component with input fields, validation, and a progress bar. The text version forces the user to hold state in their head. The UI version holds it for them.

**Interactive exploration.** "Here are your monthly expenses: rent $2,100, food $800, transport $350..." Or: a pie chart you can hover over, click to drill down, and filter by date range. Text is a report. UI is a tool.

**Decision-making.** "Based on your requirements, I recommend Plan B because..." Or: three plan cards side by side with a highlight on the recommended one and a "Select" button. The text version asks the user to read, decide, then go find where to click. The card layout collapses three steps into one.

This isn't about making things prettier. It's about matching the output modality to the task. When the task is "understand and act on structured information," text is the wrong medium.

## The Spectrum of UI Generation

Generative UI isn't a single technique. It's a spectrum, and understanding where each approach sits clarifies what's new and what isn't.

**Level 0: Template selection.** The model picks which pre-built template to show. "User asked about weather → show the weather widget." No generation — just routing. This is what most chatbots do today. The model chooses; the frontend renders a fixed component.

**Level 1: Template filling.** The model picks a template *and* populates it with data. "User asked for a comparison → show the comparison table → fill it with these three products." The structure is fixed; the content is dynamic. Think Mailchimp email templates, but chosen by an LLM instead of a marketer.

**Level 2: Component composition.** The model selects from a library of components and arranges them. "This response needs a heading, then a chart, then a table, then a call-to-action button." The model doesn't just fill slots — it decides the layout. The components exist; the arrangement is novel.

**Level 3: Full generative UI.** The model defines the entire component tree — what components exist, how they're nested, what data they contain, and how they relate to each other. A pricing page with a toggle between monthly and annual, a feature comparison grid, and a checkout flow — all described in a single model output.

The jump from Level 1 to Level 3 is where things get interesting. At Level 1, you're building a smarter router. At Level 3, you're turning the model into a layout engine.

## How Generative UI Actually Works

The core idea is simple: instead of the model outputting text, it outputs a structured description of a UI. A renderer on the client interprets that description and turns it into real, interactive components.

Here's what that looks like concretely. Say a user asks: "Show me a dashboard of my team's performance this quarter."

**With text output:**
```
Team Performance Q1 2026:

- Total revenue: $1.2M (up 15%)
- Active projects: 12
- Sprint velocity: 42 points/sprint (avg)
- Team satisfaction: 4.2/5

Top performers:
1. Alex Chen - 3 projects delivered
2. Sarah Kim - highest client satisfaction (4.8)
3. James Wu - 45% sprint velocity increase
```

**With generative UI (OpenUI Lang):**
```
root = Stack([header, metrics, chart, topList])
header = TextContent("Team Performance — Q1 2026", "large-heavy")
metrics = HStack([
  MetricCard("Revenue", "$1.2M", "+15%", "positive"),
  MetricCard("Projects", "12", "active"),
  MetricCard("Velocity", "42 pts", "/sprint"),
  MetricCard("Satisfaction", "4.2/5", "")
])
chart = LineChart(months, revenueData, "Monthly Revenue")
topList = Table(perfCols, perfRows)
```

Same information. But the second version renders as an actual dashboard — with metric cards, a line chart, and a sortable table. The user can hover over the chart, sort the table, and understand the data at a glance instead of parsing paragraphs.

The model didn't generate React code. It generated a *description* of components in a domain-specific language. The renderer knows how to turn `MetricCard("Revenue", "$1.2M", "+15%", "positive")` into a styled card with a green arrow icon. The model handles content and layout. The renderer handles pixels and interactions.

## The Rendering Pipeline

Three things must happen for generative UI to work:

**1. A structured output format.** The model needs to express UI in something more structured than natural language, but simpler than full HTML/React code. This is the format layer — it could be JSON, a custom DSL, or even XML. What matters is that it's parseable and that the model can produce it reliably.

**2. A component library.** The renderer needs to know what `MetricCard` and `LineChart` mean. This is your design system — the set of building blocks the model can compose. The model can only use components that exist in the library. It's constrained creativity, not open-ended code generation.

**3. A streaming-capable renderer.** Because models generate tokens one at a time, the renderer needs to handle partial output. This is where progressive hydration comes in — rendering components as soon as they're fully described, without waiting for the entire response. A line-oriented format like OpenUI Lang has a natural advantage here: each line is a complete component that can render immediately.

This pipeline — format → library → renderer — is what separates generative UI from "just have the model write React code." Code generation is brittle (models hallucinate syntax), insecure (arbitrary code execution), and slow (the model spends tokens on boilerplate). Generative UI gives the model a constrained vocabulary of components and lets a trusted renderer handle the actual rendering.

## What Changes for Developers

If you're building with generative UI, your development model shifts:

**You stop writing views. You start writing component libraries.** Instead of building a "team dashboard page," you build `MetricCard`, `LineChart`, `Table`, and `TopPerformers` components. Then you describe these components to the model (via system prompt or schema) and let it compose them for each user's request.

**Prompt engineering becomes layout engineering.** Your system prompt defines what components are available, what arguments they accept, and any layout constraints ("never stack more than four MetricCards horizontally"). The quality of your generative UI is a function of how well you constrain the model.

**Testing changes.** Instead of testing "does the dashboard page render correctly," you test "does MetricCard handle negative percentages" and "does the renderer handle a Stack inside a Stack." Component-level testing replaces page-level testing.

**Performance has a new dimension: token efficiency.** A format that expresses a dashboard in 500 tokens vs. 1,200 tokens isn't just cheaper — it's faster. Fewer tokens means faster completion, which means faster time-to-first-render. At scale, the format directly impacts user experience.

## When to Use Generative UI (And When Not To)

Generative UI isn't a universal replacement for traditional frontends. Here's when it earns its complexity:

**Use it when the UI must adapt to unpredictable inputs.** A customer support agent that needs to show order details, return forms, shipping trackers, or product comparisons depending on the conversation. You can't pre-build every possible layout, but you can give the model a library of components and let it compose the right one.

**Use it when data density is high.** Financial dashboards, analytics reports, multi-dimensional comparisons — anywhere the user needs to interact with structured data rather than read about it.

**Use it when the conversation flow is non-linear.** A mortgage calculator that adjusts in real-time as the user changes parameters. Text output forces sequential "what if" conversations. Generative UI can produce an interactive calculator that updates live.

**Don't use it for static, known layouts.** Your marketing landing page doesn't need generative UI. The layout is fixed. The content changes rarely. A traditional frontend is simpler and faster.

**Don't use it for simple Q&A.** "What's the capital of France?" → "Paris." Text is fine. Generative UI adds complexity without value when the output is genuinely just a sentence.

**Don't use it when you need pixel-perfect control.** Generative UI gives you component-level control, not pixel-level control. If your brand guidelines specify exact spacing, colors, and animations that can't be captured in a component library, traditional frontends give you more precision.

## The Current Landscape

Generative UI is early. The major approaches:

**OpenUI** (Thesys) takes the DSL approach — a custom language called OpenUI Lang that's optimized for token efficiency and streaming. The model outputs compact, line-by-line component descriptions. A React renderer progressively hydrates them into interactive components. The format is 50%+ more token-efficient than JSON-based alternatives, which matters at scale.

**Vercel AI SDK** uses React Server Components and JSON patches (RFC 6902) to stream UI updates. The model outputs patch operations that incrementally build the component tree. The advantage is tight integration with the React/Next.js ecosystem. The tradeoff is more verbose output (more tokens per component).

**Custom implementations** exist across companies building AI-powered products — most use JSON-based component trees with proprietary renderers. These work but lack the streaming optimization and community tooling of dedicated frameworks.

The ecosystem is comparable to where frontend frameworks were in 2014 — multiple approaches, no clear winner, rapid iteration. What's clear is the direction: AI output will increasingly be structured UI, not just text.

## Getting Started

If you want to experiment with generative UI:

1. **Try the OpenUI playground** at [openui.com](https://www.openui.com/) — see what model-generated UIs look like in practice.

2. **Read the format spec** — understanding OpenUI Lang or the Vercel AI SDK's component model takes 30 minutes. The core concepts (component tree, props, composition) map directly to React/component thinking you already have.

3. **Build one component.** Take a common UI pattern from your app — a data table, a form, a dashboard card — and express it as a generative UI component. Then prompt a model to compose it with different data. That first "aha" moment, when the model produces a working UI you didn't hard-code, is when generative UI clicks.

The text ceiling is real. If you're building an AI application that outputs anything more complex than a paragraph, generative UI is the layer you're going to need. The question isn't whether — it's when.

---

*Generative UI is an active area of development. For the latest on OpenUI, see [github.com/thesysdev/openui](https://github.com/thesysdev/openui). For the Vercel AI SDK approach, see [sdk.vercel.ai](https://sdk.vercel.ai).*
