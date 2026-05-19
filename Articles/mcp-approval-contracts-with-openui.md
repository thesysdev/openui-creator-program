<!-- markdownlint-disable MD013 -->

# MCP Approval Contracts with OpenUI: Turning Tool Results into Reviewable Interfaces

Agent applications usually become risky at the same point they become useful. A model can search, rank, summarize, call tools, update records, open pull requests, or prepare payments. The intermediate state is structured, but many products still render it as a paragraph in a chat window:

> I found three candidate actions. The first one looks best. Do you want me to continue?

That is not enough surface area for a real user decision. The user needs to inspect evidence, compare options, understand risk, approve a specific action, and know exactly what payload will go back into the agent loop.

OpenUI fits this problem because MCP and tool-based agents already produce data that looks like interface state: arrays of candidates, typed statuses, confidence scores, links, logs, error codes, and action parameters. Instead of asking the model to flatten that into prose, the application can expose a narrow component vocabulary and let the agent compose a review surface around the tool result.

This article walks through a practical pattern: treat human approval as a contract between the tool output, the generated UI, and the next agent action.

## The problem with chat-only approvals

Plain text approvals fail in three ways.

First, they hide structure. A tool might return five candidates with different scores, evidence links, costs, and failure modes. A paragraph can mention the top candidate, but it makes comparison slow and lossy.

Second, they blur the approval target. If the user says "yes," what exactly did they approve? A repository change? A deployment? A purchase? A message to a customer? Good agent systems need the approval payload to be explicit.

Third, they make state transitions hard to audit. Many agent workflows move through states like `researching`, `ready_for_review`, `approved`, `running`, `blocked`, and `complete`. Chat transcripts are a weak substitute for a visible state model.

A better approval interface should answer four questions at a glance:

1. What did the agent find?
2. Why is this action recommended?
3. What are the risks and limits?
4. What exact structured action will be sent if the user approves?

## Start with the tool result schema

Consider an MCP tool that audits open support tasks and returns candidate fixes:

```ts
type CandidateAction = {
  id: string
  title: string
  account: string
  evidence: Array<{ label: string; url: string }>
  expectedImpact: "low" | "medium" | "high"
  risk: "low" | "medium" | "high"
  estimatedCostUsd: number
  action: {
    toolName: "create_refund" | "send_followup" | "open_ticket"
    arguments: Record<string, unknown>
  }
}

type ReviewState = {
  workflowId: string
  status: "ready_for_review"
  candidates: CandidateAction[]
  policyLimits: {
    maxRefundUsd: number
    requireManualApprovalAboveUsd: number
  }
}
```

This is already more than a message. It is a review queue. The product should not ask the model to describe the queue; it should render the queue.

The useful OpenUI layer is not an unconstrained design surface. It is a small set of product-level components:

- `ReviewQueue` for the list of candidates
- `EvidenceList` for links and source snippets
- `RiskBadge` for policy and operational risk
- `ActionPayloadPreview` for the exact tool call
- `ApprovalRail` for approve, reject, or request changes
- `StateTimeline` for the workflow state

The model can choose layout and emphasis, but the application still owns the allowed components, props, action handlers, and policy checks.

## Map state to interface, not prose

A generated review screen might be described conceptually like this:

```tsx
<ReviewQueue workflowId="wf_482" status="ready_for_review">
  <CandidateCard
    id="cand_1"
    title="Refund duplicate charge for Acme"
    account="Acme Inc."
    expectedImpact="high"
    risk="low"
  >
    <EvidenceList
      items={[
        { label: "Stripe duplicate payment", url: "https://example.com/payments/123" },
        { label: "Support ticket #1842", url: "https://example.com/tickets/1842" }
      ]}
    />
    <ActionPayloadPreview
      toolName="create_refund"
      arguments={{ paymentId: "pay_123", amountUsd: 48 }}
    />
    <ApprovalRail actions={["approve", "reject", "request_changes"]} />
  </CandidateCard>
</ReviewQueue>
```

