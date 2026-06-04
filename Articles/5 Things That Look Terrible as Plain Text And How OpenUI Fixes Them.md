# 5 Things That Look Terrible as Plain Text And How OpenUI Fixes Them

Text is the default output format for most AI products because it is easy to stream, easy to store, and easy to render anywhere. That default is useful for simple answers. It is also a trap.

The moment an assistant needs to compare options, gather information, explain a workflow, summarize operational data, or help someone make a decision, plain text starts doing work it was never meant to do. The model has structure in its reasoning, but the product collapses that structure into paragraphs, bullets, and markdown tables. Users then have to rebuild the interface in their head.

That is the gap OpenUI is designed to close. OpenUI treats model output as something that can become an interface, not only a message. Its core idea is OpenUI Lang: a compact, streaming-first language for describing UI with a controlled component library. The application defines which components the model can use, generates prompt instructions from that component library, streams OpenUI Lang back from the model, and progressively renders the result in React.

That sounds technical, but the product effect is simple: the answer can arrive as the right working surface for the task.

Below are five common AI responses that look awkward as plain text, and how the same information becomes more useful when rendered as generative UI.

## 1. Product Comparisons

Product comparison is one of the most common chatbot use cases. It is also one of the first places plain text breaks down.

A user does not want a mini essay about three tools. They want to compare tradeoffs, scan differences, filter by priorities, and make a decision.

### The plain-text version

```txt
Here is a comparison of the three options:

Option A is best if you want a low-cost solution. It includes basic reporting,
simple integrations, and email support. It may not work well if you need
advanced permissions or custom workflows.

Option B is better for growing teams. It includes everything in Option A,
plus role-based access, audit logs, and SSO. It is more expensive but more
scalable.

Option C is best for enterprise teams. It includes advanced security,
custom onboarding, and dedicated support. It is the most expensive option
and may be too heavy for smaller teams.
```

This is readable, but it forces the user to keep the comparison in memory. If they want to answer "which one has SSO?" or "what is the cheapest option with audit logs?", they have to reread the whole block.

Markdown tables help a little:

```md
| Option | Best for | Key features | Tradeoff |
|---|---|---|---|
| A | Small teams | Basic reporting, integrations | Limited permissions |
| B | Growing teams | RBAC, audit logs, SSO | Higher cost |
| C | Enterprise | Security, onboarding, support | Heavyweight |
```

Better, but still static. The user cannot sort, highlight must-haves, choose weights, or ask the interface to narrow the options.

### The OpenUI version

The same answer works better as a comparison card set plus a table:

```txt
root = Stack([title, summary, filters, cards, table, cta])
title = TextContent("Compare your options", "large-heavy")
summary = TextContent("Option B is the best fit if SSO and audit logs matter, while Option A is the lowest-cost choice.", "medium")
filters = Buttons([costBtn, securityBtn, teamBtn], "row")
costBtn = Button("Prioritize cost", "secondary")
securityBtn = Button("Prioritize security", "secondary")
teamBtn = Button("Growing team", "primary")
cards = Columns([optionA, optionB, optionC])
optionA = Card("Option A", "Lowest cost", ["Basic reporting", "Simple integrations", "Email support"])
optionB = Card("Option B", "Best balance", ["RBAC", "Audit logs", "SSO"])
optionC = Card("Option C", "Enterprise ready", ["Advanced security", "Custom onboarding", "Dedicated support"])
table = Table([planCol, priceCol, ssoCol, auditCol, fitCol])
planCol = Col("Plan", ["A", "B", "C"])
priceCol = Col("Relative cost", ["Low", "Medium", "High"])
ssoCol = Col("SSO", ["No", "Yes", "Yes"])
auditCol = Col("Audit logs", ["No", "Yes", "Yes"])
fitCol = Col("Fit", ["Small teams", "Growing teams", "Enterprise"])
cta = Button("Show only plans with SSO", "primary")
```

