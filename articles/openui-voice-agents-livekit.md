# OpenUI for Voice Agents: Pairing LiveKit with Generative UI for Real-Time Visual Feedback

Most voice agents are one-dimensional. The user speaks, the agent speaks back. All information passes through a single audio channel — fine for "set a timer for five minutes," useless for "compare three health insurance plans."

The limitation isn't intelligence. It's output bandwidth. A voice agent that knows the answer to a complex question still can't effectively communicate it through speech alone. Try listening to someone read a comparison table out loud. You'll forget the first column by the time they reach the third.

The fix is obvious once you see it: let the agent show things while it talks. Not a static screen that updates after the conversation — a live visual layer that renders in parallel with speech. The agent says "here are your three options" and a comparison card appears simultaneously.

This is what you get when you pair LiveKit's real-time voice infrastructure with OpenUI's generative UI rendering. LiveKit handles the voice pipeline — speech-to-text, LLM reasoning, text-to-speech. OpenUI handles the visual output — structured components that stream onto the screen while the agent is still talking.

Thesys published a working reference implementation at [thesysdev/voice-agent-generativeui](https://github.com/thesysdev/voice-agent-generativeui). This article breaks down how it works.

## The Architecture

The system has two parallel output paths from a single LLM:

```
User speaks
    ↓
LiveKit (STT → text)
    ↓
LLM (reasoning + tool calls)
    ├── Speech path: text → TTS → audio to user
    └── Visual path: show_ui tool → Thesys C1 → streamed UI to browser
```

The LLM decides when visual output is appropriate and calls a `show_ui` tool with structured content. That content gets sent to Thesys's C1 model, which generates openui-lang code that streams to the browser and renders as interactive React components.

The critical design choice: the visual path runs **in the background**. When the LLM calls `show_ui`, it doesn't wait for the UI to finish rendering. It immediately gets back a response saying "UI is loading on screen" and continues generating speech. The user hears the agent talking while watching components appear on screen.

## How the Voice Agent Works

The agent is built on LiveKit's `@livekit/agents` SDK. It's a `voice.Agent` subclass with tools:

```typescript
import { voice, llm } from "@livekit/agents";

class VoiceAgent extends voice.Agent {
  constructor(room: any) {
    const showUI = new ShowUITool(room);

    super({
      instructions: buildPrompt(),
      tools: {
        show_ui: showUI.tool,
        web_search: llm.tool({ /* ... */ }),
        search_images: llm.tool({ /* ... */ }),
      },
    });
  }
}
```

LiveKit's voice agent handles the full pipeline: receiving audio from the user, running speech-to-text, passing the transcript to the LLM, and converting the LLM's text response back to speech. The tools are where custom behavior lives.

The `show_ui` tool is the bridge between voice and vision.

## The show_ui Tool: Voice-to-Visual Bridge

Here's the core of how visual generation works, based on the reference implementation:

```typescript
import { llm } from "@livekit/agents";
import OpenAI from "openai";
import { z } from "zod";

export class ShowUITool {
  private abortController: AbortController | null = null;
  private readonly thesysClient: OpenAI;

  constructor(private readonly room: any) {
    this.thesysClient = new OpenAI({
      baseURL: "https://api.thesys.dev/v1/embed",
      apiKey: process.env.THESYS_API_KEY,
    });
  }

  get tool() {
    return llm.tool({
      description:
        "Display rich visual UI to the user. Pass the COMPLETE " +
        "structured content you want to visualize.",
      parameters: z.object({
        content: z.string().describe(
          "The full structured content to display visually."
        ),
      }),
      execute: async ({ content }) => {
        // Cancel any previous in-flight stream
        this.abortController?.abort();
        this.abortController = new AbortController();
        const { signal } = this.abortController;

        // Stream the UI in the background
        (async () => {
          const writer = await this.room.localParticipant.streamText({
            topic: "genui",
          });

          const stream = await this.thesysClient.chat.completions.create(
            {
              model: "c1/google/gemini-3-flash/v-20251230",
              messages: [
                { role: "system", content: SYSTEM_PROMPT },
                { role: "user", content },
              ],
              stream: true,
            },
            { signal },
          );

          for await (const chunk of stream) {
            if (signal.aborted) break;
            const delta = chunk.choices[0]?.delta?.content;
            if (delta) await writer.write(delta);
          }
          await writer.close();
        })();

        // Return immediately — don't block speech generation
        return "UI is loading on screen. Tell the user what you're showing them.";
      },
    });
  }
}
```

Three things to notice:

1. **Immediate return.** The tool returns a string right away, so the LLM can generate its spoken response without waiting for the UI. The actual UI generation happens in a fire-and-forget async block.

2. **LiveKit text streams.** `room.localParticipant.streamText({ topic: "genui" })` opens a real-time text channel on the LiveKit room. The browser receives chunks as they arrive — same as receiving audio, but for UI code.

3. **Abort on new request.** If the user asks a follow-up before the current UI finishes rendering, the previous stream gets aborted. Only one visual context at a time.

The system prompt for the C1 model is concise:

```
You are being used in tandem with a voice agent.
The voice agent LLM decides what to show on the screen and calls you
with the content to generate a visual UI.
The content will be passed as the user message and your job is to
convert that content into a visually appealing and interactive UI component.
```

So the voice agent LLM is the "brain" that decides **what** to show. The C1 model decides **how** to render it as structured UI components.

## The Browser Side: Receiving and Rendering

On the frontend, a Next.js app connects to the same LiveKit room. It registers a handler for the `genui` text stream topic:

```tsx
import { C1Component } from "@thesysai/genui-sdk";

function GenUIPanel({ content, isStreaming, onAction }) {
  return (
    <C1Component
      c1Response={content}
      isStreaming={isStreaming}
      onAction={onAction}
    />
  );
}
```

The `VoiceUI` component manages the stream lifecycle:

```tsx
useEffect(() => {
  const room = session.room;
  if (!room) return;

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

  room.registerTextStreamHandler("genui", handleGenUI);
  return () => {
    try { room.unregisterTextStreamHandler("genui"); } catch {}
  };
}, [session.room]);
```

Each chunk from the server appends to an accumulator string. `C1Component` receives the growing string and progressively renders UI as the openui-lang code streams in. The user sees components appearing while the agent is still talking — a card header first, then rows of data, then action buttons.

## Bidirectional: UI Actions Back to Voice

The visual layer isn't read-only. When the user clicks a button or submits a form in the generated UI, the action flows back to the voice agent through LiveKit's chat channel:

```tsx
const handleAction = useCallback(
  (event: { type?: string; params?: Record<string, unknown> }) => {
    switch (event.type) {
      case "open_url":
        window.open(event.params?.url as string, "_blank");
        break;
      default: {
        const message = event.params?.llmFriendlyMessage as string;
        if (message) {
          sendChatMessage(message);
        }
        break;
      }
    }
  },
  [sendChatMessage],
);
```

The `llmFriendlyMessage` is a text description of what the user selected — "User selected the Premium plan at $29/month" — sent as a chat message that the voice agent receives and responds to. The conversation continues naturally: the user clicks a card, the agent acknowledges the selection and asks the next question.

This creates a multimodal loop: voice in → visual + voice out → click in → voice out.

## The Prompt Strategy

The voice agent's system prompt is designed around aggressive visual output. From the reference implementation:

> "You should use show_ui aggressively — any time information would be better seen than heard, put it on screen and give a brief spoken summary."

The prompt categorizes when to trigger visual output:

- **Data visualizations** — charts, metrics, trends. "Pass the actual data points and specify the chart type."
- **Forms** — collecting structured input. "Any time you need 2+ pieces of information from the user, show a form instead of asking questions one by one."
- **Structured comparisons** — feature breakdowns, pros/cons, side-by-side tables.
- **Product catalogs** — cards with images, prices, ratings.
- **Detail pages** — rich single-item views with specs and reviews.

The key instruction: "Keep voice responses short and natural. Avoid reading long lists aloud — show them visually instead and summarise with a couple of sentences."

This is the UX insight that makes the pattern work. The voice channel carries context and narrative ("Here are three hotels that match your criteria, the second one has the best reviews"). The visual channel carries data (the actual hotel cards with images, prices, and ratings). Neither channel tries to do the other's job.

## Two Agent Modes

The reference implementation supports two modes that handle tool narration differently:

**Realtime mode**: The LLM speaks a short sentence before calling any tool ("Let me pull that up for you"), then calls the tool. Natural but requires the model to self-narrate.

**Pipeline mode**: Tools accept a `narration` parameter. The agent speaks the narration via TTS while the tool executes in parallel. More reliable timing — the narration always plays, even if tool execution is slow.

```typescript
function makeTool(mode, session, name, config) {
  if (mode === "pipeline" && session) {
    return withNarration(session, name, config);
  }
  return llm.tool(config);
}
```

Pipeline mode wraps each tool so that calling it automatically triggers speech synthesis of the narration text while the actual tool logic runs. The user never sits in silence waiting for a web search to complete.

## Where This Gets Interesting

The voice + visual pattern opens use cases that neither channel handles well alone:

**Customer support with product lookup.** The agent asks what's wrong, searches the knowledge base, and displays the relevant troubleshooting steps as a visual stepper while verbally walking the user through the first step. If the user says "skip to step 3," the visual updates.

**Financial advising.** The agent asks about investment goals and risk tolerance, then shows a portfolio allocation pie chart and comparison table of fund options. The user clicks a fund to hear more about it.

**Medical triage.** The agent asks about symptoms, shows a body diagram highlighting relevant areas, displays a severity assessment form, and verbally explains what each option means.

**Travel planning.** "I want to go somewhere warm in March for under $2000." The agent shows a grid of destination cards with flight prices, weather data, and hotel options. The user taps a destination and the agent starts drilling into specifics.

In all of these, the voice agent without visual output would need to read lists, spell out details, and repeat information the user forgot. The visual layer makes the agent dramatically more useful for anything involving structured data, multiple options, or persistent reference information.

## Running the Reference Implementation

The [thesysdev/voice-agent-generativeui](https://github.com/thesysdev/voice-agent-generativeui) repo is a full working example. It's a Next.js app with a separate LiveKit agent process:

```
voice-agent-generativeui/
├── livekit-agent/          # Node.js agent (LiveKit + tools)
│   ├── src/agent.ts        # VoiceAgent class
│   ├── src/tools/show-ui.ts  # The show_ui bridge
│   └── src/prompt.ts       # System prompt builder
├── src/
│   ├── app/page.tsx        # Next.js entry
│   └── lib/components/
│       ├── VoiceUI.tsx     # Main voice + visual UI
│       └── GenUIPanel.tsx  # C1Component wrapper
```

You need API keys for LiveKit, Thesys (C1), and Exa (web search). The agent connects to a LiveKit room, the browser joins the same room, and the text stream channel carries the generated UI between them.

The architecture is intentionally decoupled. The voice agent is a separate process that could run on a server, edge function, or anywhere with a LiveKit connection. The browser only needs to render what arrives on the stream. You could swap the voice agent's LLM, change the visual generation model, or replace the search tools without touching the frontend.

## The Bigger Picture

Voice agents are converging on multimodal output. The question is how the visual layer gets generated — hand-coded templates for every possible response, or generated on the fly from the same LLM reasoning that produces speech.

The LiveKit + OpenUI pattern chooses generation. The voice agent's LLM decides what's worth showing, describes it in structured text, and a specialized model converts that into interactive components. No templates to maintain. No hardcoded screens for each use case. The visual output is as dynamic as the conversation.

The tradeoff is latency — there's a generation step between "agent decides to show something" and "user sees it." The reference implementation mitigates this with streaming (components appear progressively) and the fire-and-forget pattern (speech continues while UI loads). In practice, the visual output appears within a second of the agent deciding to show it, which feels natural when the agent is simultaneously narrating what's appearing.

If you're building voice agents and your users need to see structured information — not just hear it — this is the architecture to start from.
