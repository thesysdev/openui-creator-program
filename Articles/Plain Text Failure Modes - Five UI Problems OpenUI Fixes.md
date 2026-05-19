# Plain Text Failure Modes: Five UI Problems OpenUI Fixes

Plain text is a good answer format until the answer becomes something the user needs to inspect, compare, change, or act on.

That is where many AI products still feel strange. The model can understand a messy request and retrieve useful data, but then it squeezes the result back into paragraphs. The intelligence is there; the interface is not.

OpenUI is useful because it lets the model return a small UI program instead of a wall of prose. The app still controls the component library. The model composes approved components with valid props.

Here are five places where plain text usually breaks down, and the OpenUI pattern that fits each one.

The goal is not to replace every sentence with a widget. Text is still the right format for explanation, narrative, and reasoning. The problem starts when text has to pretend to be an interface.

## 1. Dense Data Becomes A Reading Test

Plain text is bad at dense tabular data.

Ask a support assistant for the last five failed invoices and you might get this:

```text
Here are the recent failures:
1. Acme Co, INV-1031, $428, failed because card expired.
2. Northwind, INV-1032, $91, failed because insufficient funds.
3. Hightower, INV-1033, $1,240, failed because bank declined.
```

That is technically readable, but the user has to scan line endings, compare amounts mentally, and keep identifiers in short-term memory. The text has thrown away column structure.

OpenUI's default library treats tables as column-oriented:

```txt
root = Stack([title, failures])
title = TextContent("Recent invoice failures", "large-heavy")
failures = Table([
  Col("Customer", customers),
  Col("Invoice", invoices),
  Col("Amount", amounts, "currency"),
  Col("Reason", reasons)
])
customers = ["Acme Co", "Northwind", "Hightower"]
invoices = ["INV-1031", "INV-1032", "INV-1033"]
amounts = [428, 91, 1240]
reasons = ["Card expired", "Insufficient funds", "Bank declined"]
```

The same information becomes a shape the user already knows how to scan. Column names do work that bullet punctuation cannot.

The important design point is not "tables are prettier." It is that tables preserve the relationships in the data. A generated UI should keep structure when structure is the point.

This also matters on small screens. Plain text tables degrade into awkward wrapping, while a real table component can choose a mobile layout, pin important columns, or hide secondary fields behind row details. The model should not have to solve responsive layout in prose.

## 2. Comparisons Collapse Into Paragraphs

Plain text comparisons are usually written as advice, not as a decision surface.

```text
Plan A is cheaper and includes basic support. Plan B costs more but adds SSO,
audit logs, and a higher usage limit. Plan C is the most expensive and is best
for larger teams that need dedicated support.
```

That might be acceptable in an email. It is weak inside an app where the user needs to choose.

A comparison wants aligned attributes:

```txt
root = Stack([heading, table])
heading = TextContent("Plan comparison", "large-heavy")
table = Table([
  Col("Plan", plans),
  Col("Monthly price", prices),
  Col("SSO", sso),
  Col("Audit logs", audit),
  Col("Best for", fit)
])
plans = ["Starter", "Team", "Enterprise"]
prices = ["$29", "$99", "Custom"]
sso = ["No", "Yes", "Yes"]
audit = ["No", "Yes", "Yes"]
fit = ["Small projects", "Growing teams", "Regulated orgs"]
```

The UI version lets the user compare across a row and down a column. The text version forces the user to reconstruct a matrix from sentences.

This is one of the cleanest rules for generative UI: if the answer contains a hidden table, render the table.

The same rule applies to product cards, candidate lists, vendor choices, and ranked recommendations. If the user has to choose between options, keep the shared attributes aligned.

## 3. Status Needs Severity, Not More Words

Operational status is another place where text buries the signal.

```text
The deploy is mostly okay. The build passed, staging is healthy, but the API
latency check is above threshold and the payment worker has a retry backlog.
You may want to investigate before promoting.
```

The user needs severity and next action, not a paragraph to interpret.

OpenUI's default components include `Card`, `CardHeader`, `TextContent`, `Callout`, `Tag`, and layout primitives such as `Stack`. That gives the model enough vocabulary to preserve state:

```txt
root = Stack([header, checks, warning])
header = CardHeader("Release readiness", "Promote build 8f31c2?")
checks = Stack([build, api, worker], "row", true)
build = Card([TextContent("Build", "small"), Tag("healthy", null, "sm", "success")])
api = Card([TextContent("API latency", "small"), Tag("warning", null, "sm", "warning")])
worker = Card([TextContent("Payment worker", "small"), Tag("backlog", null, "sm", "danger")])
warning = Callout("warning", "Hold promotion", "Latency and worker backlog need review.")
```

Now the shape matches the job. Cards group checks. Tags expose severity. The callout says what changed the decision.

