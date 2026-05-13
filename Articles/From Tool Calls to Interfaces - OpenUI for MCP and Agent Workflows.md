# From Tool Calls to Interfaces: OpenUI for MCP and Agent Workflows

Most agent demos still end the same way: a chat transcript, a list of tool calls, and a developer saying "the agent can now do real work."

That is enough for debugging. It is not enough for product UX.

As soon as an agent starts returning ranked tasks, search results, validation output, deployment checks, diffs, approval requests, or account setup steps, plain text becomes the wrong surface. The information is structured, stateful, and action-oriented. It wants UI.

This is where OpenUI becomes interesting. Instead of forcing every agent result back into markdown, OpenUI gives you a compact language and rendering model for turning structured agent state into interfaces that users can inspect, approve, reject, or modify.

This article looks at OpenUI from one specific angle:

> not as a chatbot replacement, but as the review layer for tool-driven agent workflows.

The example throughout is intentionally practical: an agent that scans a backlog, ranks candidate tasks, asks for approval on one action, and then continues with structured feedback from the user.

## The Real Problem in Agent UX

The weak point in many agent products is not model reasoning. It is handoff.

An agent can:

- call tools,
- read structured responses,
- choose a next action,
- and produce a decent explanation.

But the moment a human needs to review that state, the system often collapses back into paragraphs.

For example, imagine an agent that returns:

- 12 candidate tasks,
- confidence scores,
- blockers,
- required permissions,
- estimated risk,
- recommended next action.

That is not naturally conversational data. A user does not want to read it as prose and then manually reconstruct the state in their head. They want:

- sortable task cards,
- visible risk markers,
- an approval button,
- a defer button,
- a request-changes action,
- and a clean record of what happened next.

This is the interface problem in agent systems: tool outputs are already structured, but the final user surface is often not.

## What MCP and Tool Calls Already Give You

If you are building with MCP servers, internal tools, or function-calling agents, you are already halfway to UI.

A tool result usually contains fields like:

- lists,
- enums,
- booleans,
- links,
- timestamps,
- confidence scores,
- action labels,
- status values.

That is much closer to application state than to freeform chat.

Take a simple MCP-style result:

```ts
type CandidateTask = {
  id: string
  title: string
  source: "github" | "email" | "crm"
  confidence: number
  estimatedValue: number
  risk: "low" | "medium" | "high"
  blockers: string[]
  recommendedAction: "do_now" | "defer" | "ignore"
}

type RankTasksResult = {
  runId: string
  generatedAt: string
  tasks: CandidateTask[]
}
```

If you print this as text, the user gets a wall of output.

If you treat it as interface state, the user gets:

- cards,
- filters,
- sortable tables,
- status badges,
- action buttons.

The key idea is simple:

> tool output is not just data for the agent. It is also data for the interface.

## OpenUI as the Rendering Layer

OpenUI is built around a streaming-first model of UI generation. The point is not "have the model output HTML." The point is to generate structured interface descriptions that can be rendered, updated, and validated more safely than raw text.

From the OpenUI project itself:

- OpenUI Lang is designed for structured UI generation
- it is compact enough for model output
- it is designed to work well with streaming
- it is meant to sit between model state and rendered UI

That makes it a natural fit for agent workflows, because agents already spend their lives moving between structured states:

- query results,
- ranked options,
- verification outcomes,
- pending approvals,
- action payloads,
- final execution results.

Instead of asking the model to narrate all of that in markdown, you can map those states into OpenUI components.

Here is the important shift:

- the model does not invent random UI every turn
- you define the allowed surface area up front
- the model fills that surface with structured state

In practice, that means you can generate a prompt from a constrained component library and explicitly tell the model which tools exist.

```ts
import { generatePrompt } from "@openuidev/lang-core"

const systemPrompt = generatePrompt({
  name: "Task Review UI",
  components: [
    "Stack",
    "Card",
    "Table",
    "Button",
    "Badge",
    "Text",
  ],
  tools: [
    {
      name: "list_candidate_tasks",
      description: "Return candidate tasks with confidence and risk fields.",
    },
    {
      name: "submit_task",
      description: "Submit the approved task to the target platform.",
    },
  ],
  toolCalls: true,
  bindings: true,
  editMode: true,
  inlineMode: true,
  preamble:
    "Render reviewable task state. Prefer compact, inspectable UI over prose.",
})
```

The point of a prompt like this is not "make the model powerful." The point is to make the model legible.

## A Practical Flow: Tool Result to Review UI

Let's use a minimal review flow.

The agent calls a tool:

```ts
const result = await listCandidateTasks({
  inbox: "platform-opportunities",
  maxItems: 12,
})
```

The tool returns structured results. The agent then ranks them and emits a reviewable state:

```ts
type ReviewState = {
  phase: "researching" | "ready" | "approved" | "rejected"
  selectedTaskId?: string
  tasks: CandidateTask[]
  explanation?: string
}
```

Now you have two jobs:

1. keep this state understandable to the agent
2. turn it into a good human review surface

This is where a translation layer helps.

```ts
function toUiState(review: ReviewState) {
  return {
    phase: review.phase,
    cards: review.tasks.map((task) => ({
      id: task.id,
      title: task.title,
      meta: `${task.source} · $${task.estimatedValue}`,
      confidence: task.confidence,
      risk: task.risk,
      blockers: task.blockers,
      recommendedAction: task.recommendedAction,
      selected: review.selectedTaskId === task.id,
    })),
    explanation: review.explanation ?? "",
  }
}
```

The important part is not the exact shape. The important part is that you deliberately convert "agent state" into "UI state" instead of letting the model improvise presentation every time.

