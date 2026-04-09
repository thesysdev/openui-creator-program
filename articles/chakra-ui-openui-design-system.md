# Chakra UI + OpenUI: Building a Design-System-Aware Generative UI App

You've got a Chakra UI design system. Buttons, cards, inputs — all consistent, all themed, all the way you want them. Now someone on the team wants to add generative UI. An LLM that produces actual interactive components, not just text.

The obvious fear: the AI is going to spit out its own components that look nothing like the rest of your app. Mismatched spacing, wrong color tokens, different border radii. Two visual languages on one page.

OpenUI solves this with a layer most generative UI frameworks skip. Instead of the LLM generating raw JSX (which it will absolutely hallucinate wrong), OpenUI introduces an intermediate language — openui-lang — that gets parsed into a tree of typed component references. You control what components those references resolve to.

That's the key insight: **you register your own component library, and the model's output renders through it.** If you register Chakra UI components, every `Card`, `Button`, and `Input` the model generates will be your Chakra components, with your theme, your tokens, your design system.

## How OpenUI's Component System Works

OpenUI has three layers:

1. **`@openuidev/lang-core`** — The parser. It takes the LLM's raw text output and produces a typed AST (abstract syntax tree) of element nodes, each with a component name and validated props.

2. **`@openuidev/react-lang`** — The React binding layer. This is where `defineComponent` and `createLibrary` live. You use these to register your components with their prop schemas (via Zod), and the `Renderer` component turns parsed AST nodes into actual React elements.

3. **`@openuidev/react-ui`** — OpenUI's default component library. This is what you're replacing. It provides ~50 pre-built components (Card, TextContent, Table, Charts, Form, etc.) that work out of the box.

When you bring Chakra UI into the picture, you're swapping layer 3. Layers 1 and 2 stay the same.

Here's what the default Card component definition looks like inside `react-ui`:

```tsx
import { defineComponent } from "@openuidev/react-lang";
import { Card as OpenUICard } from "../../components/Card";
import { CardSchema } from "./schema";

export const Card = defineComponent({
  name: "Card",
  props: CardSchema,
  description:
    'Styled container. variant: "card" | "sunk" | "clear".',
  component: ({ props, renderNode }) => (
    <OpenUICard variant={props.variant ?? "card"} width="full">
      {renderNode(props.children)}
    </OpenUICard>
  ),
});
```

Three things matter here:

- **`name`**: The string the LLM uses to reference this component. When the model outputs `Card(...)`, this is what it resolves to.
- **`props`**: A Zod schema. The parser validates the model's output against it. Bad props get caught before render.
- **`component`**: The actual React component. `renderNode` recursively renders child elements through the same pipeline.

The `description` field is included in the system prompt sent to the model, so it knows what each component does and when to use it.

## Registering Chakra UI Components

Let's build a library that maps OpenUI's component contracts to Chakra UI. Start with three components that cover most chat-style generative UI: Card, TextContent, and Button.

### Setup

```bash
npm install @openuidev/react-lang @chakra-ui/react @emotion/react zod
```

### Defining a Chakra Card

```tsx
// lib/genui/chakra-card.ts
import { defineComponent } from "@openuidev/react-lang";
import { Box } from "@chakra-ui/react";
import { z } from "zod";

export const ChakraCard = defineComponent({
  name: "Card",
  props: z.object({
    children: z.array(z.any()),
    variant: z.enum(["card", "sunk", "clear"]).optional(),
  }),
  description:
    "Container for content sections. Use for grouping related information.",
  component: ({ props, renderNode }) => {
    const bg = props.variant === "sunk"
      ? "gray.50"
      : props.variant === "clear"
        ? "transparent"
        : "white";

    return (
      <Box
        bg={bg}
        borderRadius="lg"
        borderWidth={props.variant === "card" ? "1px" : "0"}
        borderColor="gray.200"
        p={5}
        display="flex"
        flexDirection="column"
        gap={4}
        _dark={{
          bg: props.variant === "sunk" ? "gray.800" : props.variant === "clear" ? "transparent" : "gray.700",
          borderColor: "gray.600",
        }}
      >
        {renderNode(props.children)}
      </Box>
    );
  },
});
```

