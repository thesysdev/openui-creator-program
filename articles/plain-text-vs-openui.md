# 5 Things That Look Terrible as Plain Text (And How OpenUI Fixes Them)

You've seen it a hundred times. You ask an AI assistant a question, and it responds with a wall of text. Maybe there's a table — if you're lucky, rendered in ASCII art. Maybe there's a list. Maybe there are bullet points with bold headings. But at the end of the day, it's all just... text.

The problem isn't the content. Large language models are remarkably good at understanding what you need and generating useful information. The problem is the *medium*. Plain text — even rich markdown — is fundamentally limited in what it can express. It can't show you a chart. It can't let you click a button. It can't give you an interactive form that adapts to your input. It can only describe these things and hope your imagination fills in the gaps.

This article walks through five scenarios where plain text fails and OpenUI succeeds. Each one is a real, everyday use case — not a hypothetical. And each one demonstrates why the gap between "describing an interface" and "generating an interface" is the single biggest opportunity in AI UX right now.

---

## 1. Flight Search Results

### Plain Text: The Wall of Departures

Ask any AI chatbot to find flights from San Francisco to Tokyo, and you'll get something like this:

```
Here are some flights from SFO to NRT on March 15:

1. Japan Airlines JL1 — Departs 11:30 AM, arrives 3:45 PM+1
   Duration: 11h 15m | Economy: $680 | Business: $3,200

2. ANA NH7 — Departs 1:15 PM, arrives 5:30 PM+1
   Duration: 11h 15m | Economy: $720 | Business: $3,450

3. United UA837 — Departs 10:45 AM, arrives 2:30 PM+1
   Duration: 10h 45m | Economy: $590 | Business: $2,900

4. Singapore Airlines SQ33 — Departs 2:00 AM, arrives 7:15 AM+1
   Duration: 11h 15m | Economy: $650 | Business: $3,100
```

This works. You can read it. But consider what you *can't* do:

- **Sort by price, duration, or departure time** — you're reading the model's chosen order
- **Filter by airline or class** — you see everything or nothing
- **Compare side by side** — the vertical list format makes visual comparison difficult
- **Select a flight** — you'd need to describe your choice in a follow-up message
- **See price trends** — is $590 a good deal? You'd need another query

### OpenUI: The Interactive Card Grid

With OpenUI, the same LLM generates an interactive card grid instead of a text list:

```
root = Grid(3)
flight1 = FlightCard(
  airline="Japan Airlines",
  flightNumber="JL1",
  depart="SFO 11:30 AM",
  arrive="NRT 3:45 PM+1",
  duration="11h 15m",
  economyPrice="$680",
  businessPrice="$3,200",
  onSelect={tool: "bookFlight", args: {flightId: "JL1"}}
)
flight2 = FlightCard(
  airline="ANA",
  flightNumber="NH7",
  depart="SFO 1:15 PM",
  arrive="NRT 5:30 PM+1",
  duration="11h 15m",
  economyPrice="$720",
  businessPrice="$3,450",
  onSelect={tool: "bookFlight", args: {flightId: "NH7"}}
)
root = Grid([flight1, flight2, flight3, flight4])
```

Each card is a live React component. You can click "Select" to book. The grid layout makes visual comparison instant. The model chose the right component for the job — not because it was hardcoded to, but because your component library includes `FlightCard` and the model knows a flight search should use it.

**The difference:** Plain text *describes* four flights. OpenUI *gives you* four flights you can act on.

---

## 2. Weather Forecasts

### Plain Text: The Paragraph Forecast

```
Weather for New York City, March 15-17:

Today (Friday): Partly cloudy, high 52°F, low 38°F.
Winds from the NW at 12-18 mph. 10% chance of rain.

Saturday: Increasing clouds, high 55°F, low 41°F.
Winds from the W at 8-12 mph. 30% chance of rain in the evening.

Sunday: Rain likely, high 48°F, low 35°F.
Winds from the NE at 15-25 mph. 70% chance of rain. Expect 0.5-1 inch of rainfall.

The weekend will start mild but deteriorate quickly. Plan outdoor activities for Saturday morning if possible.
```

This is readable. But a weather forecast is inherently *visual* — it's about trends over time, intensity levels, and conditional probabilities. A paragraph flattens all that into a linear reading experience.

What you can't see at a glance:
- The temperature *trend* (warming, then cooling)
- The rain probability curve (10% → 30% → 70%)
- The wind speed shift (moderate → calm → strong)

