# OpenUI for Voice Agents: The Latency and State Contract

Voice agents have a strange user-experience problem: the interface disappears as soon as the audio finishes.

That is fine for simple answers. If a user asks "what time is my next meeting?", a spoken reply is enough. But the moment the answer contains options, state, warnings, prices, rows, forms, or a confirmation step, audio becomes a lossy transport. The user has to remember the details, ask the agent to repeat them, or trust that the agent did the right thing.

Pairing LiveKit with OpenUI solves a different problem than "make the chatbot prettier." LiveKit keeps the voice loop fast and interruptible. OpenUI gives the same agent a durable visual surface for the parts of the interaction that should not vanish into the transcript.

The important architecture is not just audio plus UI. It is a contract:

1. Speech handles intent, pacing, and conversational repair.
2. OpenUI handles inspectable state, choices, forms, and confirmations.
3. Both outputs are tied to the same agent turn, so the user never has to reconcile two separate answers.

That contract is what makes voice agents useful for real tasks.

## The Failure Mode: Voice-Only Output For Visual Work

Imagine a travel assistant answering by voice:

> I found three hotel options. The first is 224 dollars per night and has free cancellation, the second is 197 dollars but is non-refundable, and the third is 252 dollars with breakfast included. The first has an 8.7 rating, the second has an 8.2 rating, and the third has a 9.1 rating...

The answer is technically correct and practically bad. The user cannot scan it, compare it, sort it, save it, or tap the option they want. If they interrupt halfway through, they may lose the most important detail.

Now move the same turn into a voice plus OpenUI flow:

- The agent says: "I found three good options. The safest pick is the refundable one, but I put all three on screen."
- OpenUI renders a comparison table with price, cancellation policy, rating, distance, and a "Hold this room" action.
- The user can keep talking while the table stays visible.

The spoken output becomes a guide. The generated UI becomes the working surface.

That split is the core design principle.

## A Practical LiveKit + OpenUI Shape

A production implementation can keep the pieces simple:

```text
microphone
  -> LiveKit room
  -> agent session
  -> LLM/tool turn
  -> speech response
  -> OpenUI stream
  -> browser renderer
  -> UI action back to agent
```

LiveKit is responsible for realtime audio transport, room state, interruption handling, and the agent's conversational loop. OpenUI is responsible for rendering structured UI that the model can compose from an approved component library.

The agent should not dump arbitrary React into the browser. It should emit a constrained OpenUI payload that maps to product-owned components:

```tsx
const hotelResult = {
  component: "OptionTable",
  props: {
    title: "Three hotel options",
    rows: [
      {
        id: "refundable",
        name: "North Loop Hotel",
        price: "$224/night",
        rating: "8.7",
        cancellation: "Free until Friday",
        recommended: true,
      },
      {
        id: "budget",
        name: "Canal Studio",
        price: "$197/night",
        rating: "8.2",
        cancellation: "Non-refundable",
        recommended: false,
      },
    ],
    actions: [
      { id: "hold-room", label: "Hold this room", variant: "primary" },
      { id: "compare-map", label: "Show on map", variant: "secondary" },
    ],
  },
};
```

The exact syntax depends on the OpenUI setup, but the boundary matters more than the notation. The model chooses from known interface primitives. The app owns rendering, styling, validation, authorization, and action handling.

## The Latency Budget

Voice agents are sensitive to latency in a way text chat is not. A slow text response is annoying. A slow voice response feels broken.

A useful target is to split the turn into three clocks:

1. **First audio token:** How quickly does the user hear that the agent understood?
2. **First visual frame:** How quickly does the browser show useful state?
3. **Action-ready UI:** How quickly can the user safely click or confirm something?

Do not wait for a perfect UI before speaking. The agent can start with a short bridge phrase:

> "I am checking the options now."

Then the UI can stream in as it becomes structured:

```text
0 ms     user finishes speaking
300 ms   agent starts a short acknowledgement
900 ms   tool call returns first candidate data
1200 ms  OpenUI renders skeleton plus first rows
1800 ms  agent summarizes the recommendation
2300 ms  action buttons become enabled
```

This is where OpenUI's streaming-friendly model is useful. The UI can progressively move from placeholder to partial result to action-ready result without making the user stare at a blank region.

The mistake is treating the visual surface as a post-processing artifact. If the UI appears after the spoken answer ends, it feels like a receipt. If it appears during the turn, it feels like part of the conversation.

## The State Contract

The browser, the agent, and the user need to agree on what the current turn means. That requires a small state contract.

Each generated UI surface should carry:

