<!-- markdownlint-disable MD013 -->

# UI-Based Chatbots vs. Text-Based Chatbots: A Performance Comparison Across Completion, Time, and Satisfaction

Most chatbot evaluations stop too early. They ask whether the model answered correctly, then treat the interface as a delivery detail. That is fine for a Q&A assistant, but it is not enough for workflows where the user has to compare options, choose constraints, fill data, confirm side effects, or recover from a mistake.

For those tasks, the important question is not "did the assistant produce a good answer?" It is "did the user finish the job faster, with fewer wrong turns, and with enough confidence to trust the result?"

That is where text-only chatbots and UI-based chatbots start to separate. A text-only chatbot can explain the next step. A UI-based chatbot can render the next step as an interface: a table to compare, a form to edit, a chart to inspect, a button to confirm, or a progress state to review. The model is still useful, but the user no longer has to keep the entire workflow in short-term memory.

This article compares the two patterns across three product metrics that teams already understand:

- Task completion rate
- Time-on-task
- User satisfaction

The short version: text is strong when the task is exploratory, ambiguous, or low-stakes. UI-based chat becomes stronger as soon as the task has structure, state, or consequences.

## Define the interface, not just the model

A text-based chatbot returns messages. The user reads, interprets, asks follow-up questions, and manually transfers information into the next action. The interface is simple, but the user pays the coordination cost.

A UI-based chatbot still uses natural language, but it can answer with structured components. In the Thesys documentation, Generative UI is described as an application pattern where the interface is created dynamically from user intent, context, and data instead of being fully hand-coded ahead of time. The same docs describe a Generative UI API as a layer that returns a typed UI specification rather than plain text or fragile JSON, so the frontend can render valid interactive components at runtime: charts, forms, tables, cards, layouts, and actions.

OpenUI approaches this as an open framework for generative UI. Its repository is organized around a parser and renderer, headless chat state, prebuilt UI packages, examples, docs, and token-efficiency benchmarks. That matters because the product question is not whether a chatbot can say "here are your options." The question is whether the system can turn those options into a usable interface without every team hand-writing a new adapter for every response shape.

The comparison should therefore be made at the workflow level.

## Metric 1: Task completion rate

Task completion rate asks whether users finish the task. In usability studies, this is usually measured as pass/fail or partial completion. Nielsen Norman Group's accessibility usability report, for example, reports success rate, time on task, error count, and subjective rating as separate measures because a design can help on one dimension while hurting another.

That separation is important for chatbots. Text-only chat can look successful in a transcript while still failing the user's actual task.

Consider a support workflow:

1. The user asks why a payment failed.
2. The bot explains three possible causes.
3. The user asks which one applies.
4. The bot asks for more details.
5. The user pastes a transaction ID.
6. The bot explains a retry path.
7. The user has to leave the chat and find the retry control.

The answer may be accurate, but the task is unfinished until the retry is complete. A UI-based chatbot can instead render:

- A transaction summary card
- A status timeline
- A list of detected failure reasons
- A retry form with editable fields
- A confirmation action with the exact side effect shown before execution

That interface does not make the model smarter. It removes unnecessary translation steps between answer and action.

The completion advantage shows up most clearly when the task includes selection, validation, or confirmation. Text forces the user to infer the available actions. UI exposes them. This maps directly to the classic usability heuristic "recognition rather than recall": make options visible so users do not have to remember information across steps. In a text-only flow, the user often has to recall the bot's prior explanation, the valid choices, and the current state. In a UI-based flow, the relevant state can remain visible.

That does not mean UI always wins. If the user asks, "what does this error mean?" text may be enough. If the user asks, "help me fix it safely," an interface can carry more of the task.

Practical completion-rate benchmark:

```text
Task: Resolve a failed invoice payment.

Completion criteria:
- User identifies the failed invoice.
- User selects a valid retry method.
- User confirms the action with the correct amount and recipient.
- System records the retry request.

Compare:
- Text chatbot: answer-only chat, links allowed.
- UI chatbot: chat plus generated cards, form fields, validation, and final confirmation.

Measure:
- Full completion
- Partial completion
- Wrong retry target
- Abandoned task
```

