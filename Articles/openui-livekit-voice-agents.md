# OpenUI for Voice Agents: Pairing LiveKit with Generative UI for Real-Time Visual Feedback

Voice agents are moving quickly from novelty demos into real product surfaces. LiveKit makes it practical to build low-latency agents that can listen, speak, join rooms, and coordinate realtime media like a normal participant. That solves the audio loop. But most voice agents still leave users with a familiar problem: once something has been said, it disappears into time.

That is fine for short exchanges. It is not fine when the agent compares options, explains a workflow, collects details, triages a support case, or walks through a multi-step decision. Users need something they can scan, correct, and act on while the conversation continues. This is where OpenUI fits naturally: LiveKit handles realtime voice and media transport, while OpenUI renders structured, streaming interface output next to the conversation.

The result is not a chatbot with a prettier transcript. It is a multimodal agent loop: the user speaks, the agent replies by voice, and the application simultaneously generates cards, forms, tables, timelines, and status panels that make the answer usable.

## Why voice alone is not enough

Voice is powerful because it is fast and natural. A user can ask a question while driving a workflow, looking at another screen, or holding context in their head. But voice is also linear. It is difficult to skim. It is hard to compare. It is easy to miss details.

Consider a voice support agent handling a billing dispute. The spoken answer might include invoice dates, policy rules, refund options, confidence levels, and a recommended next step. If that information only exists in audio, the user has to remember it or ask the agent to repeat it. A visual companion can make the same interaction much safer: a timeline of charges, a policy match card, a refund recommendation, and a confirmation form can stay on screen while the agent explains them.

The same pattern applies to travel planning, sales qualification, healthcare intake, onboarding, education, and internal operations. The more structured the task, the more voice benefits from generated UI.

## The architecture: LiveKit for realtime, OpenUI for structure

LiveKit Agents lets a Python or Node.js program join a LiveKit room as a realtime participant. The agent can receive audio, run speech-to-text, call an LLM, synthesize speech, and publish audio back to the room. The framework is designed for realtime media pipelines and can be deployed on LiveKit Cloud or custom infrastructure.

OpenUI solves a different layer of the problem. It provides a compact, streaming-first language for model-generated interface output, a React runtime, built-in component libraries, and chat/app surfaces that can render structured UI progressively. Instead of asking the model to produce arbitrary HTML, an application can expose approved components and let the model compose them within a controlled design system.

Together, the split is clean:

- LiveKit carries the realtime conversation.
- The agent decides what should be said and what should be shown.
- OpenUI renders the visual state as the answer streams.
- The frontend keeps voice, transcript, and generated UI in sync.

A useful mental model is “one agent response, two channels.” The audio channel is optimized for natural conversation. The UI channel is optimized for memory, comparison, validation, and action.

## Example: a voice-driven research assistant

Imagine a user asks: “Compare these three CRM options for a five-person agency and tell me what to choose.”

A voice-only agent can describe the tradeoffs. A LiveKit + OpenUI agent can do more:

1. Speak a concise summary: “For a small agency, I would shortlist Option A and Option B. Option C is likely too heavy.”
2. Render a comparison table with pricing, setup time, integrations, and risk flags.
3. Add a recommendation card with the strongest option and why.
4. Show a follow-up form asking which tools the agency already uses.
5. Update the table live when the user answers by voice.

The user can listen while also seeing the decision structure. They can interrupt naturally, ask “sort by setup time,” or say “remove the enterprise option,” and the UI can update without forcing them to parse a long transcript.

## Minimal implementation pattern

A practical implementation does not need to start with a huge component system. Start with a small set of high-value UI primitives:

- `SummaryCard` for the main answer.
- `ComparisonTable` for options and tradeoffs.
- `ActionChecklist` for next steps.
- `InputForm` for details the agent needs from the user.
- `StatusPanel` for progress, confidence, and pending actions.

On the LiveKit side, the agent listens to the room and processes user speech. When the LLM creates a response, the application asks for two coordinated outputs: a short spoken response and an OpenUI-compatible visual response. The spoken response should be concise because the UI carries detail. The visual response should be structured because the user can inspect it at their own pace.

The frontend subscribes to the room for audio and transcript events, then passes the generated OpenUI stream into the renderer. As each component arrives, the interface updates progressively. This matters because realtime voice users expect the system to feel alive; they should not wait for a full dashboard to be generated before seeing anything.

## Handling interruptions and state

Voice agents must handle interruptions. If the user cuts in with “actually, make that for a ten-person team,” the system should update both channels. The agent may stop speaking, revise the recommendation, and regenerate the relevant UI components.

This is where a visual state model becomes valuable. Instead of treating every turn as a new transcript blob, the app can keep a structured state object:

- current user goal,
- known constraints,
- selected options,
- generated components,
- pending confirmations,
- completed actions.

OpenUI can render the current state while LiveKit keeps the conversation moving. The user sees what changed, not just what was said.

## Guardrails for generated visual feedback

The main risk with generative UI is over-generation. A voice agent should not fill the screen with decorative components just because it can. The UI should appear when it reduces cognitive load, prevents errors, or helps the user act.

Good guardrails include:

- Use a fixed component vocabulary rather than arbitrary HTML.
- Validate generated UI before rendering it.
- Keep spoken output short when visual detail is available.
- Require explicit confirmation for destructive or financial actions.
- Clearly mark confidence, assumptions, and missing data.
- Preserve accessibility: keyboard navigation, labels, contrast, and screen-reader-friendly structure.
- Keep private or sensitive data scoped to the active session and product rules.

A strong LiveKit + OpenUI implementation feels like a calm copilot, not a slot machine of widgets.

## Where this pattern is strongest

The best early use cases are tasks where voice creates speed but visual structure creates trust:

- Customer support: refund decisions, account timelines, escalation forms.
- Healthcare intake: symptom summaries, triage questions, visit prep checklists.
- Sales: qualification flows, objection handling, account summaries.
- Education: spoken tutoring with generated diagrams, quizzes, and progress cards.
- Developer tools: voice-driven debugging with stack traces, failing tests, and command suggestions.
- Operations: incident response summaries, responsible teams, timelines, and next actions.

These are not just “voice chat” products. They are realtime work surfaces.

## A simple build plan

A focused first prototype can be built in four steps.

First, start from a LiveKit voice agent starter so the audio loop works: room connection, speech input, model response, and speech output. Keep the first skill narrow, such as “summarize and compare options.”

Second, define five OpenUI components that match the workflow. Do not build a universal UI generator. Give the model a constrained vocabulary that maps to real user needs.

Third, ask the model for dual output: a short response for speech and a structured OpenUI response for the visual panel. Treat the visual panel as the durable state of the turn.

Fourth, test with interruption scenarios. The prototype is only convincing if the user can revise the task by voice and watch the visual state update without breaking the conversation.

## Conclusion

LiveKit gives voice agents the realtime media foundation they need. OpenUI gives those agents a way to show durable, interactive, structured feedback while they speak. The combination turns voice from a linear conversation into a usable work surface.

That matters because the future of agents is not only better answers. It is better interfaces around those answers: interfaces that appear at the right moment, preserve context, support action, and reduce the effort required to turn a spoken request into a completed task.

For teams building voice agents, the next step is simple: stop treating the screen as a transcript container. Treat it as an adaptive interface that can be generated alongside speech.