- `turnId`: which voice turn created this UI
- `status`: `streaming`, `ready`, `needs_confirmation`, `error`, or `superseded`
- `dataVersion`: the tool result or retrieval version behind the UI
- `allowedActions`: actions the frontend is allowed to expose
- `spokenSummary`: the short sentence the agent used to describe the UI

That metadata prevents subtle bugs.

If the user interrupts while a table is streaming, the UI should not keep pretending to be current. Mark it as `superseded`. If a newer tool result arrives, disable actions from the older result. If the agent says "I can book the refundable option," the UI should make clear which option is being discussed.

A simple envelope is enough:

```ts
type VoiceUiEnvelope = {
  turnId: string;
  status: "streaming" | "ready" | "needs_confirmation" | "error" | "superseded";
  dataVersion: string;
  spokenSummary: string;
  ui: unknown;
  allowedActions: Array<{
    id: string;
    requiresConfirmation: boolean;
  }>;
};
```

This is not glamorous code, but it is the difference between a demo and a product.

## Confirmations Should Be Visual

The most important rule for action-taking voice agents is simple: irreversible or expensive actions should not rely on audio alone.

Spoken confirmation is too easy to mishear. A good voice agent can still say:

> "I am ready to swap 10 USDC to SOL. Please confirm on screen."

But the confirmation should be visual:

```text
Swap preview
- From: 10 USDC
- To: estimated 0.42 SOL
- Slippage: 0.5 percent
- Network fee: 0.00001 SOL

[Confirm swap] [Cancel]
```

OpenUI is the right place for that confirmation because it can preserve the exact payload. The action handler should validate the payload again server-side. The UI is a confirmation surface, not a source of authority.

That same pattern applies to booking, sending email, deleting data, updating CRM records, changing permissions, or approving a purchase.

Use voice to explain. Use UI to commit.

## Interruptions Are A Feature, Not An Edge Case

Live voice agents must handle barge-in. Users interrupt because they noticed something, changed their mind, or do not want the rest of the answer.

The visual layer needs to respect that.

When the user interrupts:

1. Stop or fade the current spoken answer.
2. Mark in-progress UI as interrupted or superseded.
3. Keep already useful state visible if it still matters.
4. Disable unsafe actions until the new turn resolves.

For example, if the user says "only show refundable rooms" while the first hotel table is streaming, do not erase everything instantly. Keep the old table visible as stale state, show a small "updating filters" state, then replace it when the filtered tool result returns.

This is the kind of detail that makes a voice agent feel trustworthy. The user can see what changed and why.

## What To Render, And What To Keep Spoken

Not every voice response needs UI. Rendering everything is just another kind of noise.

A useful rubric:

Render UI when the answer includes:

- more than two options
- numbers the user may compare
- an action or confirmation
- progress through a workflow
- data that should remain visible after the turn
- errors with recovery steps

Keep it spoken when the answer is:

- a short fact
- a conversational clarification
- a status acknowledgement
- a question that expects a quick verbal answer

The best voice agents are not visual dashboards with audio bolted on. They are conversations that know when to leave artifacts behind.

## A Minimal Build Plan

For a prototype, start narrow.

1. Create one LiveKit voice agent flow with a single tool, such as product comparison or appointment scheduling.
2. Define three OpenUI components: `ResultCard`, `OptionTable`, and `ConfirmationPanel`.
3. Add the `VoiceUiEnvelope` around every generated UI payload.
4. Stream UI updates to the browser as a separate channel from audio.
5. Route button clicks back to the agent as typed actions.
6. Require visual confirmation for anything irreversible.

The first demo should prove one full loop:

```text
user speaks
  -> agent calls tool
  -> agent speaks a short summary
  -> UI renders structured result
  -> user clicks an action
  -> agent acknowledges the action by voice
```

That loop matters more than the number of components.

## Production Checks

Before shipping, test the things demos usually skip:

- What happens when the UI stream fails but audio succeeds?
- What happens when audio is interrupted but the UI is still streaming?
- Can a stale button submit an old action payload?
- Does every generated component have an accessible name?
- Does the mobile layout survive while the user is still speaking?
- Can the user complete the same task with audio muted?
- Can the user review the final action before it commits?

These checks are where OpenUI becomes more than output formatting. It becomes the durable state layer for an agent that would otherwise be trapped in a transcript.

## The Payoff

LiveKit makes the agent feel present. OpenUI makes the agent's work inspectable.

That combination is powerful because users do not want a voice agent that talks more. They want one that helps them finish tasks with less uncertainty.

Use audio for the human part: intent, acknowledgement, repair, and guidance.

Use generated UI for the parts that need structure: options, data, state, and confirmation.

When those two channels share the same turn state, the agent stops being a talking chatbot and starts feeling like an interface that can listen.
