# OpenUI for Voice Agents: A QA Playbook for Real-Time Visual Feedback

Most voice agent demos are judged by the first happy-path recording: the user asks a question, the agent answers, and a nice card or table appears beside the transcript.

That is a useful demo, but it is not enough for a product. Once a voice agent can also render UI, the failure modes multiply. The agent can say one thing while the visual pane shows another. A previous visual stream can finish after a newer turn starts. A button can continue the wrong conversation. A confirmation card can remain clickable after the user interrupts. The UI can be valid React and still be semantically wrong.

Pairing LiveKit with OpenUI is powerful because it lets a realtime voice loop produce durable visual state. The practical question is: how do you test that loop before you put it in front of users?

This article walks through a QA playbook for LiveKit voice agents that render OpenUI-powered visual feedback. The examples are grounded in the public Thesys voice-agent generative UI demo, where a LiveKit agent calls a `show_ui` tool, streams generated UI to a `genui` text-stream topic, and the React app renders the stream through `C1Component`.

The goal is not to make the UI deterministic. The goal is to make the voice-plus-UI contract observable, replayable, and testable.

## The Voice Plus UI Contract

A plain voice agent has a narrow contract:

1. Listen to the user.
2. Decide what to do.
3. Speak a response.

A voice agent with generative UI has a wider contract:

1. Listen to the user.
2. Decide whether a visual surface is useful.
3. Start speaking quickly enough that the interaction still feels realtime.
4. Stream visual UI without blocking speech.
5. Render partial UI safely while the stream is still arriving.
6. Handle UI actions as part of the same conversation.
7. Cancel, replace, or mark stale UI when the user changes direction.

That wider contract is why the architecture in the reference demo is interesting. The `show_ui` tool does not wait for the whole visual response before the agent can speak. It starts a background stream, writes chunks to a LiveKit text stream with the topic `genui`, and returns immediately with a short instruction telling the agent to describe what is loading on screen.

On the frontend, the room registers a text stream handler for `genui`, appends chunks into local state, and passes the accumulated response into `C1Component` with `isStreaming`. Generated UI actions are passed back through an `onAction` handler, usually as a conversation continuation.

That is the right shape for realtime UX: voice stays responsive, visuals arrive progressively, and the UI can send structured intent back to the agent.

It also gives us clear test boundaries.

## What Needs Testing

There are five surfaces worth testing separately.

### 1. The Decision Surface

The agent must decide when to render UI. Not every turn needs a visual surface. "Thanks" should not create a dashboard. A pricing comparison, a schedule, a form, or a multi-step plan probably should.

The test question is:

> Did the agent call `show_ui` only when visual state would help the user?

### 2. The Speech Surface

The agent must keep spoken output short while the UI carries structured detail. If the agent reads a whole table aloud, the visual pane is not doing its job.

The test question is:

> Did speech summarize the UI rather than duplicate it?

### 3. The Stream Surface

The visual response is streamed. That means you need to catch broken partial output, late chunks, cancellation behavior, and empty streams.

The test question is:

> Can the frontend render, replace, or clear visual content without blank screens or stale UI?

### 4. The Semantic Surface

A generated UI can be syntactically valid and still wrong. A flight comparison can swap prices. A meeting scheduler can show the wrong timezone. A confirmation card can hide the destructive nature of the action.

The test question is:

> Does the UI preserve the facts and intent of the current turn?

### 5. The Action Surface

Buttons, forms, and cards are not decoration. They continue the agent loop. A click should send a safe, specific, user-approved message back to the agent.

The test question is:

> Did the UI action produce the correct next-turn intent, and was it tied to the current visual state?

## Add Turn IDs Before You Add More Features

The easiest way to lose trust in a realtime voice UI is to show stale visual state. A user interrupts a hotel search with "Actually, make it Tokyo," but the previous Kyoto hotel cards finish streaming a second later. The agent may be correct from that point onward, but the screen just contradicted it.

Add a turn identifier to every visual request before the app grows more complex.

```ts
type VisualTurn = {
  turnId: string;
  userUtterance: string;
  visualIntent: "compare" | "form" | "list" | "detail" | "summary";
  startedAt: number;
};
```

In a minimal implementation, the frontend can keep `activeTurnId` in state. Every chunk and every action is associated with that turn. If a new turn starts, old chunks are ignored or shown as superseded.

```ts
function applyVisualChunk(event: {
  turnId: string;
  chunk: string;
}) {
  if (event.turnId !== activeTurnId.current) {
    return;
  }

  setGenUIContent((current) => current + event.chunk);
}
```

The reference demo uses a single `genui` text stream and clears `genUIContent` whenever a new stream starts. That is enough for a demo. For production testing, make the turn boundary explicit in logs and trace fixtures, even if you keep the runtime protocol simple at first.