Notice what happened: same `name` ("Card"), same prop contract (variant + children), but the render function uses Chakra's `Box` with Chakra style props. The model doesn't know or care — it references "Card" either way.

### Defining Chakra TextContent

```tsx
// lib/genui/chakra-text.ts
import { defineComponent } from "@openuidev/react-lang";
import { Text, Heading } from "@chakra-ui/react";
import { z } from "zod";

export const ChakraTextContent = defineComponent({
  name: "TextContent",
  props: z.object({
    text: z.string(),
    level: z.enum(["h1", "h2", "h3", "body", "caption"]).optional(),
  }),
  description:
    "Text element. level controls hierarchy: h1-h3 for headings, body (default), caption for small text.",
  component: ({ props }) => {
    const level = props.level ?? "body";

    if (level.startsWith("h")) {
      const sizeMap = { h1: "xl", h2: "lg", h3: "md" } as const;
      return (
        <Heading
          as={level as "h1" | "h2" | "h3"}
          size={sizeMap[level as keyof typeof sizeMap]}
        >
          {props.text}
        </Heading>
      );
    }

    return (
      <Text
        fontSize={level === "caption" ? "sm" : "md"}
        color={level === "caption" ? "gray.500" : undefined}
      >
        {props.text}
      </Text>
    );
  },
});
```

### Defining a Chakra Button

```tsx
// lib/genui/chakra-button.ts
import { defineComponent } from "@openuidev/react-lang";
import { Button } from "@chakra-ui/react";
import { z } from "zod";

export const ChakraButton = defineComponent({
  name: "Button",
  props: z.object({
    label: z.string(),
    variant: z.enum(["primary", "secondary", "ghost"]).optional(),
    action: z.any().optional(),
  }),
  description:
    "Interactive button. variant: primary (default, filled), secondary (outlined), ghost (text only).",
  component: ({ props }) => {
    const variantMap = {
      primary: "solid",
      secondary: "outline",
      ghost: "ghost",
    } as const;

    return (
      <Button
        colorScheme="blue"
        variant={variantMap[props.variant ?? "primary"]}
      >
        {props.label}
      </Button>
    );
  },
});
```

### Assembling the Library

```tsx
// lib/genui/chakra-library.ts
import { createLibrary } from "@openuidev/react-lang";
import { ChakraCard } from "./chakra-card";
import { ChakraTextContent } from "./chakra-text";
import { ChakraButton } from "./chakra-button";

export const chakraLibrary = createLibrary({
  name: "chakra-genui",
  version: "1.0.0",
  components: [ChakraCard, ChakraTextContent, ChakraButton],
  componentGroups: [
    {
      name: "Layout",
      components: ["Card"],
      notes: [
        "Card uses Chakra Box with design tokens for spacing and color.",
        "Use variant 'sunk' for secondary content areas.",
      ],
    },
    {
      name: "Content",
      components: ["TextContent"],
      notes: ["Use level 'h2' for section titles, 'body' for paragraphs."],
    },
    {
      name: "Actions",
      components: ["Button"],
      notes: ["Use variant 'primary' for the main action, 'ghost' for secondary."],
    },
  ],
});
```

`createLibrary` takes your component definitions, extracts the schemas for prompt generation, and packages everything the `Renderer` needs. The `componentGroups` with `notes` are especially important — these notes appear verbatim in the system prompt sent to the model, teaching it your design system's conventions. "Use variant 'sunk' for secondary content areas" isn't just documentation — it's an instruction that shapes how the model uses your components.

## Wiring It Up

The `Renderer` component from `@openuidev/react-lang` takes the raw model response and your library, and handles everything else: parsing, validation, streaming support, error boundaries.

