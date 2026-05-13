# Testing Generative UI: Assertions, Snapshots, and Semantic Validation

Generative UI has a testing problem.

Not a theoretical one. A production one.

When a normal React component breaks, the failure modes are familiar:

- a prop is missing,
- a branch renders the wrong element,
- a click handler fires the wrong action,
- a snapshot changes unexpectedly.

When a generative UI system breaks, those same failures still happen, but they now sit on top of model behavior that is partly non-deterministic and partly schema-driven.

That changes what "good test coverage" means.

If you treat OpenUI output like normal static JSX, your tests will either:

- be too brittle to survive harmless variation, or
- be too weak to catch the failures that actually matter.

This article is a practical playbook for testing generative UI systems, with OpenUI as the concrete example. The focus is not on vague eval theory. It is on how to stop bad generated interfaces from shipping.

## The First Mistake: Exact-Match Thinking

The easiest trap is to write tests as if model output were static source code.

For example:

```ts
expect(generatedUi).toEqual(expectedUi)
```

That looks clean, but it assumes the whole UI tree is deterministic at the text level.

In generative systems, that is rarely what you actually care about.

You usually care about things like:

- did the model produce a valid component tree?
- did it choose the right kind of interface?
- are the required actions present?
- are dangerous actions hidden when they should be?
- does the generated state still satisfy the user intent?

Those are not exact-match questions.

They are structural and semantic questions.

## Four Layers of Useful Testing

For OpenUI-style systems, a better mental model is four layers:

1. **Structural validation**  
   Is the generated UI syntactically and structurally valid?

2. **Semantic validation**  
   Does the UI do the right thing for the given intent?

3. **Tolerance-aware regression**  
   Did the generated interface drift in a way that matters?

4. **End-to-end interaction validation**  
   Do actions from the interface still produce safe, correct payloads?

If you only do one of these, you will miss failures.

## Layer 1: Structural Validation

Structural checks are the cheapest and highest-signal first line of defense.

They answer questions like:

- does the output parse?
- does it produce a valid component tree?
- are required props present?
- are forbidden components missing?

For example, imagine your app expects a review surface built from a constrained component set:

```ts
const allowedComponents = [
  "Stack",
  "Card",
  "Table",
  "Button",
  "Badge",
  "Text",
]
```

A basic validator can reject malformed or unsafe output before it ever reaches users:

```ts
function validateGeneratedTree(node: any): string[] {
  const errors: string[] = []

  if (!node || typeof node !== "object") {
    errors.push("Root node is missing or invalid")
    return errors
  }

  if (!allowedComponents.includes(node.type)) {
    errors.push(`Disallowed component: ${node.type}`)
  }

  if (node.type === "Button" && !node.props?.action) {
    errors.push("Button missing required action")
  }

  if (Array.isArray(node.children)) {
    for (const child of node.children) {
      errors.push(...validateGeneratedTree(child))
    }
  }

  return errors
}
```

This is not glamorous work. It is still one of the most valuable things you can ship.

Structural validators catch a huge class of failures:

- invalid trees,
- partial props,
- wrong component names,
- missing action bindings,
- unsupported UI shapes.

If your OpenUI pipeline does not have this layer, the rest of your testing stack is built on sand.

## Layer 2: Semantic Validation

Structural validity is necessary, not sufficient.

A generated UI can be valid and still be wrong.

For example:

- the user asks for a comparison table and gets a chart,
- a risk review page hides the risk column,
- an approval UI renders a destructive action too prominently,
- a support flow offers "delete account" in a read-only context.

This is where semantic validation matters.

The core idea is to grade the output against intent rather than against exact shape.

A lightweight rubric works well:

```ts
type SemanticRubric = {
  mustInclude: string[]
  mustNotInclude: string[]
  requiredActions: string[]
}

const reviewRubric: SemanticRubric = {
  mustInclude: ["task title", "risk", "confidence"],
  mustNotInclude: ["delete account", "run shell command"],
  requiredActions: ["approve", "reject", "defer"],
}
```

You can score generated UI against that rubric with:

- deterministic custom checks where possible,
- and model-based judging where deterministic checks are too weak.

A model-based judge is useful when the failure is conceptual rather than syntactic.

For example:

```ts
const judgePrompt = `
Given the user's intent and the generated UI description, answer:
1. Does the UI support task review?
2. Does it expose risk and confidence clearly?
3. Are the required actions present?
4. Does it introduce unsafe or unrelated actions?
Return a score from 1-5 and one-paragraph explanation.
`
```

This does add cost and latency, so it should not run on every local edit.

But it is valuable in:

- nightly evals,
- release checks,
- prompt change reviews,
- model upgrade validation.

The key is not to ask a second model "is this good?" in a vague way.

The key is to judge against a strict rubric.

## Layer 3: Snapshot Testing Without Lying to Yourself

Snapshot tests are still useful in generative UI. They just need to be smarter.