A paragraph can describe status. A UI can make status visible.

This is especially useful for agent workflows. Agents often produce intermediate state: waiting, blocked, retrying, succeeded, failed, needs approval. A chat transcript can record those states, but it does not make the current state obvious. Status UI does.

## 4. Forms Should Validate, Not Interview

Plain text turns structured input into a slow interview.

```text
Please reply with your name, work email, company size, country, and a short
description of what you want to build.
```

Users answer in inconsistent formats. The assistant asks follow-up questions. Validation happens late. Required fields get missed.

OpenUI can render the form directly:

```txt
root = Stack([title, form])
title = TextContent("Request access", "large-heavy")
form = Form("access", buttons, [nameField, emailField, sizeField, notesField])
nameField = FormControl("Name", Input("name", "Your name", "text", { required: true }))
emailField = FormControl("Work email", Input("email", "you@company.com", "email", { required: true, email: true }))
sizeField = FormControl("Company size", Select("companySize", sizeOptions, "Choose one", { required: true }))
notesField = FormControl("Use case", TextArea("useCase", "What are you building?", 4, { minLength: 20 }))
sizeOptions = [SelectItem("small", "1-10"), SelectItem("mid", "11-100"), SelectItem("large", "101+")]
buttons = Buttons([Button("Submit", Action([@ToAssistant("Submit access request")]), "primary")])
```

The model still decides that a form is the right response. The app still owns the available components and validation behavior.

The OpenUI prompt rules also make a production detail explicit: define each `FormControl` as its own reference so fields can stream progressively, and always provide explicit buttons. Those rules matter because forms are not just display. They are stateful UI.

Plain text asks the user to serialize data manually. A form lets the interface collect data in the format the app needs.

There is also a trust benefit. When the user sees a form, they can tell what will be submitted. When the assistant asks for five fields in a sentence, it is less clear which answer maps to which internal field, whether validation exists, or what will happen after submission.

## 5. Actions Need Boundaries

A text answer often ends with a vague instruction:

```text
You should probably pause the campaign, notify the owner, and review the last
three failed events.
```

That sounds helpful, but it leaves the user to find the right screens and perform the work.

A generated interface can put safe actions next to the evidence:

```txt
root = Card([title, summary, buttons])
title = CardHeader("Campaign anomaly detected")
summary = TextContent("Spend rose 42% while conversions dropped 18% in the last hour.")
buttons = Buttons([
  Button("Pause campaign", Action([@ToAssistant("Pause campaign after confirmation")]), "primary"),
  Button("Notify owner", Action([@ToAssistant("Draft owner notification")]), "secondary"),
  Button("Show failed events", Action([@ToAssistant("Show failed events")]), "secondary")
])
```

This is not the same as letting the model perform arbitrary side effects. The generated UI exposes approved actions. The host app receives action events and decides what to do next.

That boundary is the difference between useful agent UI and unsafe automation. The model can suggest the next button. Application code owns permission, confirmation, and execution.

This is where generative UI should be conservative. A button can be generated, but the authority to run the action belongs to the host app. OpenUI gives the assistant an interface vocabulary; it does not remove the need for product permissions, audit logs, confirmations, or backend validation.

## What OpenUI Is Actually Changing

These examples can sound like normal frontend work because they are normal frontend work. That is the point.

OpenUI does not ask the model to invent raw React. It asks the model to write in a constrained language backed by components the app has already approved. The model output becomes more useful because it can choose structure:

```txt
root = Stack([summary, table, actions])
```

instead of only words:

```text
Here is a summary, followed by a table, followed by some actions...
```

The first form can be parsed and rendered. The second form leaves the user and app to do the parsing.

That is the practical value: OpenUI moves structure from the reader's head into the interface.

## A Developer Rubric

When deciding whether an AI answer should stay as text or become generated UI, ask what job the user is trying to do next.

Keep it as text when:

- the user asked for an explanation
- there is no obvious action to take
- the answer is short enough to read in one pass
- structure would add friction instead of removing it

Render UI when:

- the answer contains rows, columns, or repeated items
- the user needs to compare options
- the result has severity, progress, or status
- the app needs validated input
- the answer should lead to a guarded action

This rubric keeps generated UI from becoming decorative. If the interface shape helps the next user action, render it. If it only makes the response look busier, keep the text.

## The Pattern

The five examples are different, but the failure is the same each time:

- tables lose columns
- comparisons lose alignment
- status loses severity
- forms lose validation
- actions lose boundaries

Plain text flattens the answer. OpenUI gives the model a way to preserve the shape of the task.

The rule of thumb is practical:

Use text when the answer is meant to be read.

Use generated UI when the answer is meant to be scanned, compared, edited, validated, or acted on.

That is the real upgrade: letting an AI response keep the interface shape that the user already needs.
