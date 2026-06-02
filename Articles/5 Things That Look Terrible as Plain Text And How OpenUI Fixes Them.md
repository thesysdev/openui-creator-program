# 5 Things That Look Terrible as Plain Text, and How OpenUI Fixes Them

AI products have a default output format: paragraphs, bullets, and the occasional Markdown table.

That format is fine when the answer is a definition or a short explanation. It breaks down when the answer is really an interface. A model can describe a dashboard, a pricing comparison, or an onboarding flow in text, but the user still has to do the UI work in their head.

This is where generative UI becomes more useful than another better-formatted chat response. With OpenUI, the model can stream structured UI that is rendered by a real React runtime. The result is still AI-generated, but it is not trapped inside text. Your app can define the components the model is allowed to use, generate instructions from that component library, and render the output progressively as it streams.

Below are five common outputs that are painful as plain text and much clearer as OpenUI-rendered UI. The examples are intentionally product-shaped: these are the kinds of responses teams already ask assistants to produce every day.

## 1. Pricing comparisons

Plain text pricing comparisons usually look acceptable for about ten seconds. Then someone asks, "Which plan has SSO?" or "What changes if we go annual?" and the answer becomes a wall of repeated bullets.

### Before: plain text

```txt
Starter is $19 per month and includes 3 seats, basic analytics, email support,
and 5 projects. Team is $49 per month and includes 10 seats, advanced analytics,
priority support, unlimited projects, and shared templates. Business is $99 per
month and includes 25 seats, SSO, audit logs, custom roles, priority support,
and unlimited projects.

Best option: Team, unless you need SSO or audit logs.
```

This has the information, but it is not doing the job of an interface. A user has to scan every sentence, remember which feature belongs to which plan, and translate "best option" into an actual decision.

### After: OpenUI-rendered comparison

Instead of asking the model for prose, the app can let it render a pricing comparison component:

```txt
<PricingComparison
  currency="USD"
  billingPeriod="monthly"
  highlightedPlan="team"
  plans={[
    {
      id: "starter",
      name: "Starter",
      price: 19,
      seats: 3,
      features: ["Basic analytics", "Email support", "5 projects"]
    },
    {
      id: "team",
      name: "Team",
      price: 49,
      seats: 10,
      features: [
        "Advanced analytics",
        "Priority support",
        "Unlimited projects",
        "Shared templates"
      ]
    },
    {
      id: "business",
      name: "Business",
      price: 99,
      seats: 25,
      features: ["SSO", "Audit logs", "Custom roles", "Priority support"]
    }
  ]}
/>
```

The difference is not cosmetic. A rendered comparison can:

- Keep plans in columns so features are comparable.
- Highlight the recommended plan without hiding the tradeoff.
- Add toggles for monthly vs annual billing.
- Show disabled or missing features clearly.
- Put the call to action next to the decision.

The model is still choosing what to show, but the product decides how comparisons are displayed.

## 2. Analytics summaries

Analytics are one of the worst things to paste into chat. A text response can say "revenue increased 12 percent, churn rose 2 points, and activation dropped in mobile signup," but the user has no shape of the data. They cannot see magnitude, trend, or priority at a glance.

### Before: plain text

```txt
Revenue is up 12% week over week, mostly from expansion revenue in enterprise
accounts. New trials are flat at 1,240. Activation dropped from 44% to 39%,
mainly on mobile. Churn increased from 3.1% to 5.2%. Support tickets are down
8%, but billing-related tickets are up 21%.

Recommended actions:
1. Investigate mobile signup drop-off.
2. Review billing changes from last week.
3. Follow up with enterprise accounts that expanded.
```

This is a useful written summary, but it is a weak operational surface. Every number has the same visual weight. The most urgent metric is buried in the middle.

### After: OpenUI-rendered dashboard

An OpenUI response can split the same analysis into metric cards, a trend chart, and a prioritized action panel:

