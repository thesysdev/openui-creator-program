# OpenUI for Voice Agents: The Visual Commit Log

Voice agents are fast, natural, and surprisingly good at making a product feel alive. They are also terrible at one thing most software workflows depend on: leaving behind a state that the user can inspect.

If a voice agent compares three insurance plans, reads out a travel itinerary, explains a sales pipeline, or asks for approval on a workflow step, the spoken answer disappears as soon as it is said. The user can interrupt, but they cannot scan. They can ask the agent to repeat itself, but they cannot sort, edit, approve, or point at the one row that matters.

That is the real reason to pair LiveKit with OpenUI. The goal is not to make a voice agent more decorative. The goal is to give every important spoken turn a visual commit: a durable, structured UI state that shows what the agent meant, what data it used, what the user can do next, and which action will be sent back into the conversation.

The Thesys voice-agent demo is a useful reference because it does not treat the visual side as a screenshot after the fact. The LiveKit agent can speak immediately, while a separate generated UI stream appears in the browser. In the reference implementation, `show_ui` starts a background stream, publishes chunks over a LiveKit text-stream topic named `genui`, and lets the front end render the accumulating response through `C1Component`. The audio and visual channels are separate, but they belong to the same user turn.

That separation is the whole design pattern.

## The Problem With Audio-Only State

Audio is excellent for intent. A user can say, "Find three hotels near the venue, under $250, with late checkout," faster than they can fill out a form. A voice agent can ask one clarifying question without freezing the workflow. For discovery, triage, and lightweight command entry, voice is often better than a chat box.

But audio is weak as a state container. A spoken list is linear. A comparison table becomes a memory test. A set of next actions becomes ambiguous because the user has to remember the option labels. A confirmation step becomes risky because there is no stable artifact that says exactly what will happen.

This is especially painful in four common workflows:

1. Comparisons, where the user needs to scan multiple options across the same fields.
2. Forms, where the user needs to review structured inputs before submitting.
3. Dashboards, where the user needs persistent metrics rather than a verbal summary.
4. Approvals, where the user needs to see the exact action payload before saying yes.

A strong voice interface should use audio for the conversation and UI for the commit log. The spoken channel explains the moment. The visual channel preserves the state.

## A Two-Channel Turn Contract

A useful way to design voice plus generative UI is to treat every rich response as a two-channel contract:

```txt
user intent
  -> voice agent decides what should happen
  -> audio channel gives a short narration
  -> visual channel renders the structured state
  -> user action returns a specific continuation message
```

LiveKit is a good fit for the realtime side of that contract. It manages the room, the agent session, audio, connection lifecycle, text streams, and chat messages. OpenUI or C1 is a good fit for the visual side because the agent can emit structured content that turns into components instead of prose.

The important product decision is that the two channels should not duplicate each other. The agent should not read a full table while also showing the table. It should say something like, "I pulled together three options and highlighted the tradeoffs," then let the screen carry the details.

The reference prompt follows this direction. It tells the voice agent to keep spoken responses concise and conversational, use `show_ui` whenever information is better seen than heard, and avoid reading long lists aloud. That is not just a style preference. It is a latency and cognition strategy: speak quickly, render the detail, and let the user inspect.

## The `show_ui` Tool as a Visual Commit

The `show_ui` tool is the boundary between the voice agent's reasoning and the visual surface. In the reference implementation, the tool receives a `content` string from the agent. That content is not final UI code. It is structured intent: the data, labels, comparison points, form fields, or product details the agent wants shown.

From there, the visual path runs independently:

```txt
show_ui(content)
  -> abort previous UI stream
  -> start a LiveKit text stream on topic "genui"
  -> call Thesys with the structured content
  -> write streamed UI chunks to the topic
  -> return immediately so the agent can keep speaking
```

That immediate return matters. The tool returns a short message telling the voice agent that the UI is loading on screen. The agent can continue the conversation while the visual result streams in. The user hears forward motion instead of silence, and the UI still arrives progressively.

The abort behavior is just as important. A voice conversation changes direction quickly. If the user interrupts a hotel search and asks for restaurants instead, the old visual stream should not finish and overwrite the new state. The reference `show_ui` tool cancels any previous in-flight stream before starting a new one. That makes the visual panel behave like the latest committed turn, not an uncontrolled queue of stale screens.

For production systems, this pattern should be made explicit:

- every generated UI stream should belong to a turn id;
- only the latest non-superseded turn should update the primary panel;
- interrupted turns should close or mark their streams as superseded;
- action events should include enough context to prove which visual state they came from.

The demo shows the core shape. A production app should add the identifiers and persistence around it.

## The Front End Is an Accumulator, Not a Parser Dump

On the browser side, the LiveKit room registers a text-stream handler for the `genui` topic. Each incoming chunk is appended to an accumulator, and the accumulated content is stored as state. While chunks are arriving, `isStreaming` is true. When the stream finishes, `isStreaming` flips false.