The point is not that every comparison needs fancy UI. The point is that comparison is inherently spatial. Users compare across rows and columns. A generated interface can preserve that structure instead of flattening it into prose.

OpenUI also gives the application control over the available components. The model is not inventing arbitrary HTML. It is choosing from a component library the developer has already defined, which makes the output easier to validate and render safely.

## 2. Forms And Intake Flows

Plain text is especially weak when the assistant needs information from the user.

Many AI products still handle intake like this:

```txt
To create your travel policy, please provide:

1. Your company name
2. The maximum hotel budget per night
3. Whether employees can book business class
4. Which countries require pre-approval
5. Who should approve exceptions
```

The user then replies in free text:

```txt
Company is Acme. Hotel budget is 220 in the US, 180 in Europe, no business
class except flights over 8 hours. China and Brazil need approval. CFO approves.
```

Now the model has to parse a paragraph, infer missing values, and ask follow-up questions. This is fine for one field. It gets messy for any workflow with validation, branching, or review.

### The plain-text problem

Text makes the user do too much formatting work. It also hides errors until later.

If "220" is meant to be USD, the assistant has to infer that. If "Europe" needs country-level handling, the assistant has to clarify. If the CFO should approve only international exceptions, the assistant needs another turn.

This is not a model problem. It is an interface problem.

### The OpenUI version

The same task should render as a generated form:

```txt
root = Stack([title, intro, policyForm, review])
title = TextContent("Create a travel policy", "large-heavy")
intro = TextContent("Fill the fields below. I will generate the first draft after validation.", "medium")
policyForm = Form([company, hotelUs, hotelEu, businessClass, approvalCountries, approver])
company = TextInput("Company name", "Acme Inc.")
hotelUs = NumberInput("US hotel budget per night", 220, "USD")
hotelEu = NumberInput("Europe hotel budget per night", 180, "USD")
businessClass = Select("Business class rule", ["Never", "Flights over 8 hours", "Manager approval"])
approvalCountries = MultiSelect("Countries requiring pre-approval", ["China", "Brazil"])
approver = TextInput("Exception approver", "CFO")
review = Button("Generate policy draft", "primary")
```

This does three important things:

- It captures structured data instead of hoping the model parses a paragraph correctly.
- It lets the frontend validate fields before the assistant acts.
- It creates a natural review step before anything is submitted.

For developers, this is where generative UI starts to feel less like a demo and more like product infrastructure. The model decides which form is useful for the task, but the app still owns the components, validation rules, and actions.

## 3. Troubleshooting Instructions

Troubleshooting is another place where plain text becomes fragile.

Consider a developer asking why their OAuth callback fails in production.

### The plain-text version

```txt
Here are some things to check:

- Make sure the redirect URL in your provider dashboard exactly matches your app.
- Confirm that your production environment has the correct CLIENT_ID and CLIENT_SECRET.
- Check that cookies are configured with Secure and SameSite settings.
- Look at your server logs for the callback route.
- Try clearing the browser cache and signing in again.
```

This is not wrong. It is just hard to use. Troubleshooting is stateful. Some checks pass, some fail, some reveal new branches.

The user needs an interactive checklist, not another wall of suggestions.

### The OpenUI version

The assistant can turn the answer into a diagnostic flow:

```txt
root = Stack([title, status, checklist, branch, actions])
title = TextContent("OAuth callback diagnostic", "large-heavy")
status = Alert("Start with redirect URL and environment variables. These cause most production-only callback failures.", "info")
checklist = Checklist([redirectUrl, envVars, cookies, logs])
redirectUrl = CheckItem("Redirect URL matches provider dashboard exactly", false)
envVars = CheckItem("Production CLIENT_ID and CLIENT_SECRET are present", false)
cookies = CheckItem("Cookies use Secure and compatible SameSite settings", false)
logs = CheckItem("Callback route logs show provider response", false)
branch = Callout("If redirect URL passes but cookies fail, inspect proxy HTTPS headers before changing auth code.", "warning")
actions = Buttons([copyChecklist, showCurl, openDocs], "row")
copyChecklist = Button("Copy checklist", "secondary")
showCurl = Button("Show callback test command", "secondary")
openDocs = Button("Open OAuth docs", "primary")
```