### OpenUI: The Visual Forecast Strip

```
root = WeatherForecast(days=[day1, day2, day3])
day1 = DayForecast(
  date="Fri Mar 15",
  condition="partly-cloudy",
  high=52, low=38,
  wind="NW 12-18 mph",
  rainChance=10,
  icon="⛅"
)
day2 = DayForecast(
  date="Sat Mar 16",
  condition="increasing-clouds",
  high=55, low=41,
  wind="W 8-12 mph",
  rainChance=30,
  icon="🌤️"
)
day3 = DayForecast(
  date="Sun Mar 17",
  condition="rain",
  high=48, low=35,
  wind="NE 15-25 mph",
  rainChance=70,
  icon="🌧️"
  alert="Rain expected: 0.5-1 inch"
)
root = WeatherForecast([day1, day2, day3])
```

The rendered output shows three side-by-side forecast panels with weather icons, temperature bars, and a rain probability indicator. Sunday's panel has a yellow alert badge. The visual trend — warming Saturday, then a sharp drop Sunday — is immediately obvious without reading a single word.

**The difference:** Plain text *tells you* the weather. OpenUI *shows you* the weather pattern, and your brain processes it 10x faster.

---

## 3. Product Comparisons

### Plain Text: The Messy Markdown Table

```
Here's a comparison of three noise-cancelling headphones:

| Feature | Sony WH-1000XM5 | Bose QC Ultra | Apple AirPods Max |
|---------|-----------------|---------------|-------------------|
| Price | $348 | $429 | $549 |
| Battery | 30 hours | 24 hours | 20 hours |
| ANC Quality | ★★★★★ | ★★★★★ | ★★★★☆ |
| Sound Quality | ★★★★★ | ★★★★☆ | ★★★★☆ |
| Weight | 250g | 250g | 384g |
| Multipoint | Yes | Yes | No |
| Foldable | Yes | Yes | No |
| Spatial Audio | Yes | No | Yes |
| Mic Quality | ★★★★☆ | ★★★★☆ | ★★★★★ |

Recommendation: For most people, the Sony WH-1000XM5 offers the best balance of price, battery, and ANC. If you're in the Apple ecosystem, AirPods Max integrates seamlessly but costs significantly more and is heavier.
```

This table is fine for scanning, but it has real limitations:
- You can't **hide columns** you don't care about
- You can't **sort by priority** — what matters most to you?
- You can't **weight features** — maybe battery matters twice as much as price
- The **recommendation** is generic — it doesn't know *you*

### OpenUI: The Interactive Comparison Matrix

```
root = ProductComparison(products=[sony, bose, apple])
sony = ProductCard(
  name="Sony WH-1000XM5",
  price=348,
  image="sony-xm5.jpg",
  highlights=["30hr battery", "Best ANC", "Foldable"],
  rating=4.7,
  specs=[
    Spec(key="Battery", value="30 hours", score=5),
    Spec(key="ANC", value="Excellent", score=5),
    Spec(key="Weight", value="250g", score=4),
    Spec(key="Price", value="$348", score=5)
  ],
  badge="Best Value"
)
bose = ProductCard(
  name="Bose QC Ultra",
  price=429,
  image="bose-qc-ultra.jpg",
  highlights=["24hr battery", "Top ANC", "Comfort"],
  rating=4.6,
  specs=[
    Spec(key="Battery", value="24 hours", score=4),
    Spec(key="ANC", value="Excellent", score=5),
    Spec(key="Weight", value="250g", score=4),
    Spec(key="Price", value="$429", score=3)
  ]
)
apple = ProductCard(
  name="Apple AirPods Max",
  price=549,
  image="airpods-max.jpg",
  highlights=["Spatial Audio", "Best mic", "Apple ecosystem"],
  rating=4.5,
  specs=[
    Spec(key="Battery", value="20 hours", score=3),
    Spec(key="ANC", value="Very Good", score=4),
    Spec(key="Weight", value="384g", score=2),
    Spec(key="Price", value="$549", score=2)
  ]
)
root = ProductComparison(products=[sony, bose, apple], highlight="sony")
```

The rendered comparison shows three product cards side by side with score bars, badges for top picks, and expandable spec sections. The "Best Value" badge on the Sony card makes the recommendation visual, not just textual. Each card can have a "Learn more" button that triggers a follow-up query.

