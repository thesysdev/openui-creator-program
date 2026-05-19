# OpenUI for Voice Agents: Pairing LiveKit with Generative UI for Real-Time Visual Feedback

Your voice agent just nailed the answer — a perfect comparison of three SaaS pricing tiers. It speaks the results aloud: "Plan A costs $29 per month, Plan B is $79, and Plan C is $199. Plan A includes 5 users, Plan B includes 25..."

By the time it finishes, the user has forgotten Plan A's price. They ask the agent to repeat it. This is the voice-only trap: audio is serial, ephemeral, and hostile to anything with more than three data points.

The fix is a second output channel. While the agent speaks, it simultaneously renders structured UI — comparison tables, forms, charts, product cards — on screen. The user hears the summary and scans the details at their own pace.

[Thesys's reference implementation](https://github.com/thesysdev/voice-agent-generativeui) demonstrates exactly this pattern using [LiveKit](https://livekit.io) for voice and [OpenUI](https://www.openui.com/) for generative visual output. This article walks through how it works, how to build your own, and what to watch out for in production.

## The Dual-Output Architecture

The system has two parallel output paths from a single LLM call:

```
User speaks into microphone
         │
         ▼
LiveKit room ──── STT (speech-to-text)
         │
         ▼
    LLM reasoning
    ┌────┴────┐
    ▼         ▼
Speech path  Visual path
    │         │
 TTS engine   show_ui tool
    │         │
 Audio to     Thesys C1 model
 user's       │
 speakers     OpenUI Lang stream
              │
              React components
              on screen
```

The critical design decision: these paths run **concurrently**, not sequentially. The LLM calls `show_ui` as a tool, which kicks off the visual render in the background. The LLM immediately continues generating its spoken response. The user hears "Here are the three plans" and simultaneously watches a comparison card appear.

This is not a demo trick. It's a fundamental architecture for agents that handle complex information — any time the answer is better seen than heard, the visual path activates alongside the audio path.

## Two Agent Modes: Pipeline vs Realtime

The reference implementation supports two modes, selectable from the UI before starting a session. Understanding the difference matters for what you build.

**Pipeline mode** chains three separate models:

```
User audio → Deepgram STT → text
text → Gemini Flash (LLM) → response + tool calls
response → Inworld TTS → audio back to user
```

Each step waits for the previous one. Latency is higher, but you can swap each component independently — different STT for different languages, a cheaper LLM for simple queries, a specific TTS voice for your brand. Tool narration is injected programmatically via `session.say()` so the user hears something while the tool runs.

**Realtime mode** uses a single multimodal model:

```
User audio → OpenAI gpt-realtime → audio back to user + tool calls
```

The model natively consumes and produces audio — no transcription or synthesis step. Latency is significantly lower and the voice has better emotional nuance (tone, hesitation, emphasis). The trade-off is provider lock-in — you're tied to OpenAI for the entire voice pipeline. Narration before tool calls is handled by prompting the model to speak before acting.

Both modes share the same `VoiceAgent` class, the same tools (`show_ui`, `web_search`, `search_images`), and the same system prompt. Only the session configuration and narration wiring differ.

**When to pick which:** Use realtime when latency matters (conversational agents, customer support). Use pipeline when you need modularity (different STT/TTS per market, cost optimization, custom voice models).

## Building the Voice Agent

The agent is a `voice.Agent` subclass from `@livekit/agents`. It receives the user's speech, reasons through it, and decides whether to answer verbally, visually, or both.

```typescript
import { voice, llm } from "@livekit/agents";
import { ShowUITool } from "./tools/show-ui.js";
import { buildPrompt } from "./prompt.js";

class VoiceAgent extends voice.Agent {
  constructor(room: any, mode: AgentMode, exaClient: Exa, session?: AgentSession) {
    const showUI = new ShowUITool(room);

    super({
      instructions: buildPrompt(mode),
      tools: {
        show_ui: showUI.tool,
        web_search: makeTool(mode, session, "web_search", {
          description: "Search the web for real-time information.",
          parameters: z.object({ query: z.string() }),
          execute: webSearch.createExecute(exaClient),
        }),
        search_images: makeTool(mode, session, "search_images", {
          description: "Search for images for multiple subjects in parallel.",
          parameters: z.object({
            queries: z.array(z.string()),
            count: z.number().optional(),
          }),
          execute: imageSearch.createExecute(),
        }),
      },
    });
  }
}
```

The `makeTool` helper wraps tools differently based on mode — in pipeline mode, it adds a `narration` parameter so the LLM can specify what to say while the tool runs; in realtime mode, it uses the raw tool definition and relies on the system prompt to generate narration.

## The show_ui Tool: Where Voice Meets Vision

This is the core integration. When the LLM decides the answer is better shown than heard, it calls `show_ui` with structured content. The tool sends that content to Thesys's C1 model, which generates OpenUI Lang code that streams to the browser as interactive React components.

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
        "Display rich visual UI to the user. Pass the COMPLETE structured " +
        "content you want to visualize. The content will be converted into " +
        "beautiful interactive UI components.",
      parameters: z.object({
        content: z.string().describe(
          "The full structured content to display visually. Be detailed."
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
                {
                  role: "system",
                  content: "You convert content into visually appealing interactive UI."
                },
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

        // Return immediately — LLM continues generating speech
        return "UI is loading on screen. Tell the user what you are showing.";
      },
    });
  }
}
```

Three things to notice:

1. **Fire-and-forget streaming.** The visual render runs in an async IIFE that the tool doesn't await. The `execute` function returns immediately so the LLM can continue generating its spoken response. The user hears the agent while watching components appear.

2. **Abort on new call.** If the LLM calls `show_ui` again before the previous render finishes (e.g., the user asks a follow-up), the previous stream is aborted. This prevents stale UI from appearing after newer content.

3. **Data channel, not HTTP.** The UI streams through LiveKit's `streamText` data channel (topic: `"genui"`), not through an HTTP response. This means the UI update travels the same WebSocket connection as the audio — no CORS issues, no extra infrastructure, works behind any network topology.

## Receiving the Stream in the Browser

The frontend subscribes to the `"genui"` data channel and accumulates the streamed chunks into a growing string. When a new stream starts, the accumulator resets.

```typescript
useEffect(() => {
  const room = session.room;
  if (!room) return;

  const handleGenUI = (reader: AsyncIterable<string>) => {
    setIsStreaming(true);
    setGenUIContent(""); // Reset for new response

    let acc = "";
    (async () => {
      try {
        for await (const chunk of reader) {
          acc += chunk;
          setGenUIContent(acc); // Progressive rendering
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

The accumulated string is passed to `<C1Component>` from `@thesysai/genui-sdk`, which renders the OpenUI Lang markup as interactive React components:

```tsx
<C1Component
  c1Response={content}     // The accumulated OpenUI Lang string
  isStreaming={isStreaming} // Show skeleton while streaming
  onAction={onAction}      // Handle user interactions
/>
```

The component progressively hydrates — completed sections become interactive while later sections are still streaming. A user can click a button in a comparison table while the product cards below it are still rendering.

## Bidirectional Actions: From UI Back to Agent

The visual layer isn't read-only. When a user clicks a button, submits a form, or selects an option in the rendered UI, that action flows back through the agent loop.

```typescript
const handleAction = useCallback(
  (event: { type?: string; params?: Record<string, unknown> }) => {
    switch (event.type) {
      case "open_url":
        window.open(event.params?.url as string, "_blank", "noopener,noreferrer");
        break;

      case "continue_conversation":
      default: {
        const message = event.params?.llmFriendlyMessage as string;
        if (message) {
          setIsProcessingAction(true);
          sendChatMessage(message); // Sends to the LLM as user input
        }
        break;
      }
    }
  },
  [sendChatMessage],
);
```

This is the feedback loop: the LLM renders a comparison table with a "Compare with X" button → the user clicks it → the click event's `llmFriendlyMessage` is sent back as a chat message → the LLM processes it and may render a new visual. The conversation flows naturally between voice and visual, driven by whichever channel the user prefers at any moment.

## Prompt Engineering for Multimodal Output

The system prompt is the most important file in the project. It teaches the LLM when to use voice versus visuals, and how to structure content for the visual renderer.

Key directives from the reference implementation:

**Be aggressive with visual output.** The prompt says: "You should use show_ui aggressively — any time information would be better seen than heard, put it on screen." Specific categories:

- **Data visualizations** — charts, graphs, metrics, trends
- **Forms & interactive input** — collecting preferences, filters, structured data
- **Complex breakdowns** — comparisons, step-by-step guides, feature matrices
- **Product catalogues** — cards with images, prices, ratings
- **Product detail pages** — deep dives on a single item

**Use images before showing products.** The prompt instructs the agent to call `search_images` first, then embed those URLs in the `show_ui` content. This gives the visual renderer real images to work with instead of placeholder graphics.

**Keep voice responses short.** When visual output is active, the spoken response should be a 1-2 sentence summary. The details belong on screen. This is a hard habit to enforce — LLMs want to be thorough verbally — so the prompt explicitly says: "No markdown, no bullet points, no emojis, no asterisks" in spoken output.

**Specify chart types and data.** When asking for a chart, the prompt says to include actual data points, axis labels, and the chart type. "How has Bitcoin performed?" should pass the actual price data and specify "line chart" rather than hoping the renderer guesses correctly.

## Setting It Up Yourself

### Prerequisites

- Node.js 20+
- [pnpm](https://pnpm.io)
- [LiveKit Cloud](https://cloud.livekit.io) account (free tier works)
- API keys: [Thesys](https://platform.thesys.dev), [Exa](https://exa.ai), optionally Google Custom Search for images

### Clone and Configure

```bash
git clone https://github.com/thesysdev/voice-agent-generativeui.git
cd voice-agent-generativeui

# Frontend dependencies
pnpm install

# Agent dependencies (separate project)
cd livekit-agent && pnpm install && cd ..

# Configure environment
cp .env.example .env
```

Fill in `.env`:

```env
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your-api-key
LIVEKIT_API_SECRET=your-api-secret
THESYS_API_KEY=your-thesys-key
EXA_API_KEY=your-exa-key
OPENAI_API_KEY=your-openai-key        # Required for realtime mode
GOOGLE_API_KEY=your-google-key         # Optional, for image search
GOOGLE_CSE_ID=your-cse-id              # Optional, for image search
```

### Run

Two terminals:

```bash
# Terminal 1 — Next.js frontend
pnpm dev

# Terminal 2 — LiveKit voice agent
cd livekit-agent && pnpm agent dev
```

Open `http://localhost:3000`. Pick a mode (pipeline or realtime). Click Start. Ask "Show me the best wireless headphones under $200" and watch the agent speak while rendering product cards with real images.

### Common Setup Issues

**"Could not connect to LiveKit room"** — Verify your `LIVEKIT_URL` starts with `wss://` not `ws://`. Check that the API key and secret match your LiveKit Cloud project.

**Agent starts but doesn't respond to voice** — In pipeline mode, you need Deepgram and Inworld keys configured (the reference repo uses specific STT/TTS providers). In realtime mode, ensure `OPENAI_API_KEY` is valid and has access to `gpt-realtime`.

**Visual UI doesn't appear** — Check browser console for `THESYS_API_KEY` errors. The C1 model call happens server-side in the agent, so a missing or invalid key causes a silent failure — the agent speaks but the screen stays blank.

**Stream aborts mid-render** — This happens when the LLM calls `show_ui` twice in quick succession (e.g., it generates both a chart and a table). The abort controller in `ShowUITool` cancels the first stream. This is by design — only the most recent visual output should be on screen.

## Production Deployment

### Deploy the Agent to LiveKit Cloud

The reference repo includes LiveKit Cloud deployment:

```bash
cd livekit-agent
lk cloud auth
lk agent create --secrets-file=../.env
```

Subsequent deploys: `lk agent deploy`

### Deploy the Frontend

The Next.js frontend deploys to any Node.js hosting (Vercel, Railway, Fly.io). Set the same environment variables. The frontend only needs `LIVEKIT_URL`, `LIVEKIT_API_KEY`, and `LIVEKIT_API_SECRET` — the Thesys and search keys are used by the agent, not the frontend.

### Performance Considerations

| Metric | Pipeline Mode | Realtime Mode |
|--------|--------------|---------------|
| Time to first audio | ~800ms–1.2s | ~200–400ms |
| Time to first visual | ~1.5–2.5s | ~1–2s |
| Memory per session | ~50MB | ~80MB |
| Concurrent sessions | 50–100 per agent | 20–40 per agent |

The visual path adds ~700ms–1.2s over the audio path because it involves a second LLM call (the C1 model). This is acceptable — the user hears the agent speak first, and the visual output appears while they're listening.

### Scaling the Visual Path

For high-volume deployments, the visual path becomes the bottleneck because every `show_ui` call hits the Thesys API. Mitigations:

1. **Cache common renders.** If the agent frequently shows the same type of comparison table, cache the C1 response and replay it.
2. **Debounce rapid calls.** Add a small debounce (200ms) before calling C1 to batch consecutive tool calls into a single render.
3. **Use lighter C1 models.** The reference uses `c1/google/gemini-3-flash` which is fast and cheap. Heavier models produce richer UI but add latency.

## What to Build Next

The reference implementation is a starting point. Here are directions worth exploring:

**Domain-specific agents.** A healthcare agent that shows drug interaction charts while explaining side effects. A financial advisor that renders portfolio allocation pie charts. A cooking assistant that displays ingredient cards with substitution options.

**Multi-user sessions.** LiveKit supports multiple participants in a room. Imagine a support call where both the customer and the agent see the same visual output — the agent highlights a section and the customer's screen follows.

**Persistent visual history.** Currently, each `show_ui` call replaces the previous one. A session transcript that lets the user scroll back through previous visual outputs would make the agent more useful for research tasks.

**Custom component libraries.** The Thesys C1 model generates generic React components. For domain-specific applications, you can define custom component libraries that the model can use — specialized chart types, domain-specific card layouts, branded form components.

---

The code for the reference implementation is at [thesysdev/voice-agent-generativeui](https://github.com/thesysdev/voice-agent-generativeui). LiveKit Agents documentation is at [docs.livekit.io/agents](https://docs.livekit.io/agents). OpenUI documentation is at [openui.com](https://www.openui.com/).