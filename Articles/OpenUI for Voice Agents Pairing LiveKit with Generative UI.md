# OpenUI for Voice Agents: Pairing LiveKit with Generative UI for Real-Time Visual Feedback

Voice agents are becoming good enough that the bottleneck is no longer only speech quality.

The harder problem is memory. Audio disappears as soon as it is spoken. If an agent compares three pricing plans, summarizes an incident, or walks through a product search, the user has to hold the important details in their head while the conversation keeps moving.

That is fine for simple answers. It breaks down for structured work.

A useful voice agent should be able to speak and show. When the answer contains a comparison, it should render a table. When the answer contains steps, it should render a checklist. When the answer contains candidates, it should render cards. When the user needs to choose, it should render actions that can continue the conversation.

This is where LiveKit and OpenUI fit naturally together. LiveKit gives you the real-time audio session, agent lifecycle, and room transport. OpenUI gives the model a constrained way to produce interactive UI instead of plain text. Together, they let a voice agent talk while a visual surface streams onto the screen.

This article walks through that pattern using the Thesys voice-agent generative UI demo as the reference architecture.

## The Product Problem

Most voice agents still treat the screen as secondary. The agent speaks, the transcript scrolls, and maybe a few status indicators show that the system is listening or thinking.

That design wastes a useful channel.

Consider a voice agent for travel planning. A user asks:

> Compare three hotels near the conference venue and show me which one is best for walking distance, price, and cancellation policy.

A voice-only response has to serialize everything:

- Hotel A is cheaper, but farther away
- Hotel B is closest, but has a strict cancellation policy
- Hotel C is more expensive, but includes breakfast and flexible cancellation

The user hears the first option, then the second, then the third, and then asks the agent to repeat the first one. The agent is not necessarily wrong. The interface is wrong for the task.

The same happens in support workflows, analytics, scheduling, onboarding, and product comparison. Once the answer has structure, speech alone becomes a narrow output format.

The goal is not to replace voice with UI. The goal is to make voice and UI cooperate:

- Voice explains what is happening
- UI preserves the structure
- Actions let the user continue without restating intent

## The Architecture At A Glance

The demo is split into two parts:

- A LiveKit agent that listens, reasons, calls tools, and streams generated UI
- A Next.js frontend that connects to the room, receives the UI stream, and renders it with the Thesys GenUI SDK

The important idea is that generated UI is not returned as a normal chat message. It travels over a dedicated LiveKit text stream topic.

The flow looks like this:

1. The user speaks to the voice agent.
2. The agent decides that the answer needs a visual surface.
3. The agent calls a `show_ui` tool with structured content.
4. The tool sends that content to the Thesys embed API.
5. The generated OpenUI response streams back chunk by chunk.
6. The tool writes those chunks to a LiveKit text stream with the topic `genui`.
7. The frontend listens for `genui`, accumulates the stream, and renders it with `C1Component`.
8. The voice agent returns immediately so it can keep speaking while the interface appears.

That last part matters. The UI stream is started in the background. The voice LLM does not wait for a full interface payload before responding. The experience feels like a multimodal conversation instead of a turn-based form generator.

## The Agent Side: A Tool That Streams UI

The core server-side piece is the `ShowUITool` in the demo agent.

Conceptually, it does three jobs:

- Defines when the agent should use visual UI
- Converts the agent's structured content into an OpenUI stream
- Publishes that stream into the LiveKit room

The tool description is intentionally direct. It tells the voice model to call the tool for comparisons, lists, structured data, cards, and similar visual output. The input is a single `content` string, but that string should be complete and specific enough for the UI model to build a useful surface.

Here is the shape of the tool:

```ts
return llm.tool({
  description:
    "Display rich visual UI to the user. Pass the COMPLETE structured content you want to visualize.",
  parameters: z.object({
    content: z.string().describe(
      "The full structured content to display visually. Be detailed and specific.",
    ),
  }),
  execute: async ({ content }) => {
    // Start UI streaming work here.
    return "UI is loading on screen. Tell the user in 1-2 natural sentences what you are showing them.";
  },
});
```