Do not score "the bot gave the right instructions" as completion. Score the user's finished workflow.

## Metric 2: Time-on-task

Time-on-task measures how long users need to complete the job. It is tempting to assume text is faster because chat has a low-friction input. That is true for the first turn. It is often false for the whole workflow.

Text-only interfaces create hidden time costs:

- Reading and re-reading long answers
- Asking clarification questions
- Copying values into another UI
- Scrolling to recover earlier context
- Waiting for the bot to restate options
- Correcting errors caused by ambiguous instructions

A UI-based chatbot can reduce that time by making the next interaction concrete. Tables help comparison. Forms prevent malformed input. Buttons make valid actions obvious. Charts let users inspect distributions without asking the model to narrate every pattern.

The empirical evidence is mixed but useful. A Computers in Human Behavior study comparing chatbot and menu-based interfaces found that chatbot systems were associated with lower perceived autonomy and higher cognitive load than menu-based systems, which contributed to lower satisfaction. That result should not be read as "menus beat bots." It should be read as "conversation alone can make users feel less in control when the task requires structure."

Generative UI is interesting because it does not force a choice between conversation and structure. The user can ask naturally, and the system can answer with an interface that exposes the available state.

For time-on-task, the right benchmark is not first response latency. It is end-to-end task time.

Bad benchmark:

```text
How fast did the assistant answer?
```

Better benchmark:

```text
How long from the first user request to a correct submitted action?
```

Best benchmark:

```text
How long from the first user request to a correct submitted action, excluding abandoned users from average-time calculations but counting them in completion rate?
```

That last distinction matters. If five users abandon a text-only flow after six minutes, and the remaining five finish in two minutes, the average completion time of "successful users" hides the failure. Report completion rate and time together.

A useful time-on-task study design:

```text
Task: Choose the best support escalation plan for a customer account.

Text chatbot condition:
- Bot summarizes plans in prose.
- User asks follow-up questions.
- User types the selected plan.

UI chatbot condition:
- Bot renders a comparison table.
- User filters by SLA, price, and region.
- User selects a plan from the table.

Measure:
- Time to first plausible decision
- Time to final confirmed decision
- Number of clarification turns
- Number of times the user revisits earlier information
```

The important signal is not whether the UI is prettier. It is whether the UI turns reading time into decision time.

## Metric 3: User satisfaction

Satisfaction is not just "did the user like the bot?" It reflects confidence, perceived control, and the effort required to get through the task.

This is where text-only chatbots can disappoint even when they are technically correct. Long answers can feel helpful at first, then become work. Users must parse the response, decide which part applies, and remember what to do next. The interface gives them little feedback about whether they are on the right path.

UI-based chat can improve satisfaction by making the system's interpretation visible. If the bot says, "I found three invoices that match," the user has to trust the sentence. If the bot renders the three invoices with dates, amounts, status, and actions, the user can inspect the interpretation before acting.

That inspection step matters for trust. Users are more comfortable when they can see:

- What the system understood
- Which records or options it used
- What can be edited
- What action will happen next
- Whether the action is reversible

The Thesys docs describe frontend actions as part of the generative UI pattern: forms and inputs capture data, chained actions trigger API calls and update UI, and custom actions bind buttons to application-specific functions. That is the layer where satisfaction improves or collapses. A generated UI that exposes safe actions can make users feel in control. A generated UI that hides side effects behind vague buttons can be worse than text.

So the satisfaction comparison should include confidence questions:

```text
After completing the task, ask:
- I understood what the assistant was doing.
- I could tell which data the assistant used.
- I felt confident before confirming the final action.
- I could recover if the assistant misunderstood me.
- I would use this flow again for the same task.
```

Pair those ratings with observed behavior. If users say they are satisfied but repeatedly ask "are you sure?" before confirming, the interface is still leaking confidence.

## Where text-only chat still wins

Text-only chat is not obsolete. It remains the better default for:

- Open-ended exploration
- Brainstorming
- Explanations
- Drafting
- Low-stakes information lookup
- Tasks where the output is itself text

If the user asks, "summarize this policy," a generated form may add friction. If the user asks, "help me decide which policy exception applies, collect the required fields, and submit a request," text alone becomes a poor task surface.

The boundary is structure. When the task produces or consumes structured state, the interface should show structure.

## Where UI-based chat usually wins

UI-based chat becomes more compelling when at least one of these is true:

- The user must compare multiple options.
- The answer contains tabular or numeric data.
- The user must provide validated input.
- The task has multiple steps.
- The action has side effects.
- The user needs to inspect system state.
- The task may require approval or audit.

In those cases, plain text increases cognitive load because it serializes a multidimensional task into a paragraph. A UI can preserve the shape of the task.

For example:

```text
Text answer:
"Your usage is highest in eu-west-1, mostly from batch jobs, and you can reduce cost by moving two scheduled jobs, lowering retention, or changing the instance class."
```

That may be correct, but it is not yet a decision surface.

UI answer:

```text
Region cost table
Top jobs by spend
Retention slider
Instance-class comparison
Projected savings card
Approve changes button
Rollback notes
```

Now the user can compare, adjust, and confirm. The model provides reasoning; the UI provides control.

## A practical scorecard

Use this scorecard when deciding whether a chatbot response should stay as text or become UI.

| Workflow trait | Text-only chat | UI-based chat |
| --- | --- | --- |
| Open-ended explanation | Strong | Sometimes unnecessary |
| Compare many options | Weak | Strong |
| Fill or validate fields | Weak | Strong |
| Confirm side effects | Risky | Strong if confirmation is explicit |
| Inspect records | Weak | Strong |
| Recover from mistakes | Depends on conversation memory | Strong if state and undo paths are visible |
| Measure completion | Harder because action may happen elsewhere | Easier if action is in the generated UI |

Do not convert every answer into a component. Convert the parts of the answer where users need to act.

## How OpenUI fits

OpenUI is useful in this comparison because it treats generated UI as a runtime contract, not a screenshot. A model response can become a component tree that the frontend renders and the user can interact with. The project includes packages for parsing and rendering OpenUI language, headless chat behavior, UI libraries, and working examples.

That architecture gives product teams a way to test the performance question directly:

1. Pick a workflow where text-only chat currently creates back-and-forth.
2. Define the completion criteria and side effects.
3. Build the text-only baseline.
4. Build the UI-based variant with the same model and data access.
5. Measure completion, time-on-task, clarification turns, errors, and confidence.

If the UI version does not improve those numbers, keep the text version. Generative UI should earn its place like any other interface pattern.

## The real comparison

The debate is not "chatbots vs. buttons." Users need both language and interface. Language is good for expressing intent. Interface is good for exposing state, constraints, and action.

Text-only chatbots make the user translate from conversation to workflow. UI-based chatbots let the system do more of that translation. The performance difference appears when you measure the whole task instead of the model's first answer.

For simple answers, text is enough. For workflows with structure, state, and consequences, UI is not decoration. It is how users finish the job.

## References

- Nguyen, Q. N., Sidorova, A., & Torres, R. (2021). [User interactions with chatbot interfaces vs. menu-based interfaces: An empirical study](https://www.sciencedirect.com/science/article/abs/pii/S0747563221004167). Computers in Human Behavior.
- Nielsen Norman Group. [Recognition Rather Than Recall](https://www.nngroup.com/articles/recognition-and-recall/).
- Nielsen Norman Group. [Usability Guidelines for Accessible Web Design](https://media.nngroup.com/media/reports/free/Usability_Guidelines_for_Accessible_Web_Design.pdf).
- Thesys Documentation. [Generative UI glossary](https://docs.thesys.dev/guides/concepts).
- Thesys Documentation. [C1 Quickstart](https://docs.thesys.dev/guides/setup).
- OpenUI. [The open standard for Generative UI](https://github.com/thesysdev/openui).