```txt
<DashboardSummary>
  <MetricGrid>
    <MetricCard label="Revenue" value="$184k" delta="+12%" tone="positive" />
    <MetricCard label="Trials" value="1,240" delta="0%" tone="neutral" />
    <MetricCard label="Activation" value="39%" delta="-5 pts" tone="negative" />
    <MetricCard label="Churn" value="5.2%" delta="+2.1 pts" tone="negative" />
  </MetricGrid>

  <LineChart
    title="Activation by platform"
    series={[
      { name: "Desktop", data: [46, 47, 46, 45, 46] },
      { name: "Mobile", data: [42, 41, 40, 38, 34] }
    ]}
  />

  <ActionList
    items={[
      {
        priority: "High",
        title: "Investigate mobile signup drop-off",
        owner: "Growth",
        due: "Today"
      },
      {
        priority: "Medium",
        title: "Review billing ticket spike",
        owner: "Support Ops",
        due: "Tomorrow"
      }
    ]}
  />
</DashboardSummary>
```

The generated UI makes the response scannable. The user can see that revenue is good news, activation is the risk, and mobile is the likely source. Text can still explain the insight, but the interface carries the structure.

That distinction matters for AI copilots inside real products. A sales manager, product lead, or support ops owner does not just need a paragraph. They need a compact surface that helps them decide what to do next.

## 3. Forms and data collection

If an AI assistant tells a user "Please provide your company name, role, team size, budget, timeline, and integration requirements," it has not created a workflow. It has created homework.

Plain text is especially bad when the user needs to provide structured information back to the system.

### Before: plain text

```txt
To prepare your implementation plan, I need the following:

- Company name
- Your role
- Team size
- Current stack
- Main use case
- Budget range
- Target launch date
- Compliance requirements
- Whether you need SSO
```

The assistant knows the shape of the data it needs, but the user is still expected to answer in an unstructured message. That creates predictable problems:

- Missing fields.
- Ambiguous values.
- Follow-up questions that could have been prevented.
- Manual parsing on the backend.

### After: OpenUI-rendered intake form

OpenUI lets the model produce the actual collection surface:

```txt
<IntakeForm
  title="Implementation plan intake"
  sections={[
    {
      title: "Company",
      fields: [
        { type: "text", name: "companyName", label: "Company name", required: true },
        { type: "select", name: "role", label: "Your role", options: ["Founder", "Product", "Engineering", "Operations"] },
        { type: "number", name: "teamSize", label: "Team size", min: 1 }
      ]
    },
    {
      title: "Project",
      fields: [
        { type: "textarea", name: "useCase", label: "Main use case", required: true },
        { type: "date", name: "launchDate", label: "Target launch date" },
        { type: "checkbox", name: "needsSso", label: "Needs SSO" }
      ]
    }
  ]}
  submitLabel="Generate plan"
/>
```

Now the response is a workflow. Required fields can be enforced. Options can be constrained. The next model call can receive clean structured input instead of trying to infer meaning from a paragraph.

This is one of the quiet but important benefits of generative UI: the model can ask better questions without turning the product into a chat transcript.

## 4. Incident reports and operational triage

Incident reports often start in chat because someone asks, "What happened?" The answer quickly becomes a long chronological block: alerts, timestamps, suspected causes, affected services, owners, mitigations, and follow-up tasks.

As text, incident summaries are easy to write and hard to use.

### Before: plain text

```txt
At 09:12 UTC, API latency crossed the alert threshold. At 09:18, checkout
errors increased from 0.4% to 4.9%. The likely cause was a database connection
pool change deployed in release 2026.05.14-2. The team rolled back the release
at 09:41, and latency recovered by 09:47. Affected services were checkout-api,
payment-orchestrator, and order-worker. Next steps are to add a connection pool
load test, update the rollout checklist, and review alert thresholds.
```

This contains all the facts, but it forces responders to extract the incident model manually:

- Severity.
- Timeline.
- Blast radius.
- Current status.
- Follow-up tasks.

### After: OpenUI-rendered incident panel

The same information can become a triage surface:

```txt
<IncidentReport
  severity="SEV-2"
  status="Resolved"
  title="Checkout latency and elevated payment errors"
  impact="Checkout error rate peaked at 4.9% for 29 minutes."
>
  <Timeline
    events={[
      { time: "09:12 UTC", label: "API latency alert triggered" },
      { time: "09:18 UTC", label: "Checkout errors increased to 4.9%" },
      { time: "09:41 UTC", label: "Release 2026.05.14-2 rolled back" },
      { time: "09:47 UTC", label: "Latency returned to baseline" }
    ]}
  />

  <ServiceList
    services={[
      { name: "checkout-api", status: "Recovered" },
      { name: "payment-orchestrator", status: "Recovered" },
      { name: "order-worker", status: "Recovered" }
    ]}
  />

  <TaskList
    items={[
      { title: "Add connection pool load test", owner: "Platform", status: "Open" },
      { title: "Update rollout checklist", owner: "Release Eng", status: "Open" },
      { title: "Review checkout alert thresholds", owner: "SRE", status: "Open" }
    ]}
  />
</IncidentReport>
```