**The difference:** Plain text gives you a *table someone else designed*. OpenUI gives you a *comparison interface the AI designed for this specific query*.

---

## 4. Step-by-Step Instructions

### Plain Text: The Linear Tutorial

```
Here's how to deploy a Next.js app to Vercel:

1. First, install the Vercel CLI:
   npm install -g vercel

2. Navigate to your project directory:
   cd my-nextjs-app

3. Run the deploy command:
   vercel

4. The CLI will ask you some questions:
   - "Set up and deploy?" → Yes
   - "Which scope?" → Select your account
   - "Link to existing project?" → No (for first deploy)
   - "Project name?" → Press Enter for default or type a name
   - "Directory?" → Press Enter for current directory

5. After configuration, Vercel will deploy your app and give you a URL like:
   https://my-nextjs-app.vercel.app

6. For production deployment, run:
   vercel --prod

Done! Your app is now live.
```

This works for following along. But consider the friction:

- **No progress indicator** — where am I in the process? Am I on step 3 of 6?
- **No branching** — what if I already have the CLI installed? What if I need to authenticate first?
- **No visual feedback** — the CLI output is described, not shown
- **No "do this next" state** — after deployment, what about custom domains? Environment variables?

### OpenUI: The Guided Stepper

```
root = Stepper(steps=[step1, step2, step3, step4, step5, step6], current=0)
step1 = Step(
  title="Install Vercel CLI",
  description="Run the command below in your terminal",
  code="npm install -g vercel",
  status="completed",
  action={label: "Already installed", tool: "nextStep"}
)
step2 = Step(
  title="Navigate to project",
  description="Change to your project directory",
  code="cd my-nextjs-app",
  status="current",
  tip="Make sure you're in the root directory where package.json lives"
)
step3 = Step(
  title="Deploy",
  description="Run the deploy command and answer the prompts",
  code="vercel",
  status="pending",
  note="First deploy will ask setup questions — accept defaults for a new project"
)
step4 = Step(
  title="Get your URL",
  description="Vercel will output your deployment URL",
  output="https://my-nextjs-app.vercel.app",
  status="pending"
)
step5 = Step(
  title="Deploy to production",
  description="When ready, deploy to production",
  code="vercel --prod",
  status="pending"
)
step6 = Step(
  title="Next steps",
  description="Your app is live! Consider these optional improvements",
  recommendations=[
    Recommendation(label: "Add custom domain", tool: "addDomain"),
    Recommendation(label: "Set environment variables", tool: "addEnv"),
    Recommendation(label: "View analytics", tool: "viewAnalytics")
  ],
  status="pending"
)
root = Stepper([step1, step2, step3, step4, step5, step6])
```

The stepper shows a vertical progress indicator on the left, with completed steps checked off, the current step highlighted, and future steps grayed out. Each step has a copy-to-clipboard button for commands. Step 6 offers clickable action buttons for common follow-up tasks.

**The difference:** Plain text gives you a *reading assignment*. OpenUI gives you a *guided workflow* that tracks your progress and adapts to where you are.

---

## 5. Data Visualizations and Charts

### Plain Text: The ASCII Chart

```
Monthly active users for your app (2026):

Jan: ████████████████ 12,400
Feb: ██████████████████ 14,200
Mar: ████████████████████ 16,800
Apr: █████████████████████ 18,100
May: ████████████████████████ 21,500
Jun: ██████████████████████████ 24,300

Key insights:
- Growth rate: ~15% month-over-month
- May saw the biggest jump (+18.8%) — likely from the Product Hunt launch
- If trend continues, expect ~28,000 by July

Breakdown by platform:
- Web: 58% (14,094)
- iOS: 28% (6,804)
- Android: 14% (3,402)
```

The ASCII bar chart is a noble effort. But it's lying to you. Those block characters have limited resolution — you can't see the difference between 18,100 and 18,200. You can't hover to see exact values. You can't zoom in on a specific month. You can't toggle between MAU, DAU, and new users.

And the "breakdown by platform" — that's a pie chart dying to be born. 58%, 28%, 14% in a text list doesn't communicate *proportion* the way a visual does.

### OpenUI: The Interactive Dashboard