```mermaid
flowchart LR
  A["MCP Tool Call"] --> B["Structured Tool Result"]
  B --> C["Agent Reasoning"]
  C --> D["Review State Object"]
  D --> E["OpenUI Rendering Layer"]
  E --> F["Human Decision"]
  F --> G["Structured Action Payload"]
  G --> H["Validator"]
  H --> I["Next Tool Call or Submission"]
```

## Human Approval Should Be a First-Class Interaction

The biggest mistake in agent UX is treating human approval as a chat reply.

If the user must type:

> yes, do the second one, but not until after we verify the payout terms

you have already lost precision.

Approval should be explicit and structured.

A better model is:

- user selects a card,
- user clicks `Approve`,
- interface emits a payload,
- agent receives a typed event.

For example:

```ts
type ApprovalPayload = {
  type: "task_approval"
  taskId: string
  decision: "approve" | "reject" | "request_changes" | "defer"
  note?: string
}
```

This matters for three reasons:

### 1. The agent gets clean state back

You do not need to infer intent from language.

### 2. Auditability improves

You can record exactly what was approved, by whom, and when.

### 3. Unsafe actions become easier to gate

You can validate the payload before the agent executes anything.

That is especially important in MCP-style environments where the next step may involve:

- sending email,
- posting to a platform,
- running a command,
- updating a record,
- paying money,
- or exposing credentials.

## Streaming Matters More Than People Think

One underrated benefit of OpenUI in agent workflows is that agent state is often incremental.

A realistic run is not:

1. think
2. finish
3. display final answer

It is more like:

1. researching
2. validating
3. blocked on one dependency
4. narrowed to two candidates
5. ready for approval
6. approved
7. submitted

That means the interface should be able to reflect state transitions without feeling like a page reload every time.

A simple state progression might look like this:

```ts
const timeline = [
  { phase: "researching", message: "Scanning platform opportunities..." },
  { phase: "researching", message: "Filtering low-quality and stale tasks..." },
  { phase: "ready", message: "One task is ready for approval." },
  { phase: "approved", message: "Submitting the task proposal now." },
]
```

This does two things for the user:

- it makes the agent feel legible,
- and it reduces anxiety around long-running tool chains.

Users tolerate latency much better when they can see meaningful state transitions.

## Interface Contracts Are More Important Than Pretty Components

Once you put an agent behind an interface, you need to stop thinking only about rendering and start thinking about contracts.

Three contracts matter:

### 1. Tool result schema

What does the tool actually return?

### 2. UI translation schema

What shape does the renderer expect?

### 3. Action payload schema

What does the interface send back when the user clicks something?

If any of these are vague, your UI gets brittle.

A simple validation pass helps a lot:

```ts
function validateApprovalPayload(payload: ApprovalPayload) {
  const validDecisions = [
    "approve",
    "reject",
    "request_changes",
    "defer",
  ]

  if (!payload.taskId) throw new Error("Missing taskId")
  if (!validDecisions.includes(payload.decision)) {
    throw new Error(`Invalid decision: ${payload.decision}`)
  }
}
```

This is not glamorous, but it is the difference between:

- an interface that looks smart,
- and one that can safely drive real workflows.

## A Better Mental Model: The Agent Is Not the UI

One reason teams struggle with agent products is that they collapse too many roles together.

The agent should not be:

- the planner,
- the execution engine,
- the validator,
- the renderer,
- and the approval system

all at once.

A healthier split is:

- **tools** provide structured facts and actions
- **the agent** reasons over those facts
- **OpenUI** renders the review surface
- **the human** provides explicit decisions
- **validators** gate unsafe transitions

This separation makes systems easier to debug and easier to trust.

It also makes iteration easier. You can improve the review UI without rewriting the agent, or tighten the validator without redesigning the interface.

## Where OpenUI Fits Best

OpenUI is especially strong when the output is:

- structured,
- multi-step,
- inspectable,
- and action-oriented.

Examples:

- task triage
- deployment review
- account setup checklists
- incident response playbooks
- procurement approvals
- CRM lead qualification
- research review queues

In all of these, the user is not asking for pure conversation. They are asking for:

- understanding,
- trust,
- control,
- and a fast path to action.

That is exactly where a generative UI layer can beat plain text.

## Where Plain Chat Still Wins

Not every agent output needs UI.

Plain text is still better when:

- the answer is short,
- the action is low-risk,
- the user is exploring,
- or there is no meaningful state to inspect.

If the output is:

- "here is the command"
- "here is the explanation"
- "here is the answer"

then a full UI layer may be unnecessary overhead.

OpenUI becomes valuable when the state itself deserves interaction.

That is the right test:

> if the user needs to inspect, compare, sort, approve, reject, or edit the result, the output probably wants UI.

## A Minimal Architecture You Can Actually Build

If you wanted to implement this pattern in a small agent system, the architecture could stay simple:

```text
Tool calls
  -> structured results
  -> agent reasoning
  -> review-state object
  -> OpenUI rendering layer
  -> explicit user action payload
  -> validator
  -> next agent/tool step
```

You do not need to solve the whole "autonomous company" story.

You just need:

- one structured tool result,
- one review state,
- one approval payload,
- one validator,
- and one visible state machine.

That is enough to make an agent product feel much more real.

## Final Takeaway

MCP servers and tool-calling agents already generate the raw material for good interfaces. The missing piece is usually not more model intelligence. It is a better surface for human review.

OpenUI is useful here because it treats interface generation as structured state, not as glorified markdown.

That makes it a good fit for the part of agent workflows that most teams still underspecify:

- review,
- approval,
- action,
- and visible progress.

If you are building agents that do more than answer questions, this is the shift worth making:

stop asking your interface to summarize the workflow after the fact.

Let the workflow become the interface.