The UI does not make the incident less serious. It makes the response less fragile. Responders can scan status first, then timeline, then ownership. The model can still explain what likely happened, but the important operational fields are visible and structured.

For internal copilots, this is a huge difference. A good incident assistant should not only summarize logs. It should produce something close to the panel a responder wishes existed.

## 5. Product recommendations

Recommendations are another place where text looks worse than it feels while writing it. A model can describe three laptops, insurance plans, database vendors, or project management tools in paragraphs, but users compare with their eyes.

### Before: plain text

```txt
Option A is the best choice if you care most about battery life. It has a
14-hour battery estimate, weighs 2.7 pounds, and costs $1,249. Option B is
better for performance because it has more CPU cores and 32 GB of RAM, but it
costs $1,699 and weighs 3.4 pounds. Option C is the budget choice at $899, but
it only has 16 GB of RAM and a lower-resolution display.
```

Again, the answer is not wrong. It is just making the reader do unnecessary work.

### After: OpenUI-rendered recommendation cards

With OpenUI, the model can generate cards that preserve the comparison:

```txt
<RecommendationGrid
  context="Laptop shortlist"
  cards={[
    {
      title: "Option A",
      badge: "Best battery life",
      price: "$1,249",
      highlights: ["14-hour battery", "2.7 lb", "High-resolution display"],
      tradeoffs: ["16 GB RAM", "Midrange CPU"]
    },
    {
      title: "Option B",
      badge: "Best performance",
      price: "$1,699",
      highlights: ["32 GB RAM", "Fastest CPU", "Best for local builds"],
      tradeoffs: ["3.4 lb", "Higher price"]
    },
    {
      title: "Option C",
      badge: "Budget pick",
      price: "$899",
      highlights: ["Lowest price", "Good enough for web apps"],
      tradeoffs: ["Lower-resolution display", "Less upgrade headroom"]
    }
  ]}
/>
```

This layout lets the user compare across dimensions without rereading a paragraph. Each option has a label, price, strengths, and tradeoffs. The UI can also add filters, selected-state styling, or a "compare two" action if the product needs it.

The key is that the assistant is no longer limited to saying "Option B is better for performance." It can place that claim in an interface that makes the reason visible.

## What OpenUI changes

These examples are not about making chat prettier. The important shift is ownership of structure.

In a plain text assistant, structure is implied. The model writes:

- "Here are the three plans."
- "Here are the metrics."
- "Here are the fields I need."
- "Here is the incident timeline."
- "Here are the options."

Then the user has to reconstruct the interface mentally.

In an OpenUI-style assistant, structure is explicit. The app defines components, the model emits structured UI using those components, and the renderer turns the stream into a real interface. The model can still explain, summarize, and reason in text. It just does not have to force every result into text.

There is also a product safety benefit. When you define the component library, you constrain what the model can render. You are not asking it to invent arbitrary frontend code for every response. You are giving it a controlled vocabulary: metric cards, charts, forms, timelines, task lists, comparison cards, and whatever else makes sense for your product.

That controlled vocabulary is the difference between "the model generated a UI" and "the product let the model assemble a UI we can actually support."

## A practical way to decide when text is not enough

Plain text is still the right output for many tasks. Use it for explanations, drafts, summaries, and cases where the user mainly needs language.

Reach for generative UI when the answer has one of these shapes:

- The user needs to compare options.
- The user needs to act on structured data.
- The user needs to fill in information.
- The output has status, priority, ownership, or progress.
- The user would naturally screenshot it, sort it, filter it, or click it.

That last test is useful. If the best version of the answer looks like a table, chart, form, card grid, timeline, or control panel, plain text is probably the wrong final surface.

OpenUI does not remove language from AI products. It gives language somewhere better to land.

## Resources

- [OpenUI GitHub](https://github.com/thesysdev/openui)
- [OpenUI docs](https://www.openui.com)
- [OpenUI playground](https://www.openui.com/playground)