The important part is not the syntax. The important part is that the UI keeps the approval target concrete. If the user approves `cand_1`, the system can send back a typed payload such as:

```json
{
  "workflowId": "wf_482",
  "decision": "approve",
  "candidateId": "cand_1",
  "approvedAction": {
    "toolName": "create_refund",
    "arguments": {
      "paymentId": "pay_123",
      "amountUsd": 48
    }
  }
}
```

That payload is not inferred from a vague "yes." It is produced by a specific UI control bound to a specific candidate.

## Keep policy outside the model

OpenUI can render the approval surface, but approval authority should not live inside the model. The application still needs deterministic checks before any action runs.

For example:

```ts
function validateApproval(state: ReviewState, decision: ApprovalDecision) {
  const candidate = state.candidates.find((item) => item.id === decision.candidateId)
  if (!candidate) return { ok: false, reason: "unknown_candidate" }

  if (candidate.action.toolName === "create_refund") {
    const amount = Number(candidate.action.arguments.amountUsd)
    if (amount > state.policyLimits.maxRefundUsd) {
      return { ok: false, reason: "refund_limit_exceeded" }
    }
  }

  if (candidate.risk === "high") {
    return { ok: false, reason: "high_risk_requires_manual_escalation" }
  }

  return { ok: true }
}
```

This separation matters. The model can help organize evidence and produce a clear review interface. The server decides whether the approved payload is valid, authorized, and inside policy.

That design also makes the UI easier to trust. A disabled approval button with a visible reason is better than a hidden model decision. The user sees the same boundary the server enforces.

## Add a state timeline

Agent workflows are rarely single-step. The interface should show where the user is in the loop:

1. Tool result received
2. Candidates ranked
3. Human review requested
4. Decision captured
5. Server validation passed
6. Action executed or blocked

A `StateTimeline` component is simple, but it prevents confusion. If an action is blocked, the user can see whether the block came from missing evidence, policy validation, tool failure, or a human rejection.

For MCP workflows, this timeline can be generated directly from the same state machine that drives the agent. The model does not need to invent status labels. It receives a constrained set of states and renders them in a way a user can inspect.

## Make evidence first-class

Approval UI should not only show the recommended action. It should show the evidence that made the action reasonable.

A practical pattern is to separate evidence into three levels:

- **Summary:** one sentence explaining why the candidate is present
- **Source links:** the public or internal records used to justify it
- **Raw payload preview:** the relevant fields returned by the tool

That lets a user move quickly without losing auditability. They can approve a low-risk task from the summary, or expand the raw payload when the action is expensive, irreversible, or customer-facing.

## Where OpenUI helps most

This pattern is useful when an agent returns structured intermediate state and the next step needs human judgment. Good examples include:

- approving a customer refund or credit
- selecting one of several generated pull request fixes
- reviewing search results before outbound communication
- confirming an infrastructure change plan
- choosing which task an autonomous worker should execute next
- inspecting a compliance or safety warning before continuing

In each case, plain text creates ambiguity. A generated interface preserves the shape of the decision.

## What developers still own

OpenUI does not remove the need for product engineering. The developer still owns:

- the component allowlist
- prop schemas and validation
- server-side authorization
- action replay protection
- audit logging
- fallback rendering
- accessibility and keyboard behavior
- policy checks before tool execution

That is a feature, not a limitation. Generative UI is safest when the model composes within a bounded interface vocabulary and every user action resolves to a typed payload the server can validate.

## The practical contract

The contract for MCP approval interfaces can be summarized like this:

1. Tools return structured state.
2. OpenUI renders that state as a reviewable interface.
3. The user acts on a specific candidate or control.
4. The UI emits a typed decision payload.
5. The server validates policy and authorization.
6. The agent continues with the validated result.

That contract turns a vague chat approval into an inspectable workflow. The user is not approving a paragraph. They are approving a concrete tool action with visible evidence, risk, and limits.

For agent products, that is the difference between a clever demo and a system people can safely use in production.