```
root = AnalyticsDashboard(metrics=[mau_chart, platform_chart, insights])
mau_chart = LineChart(
  data=[
    DataPoint(label="Jan", value=12400),
    DataPoint(label="Feb", value=14200),
    DataPoint(label="Mar", value=16800),
    DataPoint(label="Apr", value=18100),
    DataPoint(label="May", value=21500),
    DataPoint(label="Jun", value=24300)
  ],
  title="Monthly Active Users",
  trend="up",
  trendValue="+15% MoM",
  annotations=[
    Annotation(at="May", label="Product Hunt launch", color="green")
  ],
  yAxis={format: "number"},
  interactive=true
)
platform_chart = PieChart(
  data=[
    Slice(label="Web", value=58, color="blue"),
    Slice(label="iOS", value=28, color="gray"),
    Slice(label="Android", value=14, color="orange")
  ],
  title="Platform Breakdown"
)
insights = InsightList(items=[
  Insight(text="Growth rate: ~15% month-over-month", type="positive"),
  Insight(text="May saw biggest jump (+18.8%) — Product Hunt launch effect", type="highlight"),
  Insight(text="Projected July: ~28,000 users", type="forecast")
])
root = AnalyticsDashboard([mau_chart, platform_chart, insights])
```

The rendered dashboard shows a live line chart with hover states, an animated pie chart with a center label, and an insight panel. The May annotation marker is clickable — it could open the Product Hunt campaign details. The pie chart segments are interactive, expanding on hover to show exact numbers.

**The difference:** Plain text *approximates* your data. OpenUI *renders* your data — with precision, interactivity, and visual fidelity that ASCII blocks can never match.

---

## Why This Matters Beyond Aesthetics

You might read these five examples and think: "Sure, it looks nicer. But does it matter?"

It does. And not for the reason you think.

The real cost of plain text AI isn't ugly formatting. It's **cognitive overhead**. Every time a user reads a text list and mentally converts it into a comparison, every time they parse an ASCII chart and try to extract a trend, every time they count steps in a tutorial to track progress — that's *their* brain doing work the AI should have done.

Research in information visualization consistently shows that visual representations are processed 60,000x faster than text (3M Corporation, 2001). Interactive interfaces don't just look better — they *reduce the time between seeing information and acting on it.*

### The Generative UI Advantage

Traditional UI development requires a designer to anticipate every possible interface need and a developer to build it. That's why most AI products have one layout for everything: a chat window with text responses.

OpenUI changes the equation:

1. **You define a component library** — charts, cards, steppers, forms, dashboards. The building blocks.
2. **The LLM generates the layout** — it picks the right components, configures them with data, and composes them into a coherent interface.
3. **The renderer brings it to life** — each component is a real React element, interactive and responsive.

The model doesn't generate HTML or CSS. It generates OpenUI Lang — a compact, streamable language that describes *what* to render, not *how*. The `Renderer` component on the client maps these descriptions to your React components in real time.

This means:
- **No hardcoded templates.** The interface adapts to the query.
- **No design debt.** The component library enforces consistency.
- **No latency penalty.** OpenUI Lang is up to 67% more token-efficient than JSON-based approaches, and it streams — the first component renders while the rest of the response is still being generated.

### Getting Started

The simplest path to trying OpenUI:

```bash
npx @openuidev/cli@latest create
```

This scaffolds a project with the OpenUI React runtime, a sample component library, and a working chat interface. From there, you define your own components using `defineComponent`, register them with `createLibrary`, and the model handles the rest.

The [OpenUI docs](https://www.openui.com/docs) cover the full architecture: component definition, system prompt generation, streaming, interactivity, and the OpenUI Lang specification. The [Playground](https://www.openui.com/playground) lets you experiment live without setting up a project.

---

## The Bottom Line

Plain text was the right interface for AI when AI could only generate text. But LLMs have moved past that limitation — they can compose structured, interactive UI in real time. The medium needs to catch up.

These five scenarios — flight search, weather forecasts, product comparisons, step-by-step guides, and data visualizations — aren't edge cases. They're the most common types of queries users make. Every day, millions of people receive text descriptions of things that should be interfaces.

OpenUI doesn't just make AI responses prettier. It makes them *functional*. It turns information into interaction. And it does it with a framework that's open-source, token-efficient, and streamable from the first token.

The question isn't whether generative UI is better than plain text. The question is why we ever accepted plain text in the first place.

---

*Built with [OpenUI](https://www.openui.com/) — the open standard for generative UI. Star us on [GitHub](https://github.com/thesysdev/openui).*