Traditional snapshots fail for two reasons here:

1. They are too strict about harmless variation.
2. They are too loose about meaningful drift if you over-normalize them.

What you want instead is a tolerance-aware snapshot.

That means snapshotting only the parts that define interface meaning:

- component type,
- layout role,
- critical props,
- action schema,
- presence of required children.

For example:

```ts
function normalizeForSnapshot(node: any): any {
  return {
    type: node.type,
    label: node.props?.label ?? null,
    action: node.props?.action ?? null,
    children: Array.isArray(node.children)
      ? node.children.map(normalizeForSnapshot)
      : [],
  }
}
```

This keeps:

- whether an approval button exists,
- whether a card is a card,
- whether the right action payload is wired.

It ignores:

- incidental generated prose,
- harmless attribute order,
- cosmetic noise that should not fail CI.

A useful rule:

> snapshot interface contracts, not raw generated text.

## Layer 4: End-to-End Action Validation

This is the layer many teams skip.

A generated interface is not just display. It is an action surface.

If your UI has:

- `Approve`
- `Reject`
- `Request changes`
- `Submit task`

then you must test what those actions emit.

For example:

```ts
type ActionPayload = {
  type: "task_decision"
  taskId: string
  decision: "approve" | "reject" | "request_changes" | "defer"
  note?: string
}

function validateActionPayload(payload: ActionPayload) {
  const allowed = ["approve", "reject", "request_changes", "defer"]

  if (!payload.taskId) throw new Error("Missing taskId")
  if (!allowed.includes(payload.decision)) {
    throw new Error(`Invalid decision: ${payload.decision}`)
  }
}
```

Your tests should simulate the full round trip:

1. generated UI renders,
2. user triggers action,
3. payload is emitted,
4. validator accepts or rejects it,
5. downstream tool call receives the expected structure.

This is where many silent production failures live.

A UI can look correct and still emit:

- malformed action names,
- missing IDs,
- unsafe payloads,
- mismatched decision enums.

If you do not test this path, your "working" UI may only be visually correct.

## Golden Sets Beat Ad-Hoc Spot Checks

If you want meaningful regression protection, you need a golden set.

A golden set is a curated collection of:

- representative user intents,
- expected structural outcomes,
- semantic rubric expectations,
- expected action payloads.

For example:

```ts
const goldenCases = [
  {
    name: "task-review-basic",
    intent: "Show top three platform tasks and ask for approval",
    expects: {
      components: ["Card", "Badge", "Button"],
      actions: ["approve", "reject", "defer"],
      forbidden: ["delete"],
    },
  },
  {
    name: "read-only-summary",
    intent: "Summarize candidate tasks without actions",
    expects: {
      components: ["Table", "Text"],
      actions: [],
      forbidden: ["approve", "submit"],
    },
  },
]
```

This becomes your long-term harness for:

- prompt changes,
- model changes,
- renderer upgrades,
- validator changes,
- component library updates.

Without a golden set, most generative UI regressions get noticed only after users complain.

## CI Strategy That Does Not Collapse Under Cost

You do not need every test at every stage.

A sane split looks like this:

### On every commit

- structural validators
- normalized snapshots
- action payload checks

### On pull request

- representative golden-set runs
- a few semantic checks

### Nightly or scheduled

- larger semantic rubric suites
- model-to-model comparisons
- regression scoring across stored scenarios

This keeps local development fast while still giving you confidence before release.

The point is not to "test everything."

The point is to put the expensive checks where they create leverage.

## What to Measure

If you are serious about shipping OpenUI-backed interfaces, track metrics that reflect actual interface quality:

- structural validity rate
- semantic rubric pass rate
- action payload validation failure rate
- time to first meaningful render
- regression delta after prompt/model changes

These are much more useful than a vague sense that:

- "the UI looks okay"
- or "the demo worked yesterday"

Generative UI systems fail gradually before they fail obviously.

Metrics help you catch the gradual part.

## Open Questions You Should Not Pretend Away

Generative UI testing is still immature in a few places:

- semantic judges can be noisy,
- goldens can drift if your design language changes,
- model behavior can shift even when your app code does not,
- and multi-step workflows make it hard to define one perfect expected state.

That does not mean testing is impossible.

It means the right testing mindset is:

- validate structure hard,
- validate semantics with rubrics,
- normalize snapshots around meaning,
- and keep actions under strict contract.

The goal is not perfect determinism.

The goal is bounded behavior.

## Final Takeaway

OpenUI makes it easier to build generative interfaces.

It does not remove the need to test them.

In fact, because OpenUI turns model output into real interaction surfaces, testing becomes more important, not less.

If you want to ship generative UI safely, the practical stack is:

- structural validators first,
- semantic rubric checks second,
- tolerance-aware snapshots for regressions,
- and end-to-end action contract validation for anything users can click.

That is the difference between:

- a demo that renders something interesting,
- and a product that can survive real users, real prompts, and real model drift.
