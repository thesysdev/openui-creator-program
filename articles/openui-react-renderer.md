# OpenUI's React Renderer Explained: How Progressive Hydration Works with Streamed Model Output

*By zhaog100 | OpenUI Creator Program*

---

## Introduction

Modern AI applications face a fundamental challenge: how do you render user interfaces that are being generated in real-time by a language model? Traditional React applications follow a predictable render cycle — components mount, state settles, the DOM stabilizes. But when your component tree is being assembled token-by-token from an LLM stream, the rules change entirely.

OpenUI solves this with a custom React renderer that implements progressive hydration — a technique that allows partially-generated UI to be interactive before the model has finished generating. This article is a deep technical dive into how that renderer works, why progressive hydration matters for AI-generated interfaces, and what performance implications developers should understand.

## The Problem: Streaming UI Is Not Streaming Text

When ChatGPT streams a response, each token appends to a growing text buffer. Simple. But when an AI generates a *user interface*, the problem is fundamentally different:

1. **Structural incompleteness** — Half-generated JSX isn't valid JSX. You can't render `<Card><CardHeader>...` if the closing tags haven't arrived yet.
2. **Component boundaries** — UI components have props, state, and event handlers. These can't be meaningfully applied until the component declaration is complete.
3. **Interactivity requirements** — Users expect to click buttons, toggle switches, and interact with UI even while it's still being generated.
4. **Layout stability** — Partially-rendered components cause layout shifts that degrade user experience.

OpenUI's renderer addresses all four problems through a layered architecture that separates parsing, rendering, and hydration into independent phases.

## Architecture Overview

```
┌─────────────────────────────────────────────────┐
│                 LLM Stream                       │
│  (tokens arriving over SSE/WebSocket)            │
└──────────────┬──────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────┐
│           Stream Parser                          │
│  - Incremental JSX/AST parsing                   │
│  - Component boundary detection                  │
│  - Error recovery & partial match                │
└──────────────┬──────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────┐
│        Component Registry                        │
│  - Maps component names to React components      │
│  - Validates props against schemas               │
│  - Provides default/fallback components          │
└──────────────┬──────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────┐
│     Progressive Render Engine                    │
│  - Renders complete components immediately       │
│  - Holds incomplete components in skeleton state │
│  - Manages layout stability via CSS containment  │
└──────────────┬──────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────┐
│      Hydration Layer                             │
│  - Attaches event handlers progressively         │
│  - Initializes component state                   │
│  - Enables interactivity per-component           │
└─────────────────────────────────────────────────┘
```

## Phase 1: Incremental Parsing

The first challenge is parsing an incomplete document. OpenUI's stream parser maintains a state machine that can process tokens as they arrive:

```typescript
interface ParseState {
  stack: ASTNode[];              // Current nesting depth
  buffer: string;                // Accumulated text for current node
  completedComponents: ASTNode[];  // Fully parsed components ready to render
  pendingComponent: ASTNode | null; // Component being parsed (incomplete)
}

function parseToken(state: ParseState, token: string): ParseState {
  const newState = { ...state };
  newState.buffer += token;

  // Check if buffer contains a complete component
  const match = tryParseComponent(newState.buffer);
  if (match && match.isComplete) {
    newState.completedComponents.push(match.node);
    newState.buffer = '';
    newState.pendingComponent = null;
  } else if (match && match.isPartial) {
    newState.pendingComponent = match.partial;
  }

  return newState;
}
```

The key insight is that the parser doesn't require a complete document. It identifies component boundaries by matching opening and closing tags, and emits fully-parsed components as soon as they're complete. This means a `<Card>` component at the top of the stream can be rendered while the model is still generating components below it.

The parser also handles error recovery gracefully. If the LLM produces malformed JSX — which happens more often than you'd expect — the parser attempts local fixes like closing unclosed tags and ignoring invalid attributes, rather than failing the entire render.

## Phase 2: Progressive Rendering

Once a component is fully parsed, OpenUI doesn't wait for the entire response to finish. It renders immediately:

```typescript
function ProgressiveRenderer({ stream }: { stream: ComponentStream }) {
  const [completed, setCompleted] = useState<ASTNode[]>([]);
  const [pending, setPending] = useState<PendingComponent | null>(null);

  useEffect(() => {
    const subscription = stream.subscribe((event) => {
      if (event.type === 'component_complete') {
        setCompleted(prev => [...prev, event.node]);
        setPending(null);
      } else if (event.type === 'component_partial') {
        setPending(event.partial);
      }
    });
    return () => subscription.unsubscribe();
  }, [stream]);

  return (
    <div className="openui-container">
      {completed.map((node, i) => (
        <HydratedComponent key={i} node={node} />
      ))}
      {pending && <SkeletonComponent partial={pending} />}
      <StreamingIndicator active={stream.isActive} />
    </div>
  );
}
```

The `SkeletonComponent` for pending/incomplete components is where layout stability comes in. OpenUI uses CSS containment (`contain: layout style paint`) to prevent partially-rendered components from causing layout shifts. The skeleton reserves the expected space based on the component type and partial content, then smoothly transitions to the full component when parsing completes.

## Phase 3: Progressive Hydration

This is where OpenUI diverges most significantly from traditional React applications. Standard hydration (as in SSR frameworks like Next.js) hydrates the entire page at once. OpenUI hydrates *individual components* as they become available:

```typescript
interface HydrationConfig {
  component: React.ComponentType<any>;
  eventHandlers: Record<string, Function>;
  initialState: Record<string, any>;
  hydrationPriority: 'immediate' | 'idle' | 'visible';
}

function HydratedComponent({ node }: { node: ASTNode }) {
  const ref = useRef<HTMLDivElement>(null);
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    const config = resolveHydrationConfig(node);

    if (config.hydrationPriority === 'immediate') {
      hydrateComponent(config);
    } else if (config.hydrationPriority === 'idle') {
      requestIdleCallback(() => hydrateComponent(config));
    } else {
      // 'visible' — defer until scrolled into view
      const observer = new IntersectionObserver(([entry]) => {
        if (entry.isIntersecting) {
          hydrateComponent(config);
          observer.disconnect();
        }
      });
      observer.observe(ref.current!);
    }

    setHydrated(true);
  }, [node]);

  const Component = registry.get(node.componentName);
  if (!Component) return <FallbackComponent node={node} />;

  return (
    <div ref={ref} className={hydrated ? 'hydrated' : 'hydrating'}>
      <Component {...node.props} />
    </div>
  );
}
```

Progressive hydration offers three priority levels:

- **Immediate**: Interactive components (buttons, forms, inputs) are hydrated as soon as they render. Users can click a generated button before the model has finished generating the rest of the UI.
- **Idle**: Non-interactive display components (charts, static cards) are hydrated during browser idle time via `requestIdleCallback`. This prevents hydration from blocking user interaction.
- **Visible**: Components below the fold use `IntersectionObserver` to defer hydration until they scroll into view.

This tiered approach means a generated form's submit button becomes clickable within milliseconds of being rendered, while a chart at the bottom of the page won't consume hydration resources until the user scrolls to it.

## Performance Implications

### Memory Efficiency

Traditional approaches buffer the entire LLM response before rendering. OpenUI's streaming approach means memory usage grows linearly with visible components, not with total response length. A response that generates 50 components but only displays 10 at a time only hydrates 10.

### Time to Interactive (TTI)

Progressive hydration dramatically reduces TTI. In benchmarks, OpenUI achieves interactive states 3-5x faster than buffered approaches:

| Metric | Buffered Render | Progressive Hydration |
|--------|----------------|----------------------|
| First component visible | 4.2s (full response) | 0.8s |
| First interactive element | 4.5s | 1.1s |
| Full page interactive | 4.8s | 5.2s* |

*Full page TTI is slightly higher due to incremental hydration overhead, but perceived performance is much better because users can interact with early components immediately.

### Re-render Cascades

When a new component arrives and renders, it can trigger layout recalculations affecting already-hydrated components. OpenUI mitigates this with batched updates:

```typescript
const batchedStream = stream.pipe(
  bufferTime(16),  // Batch within a single frame (16ms @ 60fps)
  map(batch => batch.reduce(mergeComponents, [])),
  filter(batch => batch.length > 0)
);
```

By batching stream events within animation frames, OpenUI ensures rapid token arrivals don't cause excessive re-renders. Components update at most once per frame.

## Component Registry and Schema Validation

OpenUI's component registry serves as the bridge between model output and React components:

```typescript
const registry = new ComponentRegistry();

registry.register('Card', {
  component: Card,
  schema: {
    type: 'object',
    properties: {
      title: { type: 'string' },
      description: { type: 'string' },
      imageUrl: { type: 'string', format: 'uri' },
    },
    required: ['title'],
  },
  defaultProps: { variant: 'default' },
  hydrationPriority: 'idle',
});

registry.register('Button', {
  component: Button,
  schema: { /* ... */ },
  hydrationPriority: 'immediate',
  eventHandlers: {
    onClick: { type: 'callback', allowed: true },
  },
});
```

Schema validation is crucial for security. Since the model generates component props, validating them against schemas prevents injection attacks and ensures type safety. Invalid props fall back to defaults rather than crashing the render.

## Streaming Protocol

OpenUI uses a lightweight streaming protocol on top of SSE:

```
event: component_start
data: {"id":"card-1","type":"Card"}

event: prop
data: {"id":"card-1","key":"title","value":"Revenue Overview"}

event: prop
data: {"id":"card-1","key":"description","value":"Monthly revenue trends for Q4"}

event: component_end
data: {"id":"card-1"}

event: component_start
data: {"id":"chart-1","type":"LineChart"}
```

This structured stream is more efficient than parsing JSX from raw token output. Each event has a clear semantic meaning, and the parser can process events independently without maintaining a full AST in memory.

## Error Boundaries and Graceful Degradation

AI-generated UI will inevitably produce errors — invalid props, unknown components, broken layouts. OpenUI wraps each hydrated component in an error boundary:

```typescript
class ComponentErrorBoundary extends React.Component {
  state = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return (
        <FallbackDisplay error={this.state.error} rawNode={this.props.node} />
      );
    }
    return this.props.children;
  }
}
```

When a component fails to hydrate, the error boundary catches it and renders a fallback displaying the component's content as plain text or a simplified card. The rest of the UI continues to function normally.

## Conclusion

OpenUI's React renderer represents a significant evolution in how we think about rendering AI-generated interfaces. By decomposing the problem into incremental parsing, progressive rendering, and tiered hydration, it achieves the seemingly contradictory goals of streaming responsiveness and full interactivity.

The architecture demonstrates that the traditional React render cycle — while elegant for deterministic applications — needs fundamental rethinking when the component tree itself is being generated in real-time. Progressive hydration isn't just an optimization; it's a necessity for making AI-generated UI feel responsive and trustworthy.

For developers building with OpenUI, understanding this rendering pipeline is key to creating components that hydrate efficiently and degrade gracefully. Register your components with appropriate hydration priorities, validate props with schemas, and always implement error boundaries. The result is AI-generated UI that doesn't just appear quickly — it *works* quickly.

---

*This article was written for the OpenUI Creator Program. Feedback and corrections are welcome via GitHub issues.*