## Capture a Trace for Every Voice-UI Turn

Good QA starts with traces. You need to see what happened across audio, tool calls, visual streams, and UI actions.

A trace does not need to capture private audio. For most regression tests, structured metadata is enough.

```json
{
  "turnId": "turn_2026_05_19_001",
  "prompt": "Compare three CRM tools for a five-person sales team.",
  "events": [
    { "t": 0, "type": "user_final_transcript" },
    { "t": 310, "type": "agent_started_speaking" },
    { "t": 520, "type": "show_ui_called", "visualIntent": "compare" },
    { "t": 790, "type": "genui_first_chunk" },
    { "t": 1420, "type": "genui_first_render" },
    { "t": 2610, "type": "genui_stream_closed" },
    { "t": 4910, "type": "ui_action", "action": "continue_conversation" }
  ]
}
```

This gives you measurable acceptance criteria:

- First speech should happen before the visual stream completes.
- First visual chunk should arrive soon after `show_ui_called`.
- The stream should close cleanly.
- The first render should not wait for the full response.
- UI actions should include enough context to continue safely.

These are not vanity metrics. They catch real bugs.

If `agent_started_speaking` comes after `genui_stream_closed`, the UI generation is blocking the voice loop. If `ui_action` fires after a new turn starts, the user may be acting on stale UI. If `genui_first_render` never appears but chunks were received, the renderer is failing.

## A Small Test Harness

You can build a simple harness around the frontend stream handler without mocking all of LiveKit.

The reference frontend receives an async iterable of chunks. That is already a test-friendly shape. Extract the accumulation logic into a small function or hook, then feed it fake streams.

```ts
async function collectVisualStream(
  reader: AsyncIterable<string>,
  onChunk: (content: string) => void,
) {
  let accumulated = "";

  for await (const chunk of reader) {
    accumulated += chunk;
    onChunk(accumulated);
  }

  return accumulated;
}

async function* chunks(parts: string[]) {
  for (const part of parts) {
    yield part;
  }
}
```

Now you can test progressive behavior.

```ts
it("emits accumulated visual content as chunks arrive", async () => {
  const frames: string[] = [];

  const final = await collectVisualStream(
    chunks(["Card(", "\"CRM A\"", ")"]),
    (content) => frames.push(content),
  );

  expect(frames).toEqual([
    "Card(",
    "Card(\"CRM A\"",
    "Card(\"CRM A\")",
  ]);
  expect(final).toBe("Card(\"CRM A\")");
});
```

You are not asserting that the model always produces the same UI. You are asserting that your stream consumer behaves correctly when UI arrives incrementally.

## Replay the Visual Stream

A trace becomes more valuable when it can be replayed. Store generated visual chunks as JSONL during manual test sessions.

```jsonl
{"turnId":"turn_001","type":"chunk","value":"Stack(["}
{"turnId":"turn_001","type":"chunk","value":"TextContent(\"CRM comparison\"),"}
{"turnId":"turn_001","type":"chunk","value":"Table([...])])"}
```

Then add a tiny replay page or test helper that feeds those chunks back into the renderer with the same timing. This catches regressions in three places:

- The renderer no longer accepts an output shape it previously rendered.
- The frontend blank state or skeleton logic hides partial UI too long.
- Action callbacks changed shape and no longer continue the conversation.

Replay tests are especially useful for voice agents because live audio tests are slow and flaky. You can keep a small set of golden traces:

| Scenario | What It Catches |
| --- | --- |
| Product comparison | Tables, cards, image references, action buttons |
| Trip planner form | Form fields, defaults, submit action |
| Metrics dashboard | Charts, units, numeric formatting |
| Interrupt and replace | Stale stream cancellation |
| Destructive action confirmation | Explicit confirmation language |

## Semantic Checks Beat Pixel Checks

Screenshots are useful for layout regressions, but generative UI needs semantic assertions too.

For example, if the user asks:

> Compare the free and pro plans. Highlight the cheapest option for a solo developer.

A valid UI should include:

- both plan names,
- prices,
- the solo-developer recommendation,
- a visible comparison structure,
- and no invented plan.

That can be checked without freezing the exact copy or layout.

```ts
const requiredFacts = [
  "Free",
  "Pro",
  "$0",
  "$20",
  "solo developer",
];

for (const fact of requiredFacts) {
  expect(renderedText).toContain(fact);
}
```

For higher confidence, write scenario-specific validators:

```ts
type PlanComparison = {
  plans: Array<{ name: string; monthlyPrice: number }>;
  recommendation: string;
};

function validatePlanComparison(result: PlanComparison) {
  expect(result.plans.length).toBeGreaterThanOrEqual(2);
  expect(result.plans.some((plan) => plan.name === "Free")).toBe(true);
  expect(result.recommendation.toLowerCase()).toContain("solo");
}
```