Now the response supports the work. The user can mark progress, copy the checklist, reveal deeper diagnostics, or move to docs. The interface can also remember which checks have passed, so the next assistant turn starts from the current state instead of repeating the whole list.

This is the difference between "AI as a paragraph generator" and "AI as an operator inside a workflow."

## 4. Dashboards And Operational Summaries

Dashboards are probably the clearest example of text collapse.

A support lead asks:

> What changed in the support queue today?

The assistant can query the data and produce a decent summary:

```txt
Support volume is up 18% today. Billing tickets increased the most, rising
from 42 to 71. The highest-risk segment is enterprise accounts because SLA
breaches rose from 3 to 9. The team should move two agents from general
support to billing for the next four hours.
```

That is useful, but incomplete. A support lead needs to scan trend lines, inspect categories, see the recommended staffing shift, and maybe trigger an action.

### The plain-text problem

Operational work rarely ends at "good to know." The user usually needs to do something:

- reassign people,
- escalate accounts,
- open a filtered queue,
- download a report,
- compare against yesterday,
- or notify another team.

Plain text can recommend those actions, but it cannot become the control surface.

### The OpenUI version

The response can render as a compact operations panel:

```txt
root = Stack([title, kpis, chart, queueTable, recommendation, actions])
title = TextContent("Support queue today", "large-heavy")
kpis = Metrics([volume, billing, sla])
volume = Metric("Ticket volume", "+18%", "warning")
billing = Metric("Billing tickets", "71", "critical")
sla = Metric("SLA breaches", "9", "critical")
chart = LineChart("Tickets by hour", hours, today, yesterday)
hours = ["9am", "10am", "11am", "12pm", "1pm"]
today = [22, 31, 44, 58, 71]
yesterday = [18, 25, 36, 40, 42]
queueTable = Table([categoryCol, countCol, deltaCol, ownerCol])
categoryCol = Col("Category", ["Billing", "Login", "Integrations"])
countCol = Col("Open", [71, 34, 19], "number")
deltaCol = Col("Change", ["+69%", "+8%", "-12%"])
ownerCol = Col("Suggested owner", ["Billing pod", "General pod", "API pod"])
recommendation = Alert("Move two agents to billing for the next four hours.", "warning")
actions = Buttons([openBillingQueue, draftUpdate], "row")
openBillingQueue = Button("Open billing queue", "primary")
draftUpdate = Button("Draft Slack update", "secondary")
```

This is not just prettier. It preserves the shape of the work. The user gets metrics, trend context, a ranked table, and action buttons in one generated surface.

OpenUI's streaming-first design matters here. If a dashboard has to wait for a complete JSON blob before anything renders, the user sees a blank screen. OpenUI Lang is designed so structured UI can be parsed and rendered progressively as tokens arrive, which makes generated interfaces feel closer to live software than delayed reports.

## 5. Decision Memos And Approval Workflows

Decision support is where plain text can be actively risky.

Imagine a finance assistant summarizing a vendor renewal:

```txt
The renewal is $48,000 annually, which is 12% higher than last year. Usage
has increased by 27%, so the price increase may be justified. However, only
43% of seats are active monthly. I recommend approving if the vendor agrees
to remove inactive seats or provide a price lock for 24 months.
```

That summary is useful, but an approver needs more than a paragraph. They need the numbers, risks, conditions, audit trail, and approval action separated clearly.

### The plain-text problem

Approval workflows need structure because people are accountable for the decision. A paragraph mixes facts, assumptions, and recommendations. It can be hard to tell what is sourced, what is inferred, and what action is being requested.

### The OpenUI version

