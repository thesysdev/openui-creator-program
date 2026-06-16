# 5 Things That Look Terrible as Plain Text (And How OpenUI Fixes Them)

Most AI products still end in text.

That sounds harmless until the answer is not really a sentence-shaped answer. A model can understand a request, call tools, compare options, calculate totals, and produce a useful plan. Then the product flattens the result into paragraphs, bullets, or a markdown table and asks the user to do the interface work in their head.

Plain text is great for explanation. It is weak at comparison, triage, inspection, editing, selection, and action. Those are interface jobs.

Generative UI is not about making chatbot responses prettier. It is about letting the model compose the right working surface from components your app already trusts. OpenUI gives that process a practical shape: you define a component library, OpenUI generates prompt instructions from that library, the model responds in OpenUI Lang, and the renderer maps that stream back to real UI.

The difference becomes obvious when you look at concrete cases. Here are five common AI responses that look terrible as plain text, and what they become when rendered as task-specific UI.

## 1. Product Comparisons

Product comparison is one of the fastest ways to expose the limits of text.

Ask an assistant to compare three laptops, three pricing plans, or three vendors and you usually get a list like this:

```text
Option A is cheaper and has 16GB RAM, but the battery is weaker.
Option B has better battery life and a nicer display, but costs more.
Option C is the most powerful, but it is probably overkill unless you edit video.
```

That is readable, but it is not inspectable. The user has to remember which option had which tradeoff. If there are more than three attributes, the comparison starts to collapse. If the user cares about one attribute more than another, text offers no obvious way to re-rank.

A markdown table helps, but only a little:

```markdown
| Laptop | Price | RAM | Battery | Best for |
| --- | ---: | ---: | --- | --- |
| A | $999 | 16GB | 8h | Students |
| B | $1299 | 16GB | 14h | Travel |
| C | $1799 | 32GB | 10h | Video work |
```

The table is still passive. It cannot expose details on demand. It cannot mark the current best choice after the user changes priorities. It cannot let the user compare only two rows or save a shortlist.

In OpenUI, the model can produce a comparison surface instead of a paragraph:

```text
root = ComparisonBoard({
  title: "Laptop shortlist",
  criteria: ["Price", "RAM", "Battery", "Weight", "Best for"],
  items: [laptopA, laptopB, laptopC],
  recommendedItemId: "laptop-b"
})
laptopA = ProductOption({ name: "Aero 14", price: 999, ram: "16GB", battery: "8h", weight: "1.4kg", bestFor: "Students" })
laptopB = ProductOption({ name: "Nomad Pro", price: 1299, ram: "16GB", battery: "14h", weight: "1.2kg", bestFor: "Travel" })
laptopC = ProductOption({ name: "Studio Max", price: 1799, ram: "32GB", battery: "10h", weight: "1.8kg", bestFor: "Video work" })
```

Those component names are just examples. The important part is the contract. Your app decides that `ComparisonBoard` and `ProductOption` exist, what props they accept, and what actions they expose. The model chooses and configures them.

Now the response can highlight the recommended option, collapse less important specs, show tradeoffs as badges, and let the user adjust priorities. Text can still explain the recommendation, but the comparison itself belongs in UI.

The user does not need a better paragraph. They need a surface for deciding.

## 2. Analytics Answers

Data answers often start with text because text feels natural:

```text
Revenue increased 8.2% this week. The strongest growth came from enterprise accounts in the northeast region. Churn was mostly flat, but expansion revenue from existing customers offset two lost accounts.
```

That is useful for a status update. It is not enough for analysis.

When a user asks "Why did revenue move this week?", they are rarely asking for a final sentence. They want to inspect the trend, see the segment split, compare outliers, and decide what to do next. Plain text hides the shape of the data.

A better response is mixed:

- a short narrative summary,
- a chart showing the week-over-week movement,
- a breakdown table,
- anomalies or drivers,
- and follow-up actions.

With OpenUI, the model can render that structure progressively:

```text
root = AnalyticsAnswer({
  summary: "Revenue increased 8.2% week over week, driven mostly by enterprise expansion.",
  chart: revenueChart,
  drivers: driverTable,
  actions: actionList
})
revenueChart = LineChart({ title: "Revenue by day", series: weeklyRevenue })
driverTable = DataTable({ columns: ["Driver", "Impact", "Segment"], rows: driverRows })
actionList = ActionList({ actions: ["Inspect enterprise deals", "Open churn accounts", "Export driver table"] })
```

This is where OpenUI's streaming-first design matters. A user should not wait for the entire analytical object to finish before seeing anything. The frame can render first. The summary can arrive next. The chart can fill as data streams. A table can appear before every row is complete.

The result feels less like a chatbot answer and more like a temporary analytics workspace shaped around the current question.

Text still has a role. It tells the user what to look at. But it should not be the only artifact when the answer depends on structured data.

## 3. Multi-Step Plans

AI assistants are good at creating plans. Unfortunately, plans often become long numbered lists:

```text
1. Create a staging database.
2. Export the production schema.
3. Run migrations in staging.
4. Validate constraints.
5. Update the application connection string.
6. Run smoke tests.
7. Monitor logs for 30 minutes.
```

This is fine for reading. It is poor for execution.

Real plans have dependencies, owners, states, risks, blocked steps, and decisions. Some steps are optional. Some should not be started until a previous check passes. Some need approvals. A plain list makes every item look equally simple.

A generated interface can turn the same plan into something operational:

```text
root = Runbook({
  title: "Staging migration checklist",
  phases: [prep, migration, validation, monitoring],
  riskLevel: "medium"
})
prep = ChecklistPhase({
  name: "Preparation",
  items: [
    Step({ label: "Create staging database", status: "ready" }),
    Step({ label: "Export production schema", status: "blocked", reason: "Needs read-only credential" })
  ]
})
migration = ChecklistPhase({ name: "Migration", items: migrationSteps })
validation = ChecklistPhase({ name: "Validation", items: validationSteps })
monitoring = ChecklistPhase({ name: "Monitoring", items: monitoringSteps })
```

Now the user can see state. They can identify the blocker. They can expand a step for commands or rollback notes. They can mark items complete. They can hand the runbook to another person without losing context.

This is especially important for internal tools and agent workflows. If an agent proposes a multi-step operation, the user should not have to copy a numbered list into a project board to make it usable. The response itself should be a working checklist.

The OpenUI approach keeps that safe because the model is not emitting arbitrary application code. It is composing approved components with typed props. Your app controls what a `Runbook`, `Step`, or `ApprovalGate` can do.

## 4. Forms and Configuration

Some answers are not answers at all. They are missing-input conversations.

For example:

```text
To create the campaign, I need the audience segment, budget, start date, end date, channel, and approval owner.
```

That is technically correct, but it makes the user do extra work. They have to reply in prose and hope the model parses it. If the model misses one field, the conversation keeps stretching.

The right output is a form.

```text
root = CampaignForm({
  title: "Create campaign",
  fields: [audience, budget, dates, channel, approver],
  submitLabel: "Create draft campaign"
})
audience = SelectField({ label: "Audience", options: ["Trial users", "Enterprise admins", "Churn risk"] })
budget = CurrencyField({ label: "Budget", currency: "USD", min: 100 })
dates = DateRangeField({ label: "Run dates" })
channel = MultiSelectField({ label: "Channels", options: ["Email", "LinkedIn", "In-app"] })
approver = UserPicker({ label: "Approval owner" })
```

A form makes the missing information explicit. It reduces ambiguity. It lets the app validate before anything is submitted. It also gives the user confidence that the agent understood the task as a workflow, not just a prompt.

Plain text is particularly bad for configuration because it hides constraints. Is budget required? What are valid channels? Can the date range start today? Is there a default approver? Text can explain those rules, but UI can enforce them.

This is one of the clearest wins for generative UI. The model does not need to invent a custom form renderer. It only needs to choose from the fields your product already supports.