The point is to test what the UI means, not the exact sentence the model chose.

## Test Interruptions as a First-Class Flow

Voice users interrupt. They correct themselves. They change filters mid-sentence. They stop an action after seeing the visual result.

Your QA matrix should include interruption prompts:

| Prompt | Interruption | Expected Result |
| --- | --- | --- |
| "Show me hotels in Kyoto under $200." | "Actually, make it Tokyo." | Kyoto stream stops or becomes stale; Tokyo UI wins. |
| "Build a signup form." | "No, just collect email." | The final UI is a one-field form. |
| "Compare these vendors." | User clicks an old card after a new comparison starts. | The old action is ignored or requires refresh. |
| "Cancel my subscription." | User says "wait" during confirmation. | The confirmation UI is disabled or replaced. |

The most important assertion is that old UI cannot silently control new state.

## Test UI Actions Like Tool Calls

Generated UI actions deserve the same care as agent tools. In the demo, `open_url` opens a link, while `continue_conversation` sends an LLM-friendly message back into the LiveKit chat loop.

That pattern is flexible, but the action payload needs guardrails.

A weak action payload looks like this:

```json
{
  "type": "continue_conversation",
  "params": {
    "llmFriendlyMessage": "Book it"
  }
}
```

A stronger payload is explicit:

```json
{
  "type": "continue_conversation",
  "params": {
    "turnId": "turn_001",
    "llmFriendlyMessage": "The user selected the Pro plan from the visible pricing comparison. Continue by asking for billing-cycle preference before checkout.",
    "requiresConfirmation": true
  }
}
```

Even if the renderer only passes a simple event today, test for the intent you eventually want:

- Which visible item did the user act on?
- Is the action reversible?
- Does it need confirmation?
- Is it still tied to the active turn?
- Does it expose only the data the agent needs?

## A Practical Acceptance Checklist

Use this checklist before shipping a LiveKit plus OpenUI voice flow.

| Area | Acceptance Criteria |
| --- | --- |
| Speech | Agent gives a short spoken summary, not a full visual readout. |
| Visual decision | `show_ui` is used for structured data, comparisons, forms, and multi-step flows. |
| Streaming | First visual frame appears before full generation completes. |
| Replacement | Starting a new visual turn clears or supersedes the previous one. |
| Stale actions | Actions from old turns are ignored, disabled, or revalidated. |
| Semantics | Key facts from the user request appear in the generated UI. |
| Accessibility | Critical information is available in text, not only color, position, or imagery. |
| Recovery | Renderer errors show a useful fallback instead of leaving a blank panel. |
| Confirmation | Irreversible or high-impact actions require explicit user confirmation. |
| Replay | At least five golden voice-to-UI traces can be replayed locally. |

This checklist is intentionally product-facing. A voice agent can pass unit tests and still fail if the user cannot trust what is on screen.

## Where OpenUI Helps

OpenUI helps because it gives the model a constrained visual language and a React rendering path instead of asking it to invent arbitrary frontend code. For voice agents, that is more than a frontend convenience. It creates a layer you can observe and test.

The LiveKit side gives you the realtime room, audio lifecycle, text streams, and agent loop. The OpenUI side gives you a structured visual output that can be streamed, rendered progressively, and wired back into conversation actions.

Together, they let you build a voice agent that does not force users to remember everything they heard. The agent can speak the summary and leave the working surface on screen: a table, a form, a dashboard, a comparison, or a confirmation.

The production bar is making sure those two channels stay aligned.

## Start With Three Golden Scenarios

If you are adding generative UI to a voice agent for the first time, do not start with a giant automated suite. Start with three golden scenarios:

1. A comparison flow with three options and one recommendation.
2. A form flow where the user changes requirements mid-turn.
3. A confirmation flow where the user must approve an action from the visual UI.

Capture traces for each. Replay the streams. Assert the important facts. Check stale turn behavior. Verify the spoken response is short.

That small suite will catch more useful failures than a large set of brittle snapshot tests.

The promise of LiveKit plus OpenUI is not just that agents can talk and show UI at the same time. It is that the interface can become the durable half of a realtime conversation. Users should be able to hear the answer, inspect the details, and act with confidence.

That confidence comes from the product contract behind the demo: observable turns, replayable streams, semantic checks, and UI actions that respect the current conversation.

## References

- [OpenUI GitHub repository](https://github.com/thesysdev/openui)
- [OpenUI docs](https://www.openui.com/)
- [Thesys voice-agent generative UI demo](https://github.com/thesysdev/voice-agent-generativeui)
- [LiveKit Agents documentation](https://docs.livekit.io/agents/)
- [LiveKit text streams documentation](https://docs.livekit.io/home/client/data/text-streams/)
