# Voice Agents Need a Visual Commit Log

Voice agents are becoming good at conversation. They can listen, answer quickly, use tools, and keep a natural rhythm. That makes them feel more useful than a form and less rigid than a phone tree.

But voice has a serious weakness: it disappears.

If an agent lists three plans, the user has to remember them. If it asks for a shipping address, the user cannot easily scan what was captured. If it recommends an irreversible action, the confirmation often lives only in the transcript. Voice is excellent for intent and pacing. It is weak as a durable work surface.

That is why the next useful voice-agent pattern is not voice alone. It is voice plus generated UI. LiveKit can run the realtime audio loop. OpenUI can render the visual state that the agent is building as it speaks.

Think of the UI as the agent's visual commit log: the stable, inspectable record of facts, choices, forms, and actions that came out of the spoken turn.

## The problem with voice-only answers

Imagine a travel assistant:

```txt
I found three flights. The first is cheaper but has a long layover.
The second is nonstop but lands late. The third is refundable and
arrives mid-afternoon.
```

That sounds natural. It is also hard to act on.

The user may ask, "Wait, which one was refundable?" The agent repeats itself. Then the user asks about baggage. The agent repeats again. Every step depends on memory and turn-taking instead of inspection.

Now imagine the same response with a generated UI panel:

- three flight cards,
- price, arrival time, refund policy, and baggage details,
- tags for tradeoffs,
- a selected option,
- and a visible "hold this flight" action.

The agent can still speak naturally. The user can still interrupt. But the important state no longer vanishes into the audio stream.

## LiveKit owns the realtime conversation

LiveKit is a strong fit for the voice side because it handles the parts that are hard to fake in a browser demo:

- realtime audio transport,
- room and participant state,
- low-latency agent interactions,
- interruption handling,
- and integration with agent frameworks.

In a voice-agent app, LiveKit is responsible for the loop that feels conversational:

1. The user speaks.
2. Speech is transcribed.
3. The agent reasons and calls tools.
4. Audio is synthesized back to the user.
5. The user can interrupt, clarify, or continue.

That loop should stay fast. The visual layer should not block first audio. A good voice agent can start speaking while the UI is still being assembled.

## OpenUI owns the visible state

OpenUI is useful because the visual side does not need to be a hand-coded screen for every possible answer.

Your app defines a component library:

```tsx
const FlightOption = defineComponent({
  name: "FlightOption",
  description: "A selectable flight option with price and tradeoffs.",
  props: z.object({
    id: z.string(),
    route: z.string(),
    price: z.string(),
    arrival: z.string(),
    tradeoffs: z.array(z.string()),
  }),
  component: ({ props }) => <FlightCard {...props} />,
});
```

The model can then output OpenUI Lang using only the components your app approves. The renderer maps those statements into React components as the response streams.

For voice agents, that means the spoken answer and visual answer can be two views of the same turn:

- speech for the human-friendly explanation,
- OpenUI Lang for the structured interface,
- app actions for anything that changes state.

The model does not get to invent arbitrary UI code. It gets to compose from your library.

## Use turn IDs to avoid stale UI

Voice conversations are messy. Users interrupt. Agents self-correct. Tool calls finish late. A response that was correct three seconds ago may be stale now.

Generated UI needs a turn identity.

Each spoken turn should have an ID, and every visual update should belong to that ID:

```ts
type VisualTurnUpdate = {
  turnId: string;
  sequence: number;
  openui: string;
  status: "streaming" | "final" | "superseded";
};
```

When the user interrupts, the app can mark the current turn as superseded. The UI can keep the last stable panel visible, dim the stale section, or replace it with the new turn's output. The key is that the visual state does not silently mix two different spoken contexts.

This is especially important for actions. A "Confirm booking" button from a superseded turn should not remain active after the user changes destination or budget.

## Render partial UI without delaying speech

A common mistake is to treat the visual layer as a full response artifact. The agent speaks only after it has generated the whole UI. That defeats the point of realtime voice.

The better flow is parallel:

1. Start audio as soon as the agent has a useful spoken response.
2. Stream OpenUI Lang as the structured visual response develops.
3. Render the shell first.
4. Fill in tables, cards, forms, and actions as statements arrive.

OpenUI's renderer can parse and render streamed content, which makes this shape practical. A root component can appear early:

```txt
root = TripOptions("I found three good matches", [optionA, optionB, optionC])
```

Then individual option cards can arrive as the model fills in details:

```txt
optionA = FlightOption("a", "SFO to JFK", "$318", "6:40 PM", ["long layover"])
optionB = FlightOption("b", "SFO to JFK", "$421", "3:10 PM", ["nonstop"])
```

The user hears the summary and sees the structure appear without waiting for a complete final object.

## Make interruptions visible

Interruption handling is one of the reasons voice feels alive. It is also one of the reasons voice UI can become confusing.

If the user interrupts with "Actually, make it refundable only", the audio agent can stop speaking and restart. The visual layer should show what happened:

- previous options are marked stale,
- a new constraint appears as a visible filter,
- updated options stream in,
- actions from the old turn are disabled,
- and the final state clearly reflects the new request.

Without that visible transition, the user has to infer whether the agent understood the correction.

The UI is not decoration here. It is the continuity layer.

## Use the visual layer for confirmation

Voice confirmation is fragile for high-impact actions.

If the agent says, "I will cancel the subscription now", the user may respond "yes" while distracted. If the agent reads a long legal summary, the user may not catch every detail. A generated UI confirmation panel creates a safer checkpoint.

A good confirmation surface includes:

- the exact action,
- affected account or object,
- irreversible consequences,
- required acknowledgements,
- and a final button controlled by the application.

The model can generate the panel from approved components, but the app must own the final execution. The server should still check permissions, validate current state, and record the decision.

Voice can ask. UI should commit.

## Keep component libraries task-specific

Do not give a voice agent every possible UI component. The component library should match the domain.

A scheduling agent may need:

- `AvailabilityGrid`,
- `MeetingOption`,
- `ParticipantConflict`,
- `CalendarAction`.

A support agent may need:

- `IssueSummary`,
- `TroubleshootingStep`,
- `LogSnippet`,
- `EscalationAction`.

A shopping agent may need:

- `ProductComparison`,
- `FilterChip`,
- `CartPreview`,
- `CheckoutConfirmation`.

Small libraries make the model more reliable and make the visual output easier for users to understand. They also keep prompts shorter and action handling clearer.

## A practical architecture

A production voice-plus-UI loop can look like this:

1. LiveKit manages the room, audio stream, transcription, and agent session.
2. The agent receives the transcript and current app context.
3. The agent produces two streams: spoken response text and OpenUI Lang.
4. Text-to-speech starts as soon as the spoken response is ready.
5. The client sends OpenUI Lang chunks to `<Renderer />`.
6. The renderer displays a safe component tree from the app library.
7. User actions flow back through app-owned handlers, not arbitrary model code.
8. Turn IDs prevent stale visual actions after interruptions.

That design keeps each part honest. LiveKit handles realtime presence and audio. OpenUI handles structured rendering. The app handles permissions and state changes.

## The takeaway

Voice agents should not try to make users remember everything.

For short answers, voice is enough. For complex tasks, the agent needs a visible surface that survives the turn. Options should stay visible. Forms should be editable. Confirmations should be explicit. Actions should be safe. Corrections should be reflected in state, not buried in a transcript.

LiveKit and OpenUI pair naturally because they solve different halves of the same experience. LiveKit makes the agent conversational. OpenUI makes the conversation inspectable and actionable.

That is the pattern to aim for: voice for flow, generated UI for state, and application code for authority.