The interesting part is inside `execute`.

First, the tool cancels any previous in-flight UI stream:

```ts
this.abortController?.abort();
this.abortController = new AbortController();
const { signal } = this.abortController;
```

That is a practical detail, but an important one. In a real conversation, users interrupt, clarify, and change direction. If the agent is still streaming an old comparison table while the user asks a new question, the screen becomes misleading. Canceling the previous stream keeps the visible UI aligned with the current turn.

Then the tool opens a LiveKit text stream:

```ts
writer = await this.room.localParticipant.streamText({
  topic: "genui",
});
```

The topic name is the contract between the agent and frontend. Audio can continue over the normal LiveKit media path while UI chunks travel over this named text stream.

Next, the tool calls the Thesys embed API using an OpenAI-compatible client:

```ts
const stream = await this.thesysClient.chat.completions.create(
  {
    model: THESYS_MODEL,
    messages: [
      { role: "system", content: THESYS_SYSTEM_PROMPT },
      { role: "user", content },
    ],
    stream: true,
  },
  { signal },
);
```

The system prompt is short but specific: the UI model is being used alongside a voice agent, and its job is to turn the voice agent's content into a visually appealing interactive component.

Finally, each streamed delta is written into the LiveKit room:

```ts
for await (const chunk of stream) {
  if (signal.aborted) break;
  const delta = chunk.choices[0]?.delta?.content;
  if (delta) {
    await writer.write(delta);
  }
}

await writer.close();
```

The tool returns immediately after starting this background work. That design keeps the spoken response responsive while the visual response renders progressively.

## The Frontend Side: Listen For `genui`

On the frontend, the generated UI stream is handled inside the main voice UI component.

The important state is small:

```ts
const [genUIContent, setGenUIContent] = useState("");
const [isStreaming, setIsStreaming] = useState(false);
```

When the LiveKit room is available, the frontend registers a text stream handler for the same `genui` topic used by the agent:

```ts
room.registerTextStreamHandler("genui", handleGenUI);
```

The handler accumulates chunks as they arrive:

```ts
const handleGenUI = (reader: AsyncIterable<string>) => {
  setIsStreaming(true);
  setGenUIContent("");
  let acc = "";

  (async () => {
    try {
      for await (const chunk of reader) {
        acc += chunk;
        setGenUIContent(acc);
      }
    } finally {
      setIsStreaming(false);
    }
  })();
};
```

That accumulated string becomes the input to the renderer:

```tsx
<GenUIPanel
  content={genUIContent}
  isStreaming={isStreaming}
  isProcessingAction={isProcessingAction}
  isAgentReady={isAgentReady}
  onAction={handleAction}
/>
```

Inside the panel, the actual rendering is handled by the Thesys component:

```tsx
<C1Component
  c1Response={content}
  isStreaming={isStreaming}
  onAction={onAction}
/>
```

This keeps the application boundary clean. The LiveKit component manages connection state, audio session lifecycle, transcript state, and incoming UI streams. The GenUI panel renders the model-generated interface.

## Actions Close The Loop

Generated UI becomes much more useful when it can continue the conversation.

In the demo, UI actions are sent back into the chat path. If the generated component emits an action like `continue_conversation`, the frontend extracts an `llmFriendlyMessage` and sends it as a chat message:

```ts
const message = event.params?.llmFriendlyMessage as string | undefined;
if (message) {
  setIsProcessingAction(true);
  sendChatMessage(message);
}
```

That means a generated comparison table can include actions such as:

- "Compare only flexible cancellation"
- "Show the cheapest option"
- "Explain the tradeoff"
- "Book this one"

The user can click instead of restating a long instruction by voice. The agent receives a clean follow-up message and can continue the same loop: speak, call tools, stream UI, accept actions.

This is the difference between showing a decorative card and building a multimodal agent interface.

## Choosing Between Pipeline And Realtime Agents