The same answer should become a decision panel:

```txt
root = Stack([title, summary, financials, riskList, conditions, approval])
title = TextContent("Vendor renewal review", "large-heavy")
summary = Alert("Recommendation: approve only if inactive seats are removed or a 24-month price lock is added.", "warning")
financials = Metrics([renewal, increase, usage, activeSeats])
renewal = Metric("Annual renewal", "$48,000", "neutral")
increase = Metric("YoY increase", "+12%", "warning")
usage = Metric("Usage change", "+27%", "positive")
activeSeats = Metric("Monthly active seats", "43%", "critical")
riskList = Checklist([seatWaste, lockIn, missingOwner])
seatWaste = CheckItem("Inactive seat waste remains unresolved", true)
lockIn = CheckItem("No price lock in current terms", true)
missingOwner = CheckItem("Business owner confirmed renewal need", false)
conditions = TextContent("Approval condition: remove inactive seats or add 24-month price lock.", "medium-heavy")
approval = Buttons([approve, requestChanges, reject], "row")
approve = Button("Approve with condition", "primary")
requestChanges = Button("Request vendor revision", "secondary")
reject = Button("Reject renewal", "danger")
```

The generated UI separates facts from risks and actions. It gives the approver a way to proceed without copying text into another system.

For many business workflows, this is the real value of generative UI. It is not about making chatbot answers look nicer. It is about moving from "the assistant described the work" to "the assistant produced the interface for doing the work."

## What OpenUI Adds Beyond A Pretty Renderer

It is tempting to look at these examples and think, "Couldn’t I just ask the model for JSON and render that?"

You can, and many teams do. But that approach has tradeoffs:

- JSON is verbose, which increases token usage.
- Partial JSON is hard to render while it is still streaming.
- Arbitrary JSON schemas tend to sprawl as product needs grow.
- The model may output shapes the app does not safely support.

OpenUI's approach is more constrained. The app defines component contracts, the prompt is generated from those contracts, and the model emits a compact UI description that the renderer can parse progressively. The OpenUI repository describes this as a full-stack generative UI framework with a compact streaming-first language, React runtime, built-in component libraries, prompt generation from your component library, and ready-to-use chat surfaces.

That stack matters because generated UI needs more than a model prompt. It needs an agreement between the model and the application:

- What components are allowed?
- What props are valid?
- What can stream before the full answer is finished?
- Which actions can the user take?
- How does the app validate and render the result?

Plain text avoids those questions by giving users paragraphs. Generative UI answers them by building a controlled interface layer between model reasoning and product interaction.

## When Plain Text Is Still The Right Answer

Not every AI response should become UI.

If the user asks for a definition, a short explanation, or a draft paragraph, text is perfect. If the assistant is brainstorming, writing, translating, or summarizing something lightweight, adding UI may slow the experience down.

The decision rule is simple:

Use text when the user only needs to read.

Use UI when the user needs to compare, choose, filter, inspect, validate, approve, or act.

The best AI products will not replace text with UI everywhere. They will choose the right output shape for the job.

## The Takeaway

Plain text is a good answer format. It is a bad interface format.

That distinction matters more as AI products move from chat demos into real workflows. The more complex the task, the more structure the user needs. Comparisons need tables and cards. Intake needs forms. Troubleshooting needs checklists. Operations need dashboards. Approvals need decision panels.

OpenUI gives developers a practical way to generate those surfaces without letting the model invent arbitrary frontend code. You define the component library, the model emits a compact streamable UI description, and the React renderer turns that output into an interface the user can actually work with.

The future of AI interfaces is not "less text" for its own sake. It is better matching the shape of the answer to the shape of the task.

Sometimes that shape is a paragraph.

Often, it is a UI.

## References

- [OpenUI GitHub repository](https://github.com/thesysdev/openui)
- [OpenUI documentation](https://www.openui.com/)
- [OpenUI playground](https://www.openui.com/playground)