```tsx
// app/chat/page.tsx
"use client";

import { Renderer } from "@openuidev/react-lang";
import { ChakraProvider } from "@chakra-ui/react";
import { chakraLibrary } from "@/lib/genui/chakra-library";

export default function ChatPage() {
  const [response, setResponse] = useState<string | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);

  // response comes from your LLM integration
  // (ChatProvider, Vercel AI SDK, direct API call, etc.)

  return (
    <ChakraProvider>
      <Renderer
        response={response}
        library={chakraLibrary}
        isStreaming={isStreaming}
        onAction={(event) => {
          // Handle button clicks, form submissions, etc.
          console.log("Action:", event);
        }}
      />
    </ChakraProvider>
  );
}
```

When the model generates openui-lang like:

```
Card(
  TextContent(text="Here are three options for your trip", level="h2")
  TextContent(text="Based on your budget and dates, these destinations fit best.")
  Button(label="Show me flights" variant="primary")
)
```

The parser produces a tree. The `Renderer` walks it. Each node resolves to your Chakra component. The output is a Chakra `Box` containing a `Heading`, a `Text`, and a `Button` — all using your theme's color tokens, spacing scale, and font stack.

## Handling the Theme

Chakra's theme system and OpenUI's rendering are independent — which is actually the point. Your Chakra theme controls how components look. OpenUI's library controls which components exist and what props they accept.

To pass theme context down to your genui components, wrap the `Renderer` in `ChakraProvider` with your custom theme:

```tsx
import { extendTheme, ChakraProvider } from "@chakra-ui/react";

const theme = extendTheme({
  colors: {
    brand: {
      50: "#e3f2fd",
      500: "#2196f3",
      600: "#1e88e5",
      900: "#0d47a1",
    },
  },
  fonts: {
    heading: "'Inter', sans-serif",
    body: "'Inter', sans-serif",
  },
});

// In your component:
<ChakraProvider theme={theme}>
  <Renderer response={response} library={chakraLibrary} />
</ChakraProvider>
```

Now when the model generates a `Button(label="Book now" variant="primary")`, it renders as a Chakra Button using your brand colors. No extra work. The component you registered already uses `colorScheme`, so Chakra's theming machinery handles the rest.

## What About Components You Don't Define?

If the model references a component that isn't in your library — say `Table` — the `Renderer` returns `null` for that node. No crash, no error in the UI. The `onError` callback fires with a structured error:

```ts
{
  source: "runtime",
  code: "unknown-component",
  component: "Table",
  message: "Component Table is not registered in the library"
}
```

You can use this to build a feedback loop: feed the error back to the model so it retries with components it knows about. Or just expand your library. The more components you register, the richer the model's output vocabulary.

In practice, you'll want to cover at least these categories to handle most generative UI scenarios:

- **Layout**: Card, Stack (horizontal/vertical grouping)
- **Content**: TextContent, Image, CodeBlock, Separator
- **Data**: Table, ListBlock
- **Forms**: Input, Select, CheckBoxGroup, RadioGroup
- **Actions**: Button, FollowUpBlock
- **Charts**: BarChart, LineChart, PieChart (if you need data visualization)

Each one follows the same pattern: `defineComponent` with a Zod schema, a description for the model, and a render function that uses your Chakra components.

## Why This Pattern Matters

The design system problem in generative UI isn't a styling problem — it's a contract problem. When an LLM generates UI, you need guarantees about:

1. **What components can appear** — the library defines the vocabulary
2. **What props are valid** — Zod schemas enforce the contract at parse time
3. **How things render** — your component functions control the output

OpenUI's `defineComponent` / `createLibrary` / `Renderer` pattern separates these concerns cleanly. The model generates structured references. The parser validates them. Your components render them. Chakra's theme styles them.

The alternative — letting the model generate raw JSX with Chakra imports — breaks on several levels. The model hallucinates prop names, mixes up import paths, uses deprecated APIs, and produces components that can't be safely rendered without `eval`. The intermediate language approach avoids all of this by constraining the model's output to a validated schema.

If you're evaluating generative UI for a production app, the question isn't whether the model can generate good-looking components. It's whether it can generate components that match *your* components. With OpenUI's headless architecture, the answer is yes — bring your own design system, register it once, and let the model work within your constraints.