The demo supports two agent modes.

In pipeline mode, the agent is built from separate speech-to-text, language model, text-to-speech, and voice activity detection pieces. In realtime mode, it uses OpenAI's realtime model path.

That choice changes the audio stack, but not the UI pattern. The `show_ui` tool remains the bridge between agent reasoning and visual rendering.

For product teams, that separation is useful. You can change voice infrastructure, model providers, or speech settings while keeping the UI stream contract stable:

- The backend publishes generated UI chunks on `genui`
- The frontend listens on `genui`
- The renderer turns the accumulated stream into interface

That small contract makes the architecture easier to reason about.

## What To Show Visually

Not every answer needs generated UI.

A good rule of thumb: call `show_ui` when the answer contains structure the user may need to inspect, compare, remember, or act on.

Strong candidates:

- Product comparisons
- Search results
- Itineraries
- Pricing breakdowns
- Support ticket summaries
- Data snapshots
- Forms and confirmation steps
- Step-by-step troubleshooting

Weak candidates:

- Short factual answers
- Conversational acknowledgements
- Simple yes/no confirmations
- Sensitive data that should stay out of persistent UI
- Anything where the model lacks trusted source data

The best voice agents will not generate UI constantly. They will generate it at the moments when the screen makes the conversation easier to understand.

## Practical Guardrails

Pairing voice with generated UI introduces a few product and engineering concerns.

First, keep the data source trustworthy. The `show_ui` tool should visualize content the agent already has permission to show. If the UI depends on external data, fetch that data through tools with clear permissions and then pass the result into the UI generation step.

Second, cancel stale streams. The demo's abort controller is a good pattern. Voice interactions are interruptible by nature, so old visual output should not keep arriving after the conversation has moved on.

Third, make loading state visible. Streaming UI is powerful because the user sees progress. The frontend should distinguish between empty, loading, streaming, complete, and action-processing states.

Fourth, preserve transcript and UI together. The transcript explains why a surface appeared. The surface preserves the structured result. Users need both when they look back at a conversation.

Fifth, log generated UI payloads. In production, you will want to inspect which prompts create useful interfaces, which ones confuse users, and which actions drive follow-up turns.

## A Minimal Build Plan

If you are adding generative UI to an existing LiveKit voice agent, start small.

1. Add a `show_ui` tool to the agent.
2. Give it one clear input: complete structured content to visualize.
3. Inside the tool, call the OpenUI or Thesys generation endpoint with streaming enabled.
4. Publish each streamed chunk into the LiveKit room on a dedicated text topic.
5. In the frontend, register a text stream handler for that topic.
6. Accumulate the stream in state.
7. Render it with a GenUI component.
8. Wire UI actions back into the agent as chat messages.

You do not need to rebuild the whole voice experience at once. Pick one workflow where speech is obviously too linear: comparing options, summarizing a case, filling a form, or showing ranked results.

Once that works, measure whether users ask fewer repeat questions and complete the workflow faster.

## Why This Pattern Matters

Voice agents make software feel more direct. Generative UI makes AI output more usable. The combination is stronger than either part alone.

A voice-only agent can be fast but hard to inspect. A UI-only agent can be rich but slow to navigate. A multimodal agent can explain the answer aloud while showing the structure visually and letting the user act without breaking the flow.

LiveKit provides the real-time room and agent infrastructure. OpenUI provides the generated interface layer. The bridge between them can be as small as a streamed text topic and a rendering component.

That is the practical takeaway: multimodal agents do not require a completely new application architecture. They require a clear contract between speech, tools, generated UI, and user actions.

When that contract is in place, the voice agent stops being a talking transcript and starts becoming a real working surface.

## References

- OpenUI repository: https://github.com/thesysdev/openui
- OpenUI documentation and playground: https://www.openui.com/
- Thesys voice-agent generative UI demo: https://github.com/thesysdev/voice-agent-generativeui
- LiveKit Agents documentation: https://docs.livekit.io/agents/