That sounds simple, but it is an important UI contract. The front end is not waiting for a complete document and then swapping in a finished widget. It is maintaining the best current visual state for this turn. The generated UI component receives both the current response and the streaming flag.

This is exactly where generative UI is different from a normal voice transcript. A transcript is a log of words. The visual panel is a structured working surface. It can show skeletons while the stream starts, render partial content while the response grows, and then become interactive when the turn is ready.

There are three states worth separating:

1. `isStreaming`: the visual response is still being generated.
2. `isProcessingAction`: the user clicked or submitted something and the agent is handling it.
3. `isAgentReady`: the voice agent is connected and able to receive input.

The reference UI separates those states. It can show an empty "getting ready" view before the agent is usable, a skeleton while generated UI or an action is in progress, and the rendered component when content is available. That state split prevents a common voice-agent failure mode: the agent sounds available while the interface is not ready, or the UI looks actionable while the system is still processing the previous action.

## Actions Need Confirmation Semantics

The visual surface becomes much more valuable when it can send actions back into the voice loop. In the reference front end, `C1Component` receives an `onAction` callback. If the action type is `open_url`, the browser opens the URL with `noopener,noreferrer`. For other actions, the handler looks for an `llmFriendlyMessage`, sets `isProcessingAction`, and sends that message back through LiveKit chat.

That is a compact version of a powerful pattern: the UI can continue the conversation without forcing the user to translate a click into speech.

But action handling is also where voice agents need discipline. A button labeled "Book this" or "Approve" should not become an unreviewed natural-language message with unclear side effects. The visual commit log should make action boundaries visible:

- what action will be taken;
- what data will be sent;
- whether the action is reversible;
- whether the user is approving, previewing, or merely asking for more detail;
- whether the action belongs to the current visual turn.

For low-risk actions, a click can simply continue the conversation. For high-risk actions, the visual UI should require a second confirmation, and the spoken agent should summarize only the key consequence: "This will submit the selected policy change for approval." The detailed payload belongs on screen.

OpenUI-style generated interfaces are useful here because the model can present a structured review surface instead of a paragraph. The application still owns the action handler and policy checks. The model proposes the interface; the app decides what a button is allowed to do.

## What To Render, What To Say

The most common mistake in multimodal agents is making the voice and UI compete. If both channels contain the same information, the user has to decide which one to trust. A better rule is:

- voice is for orientation, pacing, and reassurance;
- UI is for data, options, forms, state, and decisions.

For a product comparison, the agent might say: "I found three good matches. The first is cheapest, the second has the best battery, and the third is the lightest." The UI should show the full card grid, ratings, prices, tradeoffs, and action buttons.

For a form, the agent might say: "I need a few preferences before I narrow this down." The UI should show the fields, default values, constraints, and a submit action.

For a dashboard, the agent might say: "The main issue is conversion drop-off after the pricing step." The UI should show the funnel, deltas, and affected segments.

For an approval, the agent might say: "Please review the generated change before I send it." The UI should show the diff, the target system, and the confirmation control.

This is also better for accessibility and interruption. If the user misses the spoken sentence, the visual state remains. If the user interrupts, the app can supersede the stream. If the user cannot or does not want to speak, the UI action can continue the loop.

## Production Checklist

A LiveKit plus OpenUI voice agent is not production-ready just because it can speak while rendering a card. The architecture needs a few explicit contracts.

Turn identity: Every visual stream should be tied to a voice turn. Store the user utterance, the short spoken narration, the structured content sent to `show_ui`, and the resulting UI stream id. This makes debugging possible.

Supersession: When a new turn starts, decide whether the old visual state remains visible, becomes history, or is replaced. Do not let an old stream finish into the active panel after the conversation has moved on.

Action provenance: Every UI action should identify the visual turn and component that produced it. This prevents stale buttons from acting on a newer state.

Risk levels: Separate harmless continuation actions from irreversible actions. Opening a URL, asking for more details, and approving a transaction should not share the same confirmation path.

Fallbacks: If visual generation fails, the voice agent should still be able to continue with a short explanation and a simpler text or form fallback.

Streaming UX: Show skeletons or partial states honestly. Avoid making the UI look complete before it is interactive.

Observability: Log stream start, first chunk, stream close, abort, action click, and agent response. Voice-agent bugs are often timing bugs, and timing bugs need traces.

Security: Treat generated UI as a proposal. The app's component library, renderer, and action handlers should enforce what can render and what can execute.

## The Real Payoff

The best voice agents will not be audio-only assistants with a decorative panel. They will be conversational control surfaces where speech captures intent and generated UI preserves state.

LiveKit gives the agent a realtime room to listen, speak, and exchange messages. OpenUI gives the agent a way to turn structured intent into an inspectable interface. Together, they let a user say what they want, hear a short response, and then work with the result on screen.

That is the shift: the screen is not a transcript. It is the commit log of the conversation.

When a voice agent can leave behind a table, a form, a dashboard, or a reviewed action payload, the user no longer has to hold the whole interaction in memory. The interface carries the state. The voice carries the flow. The product becomes easier to trust.