## 5. Search Results and Recommendations

Search is another place where text gets awkward quickly.

Ask for "the best restaurants near the conference venue for a team dinner" and a text assistant might respond:

```text
Here are a few options:
- North Table: modern American, 0.3 miles away, good for groups.
- Saffron Room: Indian, 0.6 miles away, private dining available.
- Bar Molino: Italian, 0.4 miles away, lively but can be loud.
```

Again, this is useful but incomplete. Recommendations are not just facts. They involve distance, price, availability, constraints, tradeoffs, and actions.

A better surface could combine cards, filters, a map, and booking actions:

```text
root = RecommendationResults({
  title: "Team dinner options near the venue",
  filters: dinnerFilters,
  items: [northTable, saffronRoom, barMolino],
  map: venueMap
})
dinnerFilters = FilterBar({ chips: ["Private room", "Under 0.5 miles", "Vegetarian friendly"] })
northTable = PlaceCard({ name: "North Table", distance: "0.3 mi", price: "$$$", tags: ["Groups", "Quiet"], action: "Check availability" })
saffronRoom = PlaceCard({ name: "Saffron Room", distance: "0.6 mi", price: "$$", tags: ["Private dining", "Vegetarian"], action: "View menu" })
barMolino = PlaceCard({ name: "Bar Molino", distance: "0.4 mi", price: "$$", tags: ["Lively", "Italian"], warning: "Can be loud" })
```

The key is not that the result looks nicer. It is that the user can work with it. They can filter. They can compare. They can choose. They can take the next action without rephrasing the request.

This applies to products, candidates, support tickets, documents, flights, apartments, APIs, and almost any result set. Once an answer contains multiple candidates, plain text becomes a bottleneck.

## What OpenUI Changes

OpenUI changes the handoff between the model and the application.

In a normal chatbot, the model produces text and the frontend displays it. In a hardcoded app, the frontend owns the interface and the model fills in small bits of content. Both approaches are useful, but both are limited.

OpenUI introduces a middle path:

1. The developer defines a component library.
2. The component library becomes part of the model instructions.
3. The model emits OpenUI Lang instead of raw code or bulky JSON.
4. The renderer parses the stream and maps it to trusted React components.
5. The user gets a real interface, not a screenshot of one.

That matters for safety and maintainability. The model is not allowed to invent arbitrary UI code. It can only compose the components you expose. If your app has `DataTable`, `MetricCard`, `ApprovalGate`, and `DateRangeField`, those are the building blocks. The generated interface remains inside your product system.

It also matters for cost and latency. OpenUI Lang is compact and line-oriented, so it is friendlier to streaming than waiting for a full JSON tree to become valid. The OpenUI docs describe the renderer parsing each line as it arrives, letting structure appear before the whole response is complete.

For users, the difference is simple: the assistant stops handing them text descriptions of work and starts handing them the work surface itself.

## When Text Is Still the Right UI

Not every response should become a component tree.

If the user asks for a definition, a short explanation, a rewrite, or a quick answer, text is still the right surface. A generated UI should earn its place. It should appear when it gives the user better control, better inspection, or a shorter path to action.

A good rule of thumb:

- Use text for explanation.
- Use UI for structure.
- Use actions for commitment.

The best generative UI experiences combine all three. The model explains the intent, renders the structure, and exposes safe actions where the user can decide what happens next.

## The Practical Shift

The practical shift is not "AI can generate UI now." That framing makes it sound like a novelty.

The better framing is this:

When an AI response contains data, choices, constraints, state, or next actions, it should not be trapped in prose.

Product comparisons want comparison boards. Analytics answers want charts and tables. Plans want runbooks. Missing inputs want forms. Search results want cards, filters, and maps.

Plain text can describe all of these, but it cannot carry the interaction. OpenUI lets the model compose interfaces from the components your app already trusts, so the response can become something the user can inspect, edit, and act on.

That is the "aha" moment. Generative UI is not decoration after the answer. It is the answer taking the right shape.
