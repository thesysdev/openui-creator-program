# Chakra UI as the Contract for Generated Interfaces

Most teams do not adopt a new UI runtime on a blank canvas. They already have a design system, a pile of product conventions, a11y expectations, color tokens, spacing rules, form patterns, and a long list of components that have been hardened by real users.

That is why the interesting question is not "Can an AI generate an interface?" The interesting question is "Can it generate an interface that still feels like our product?"

For teams using Chakra UI, the answer should not be to hand the model every Chakra primitive and hope it makes tasteful choices. Chakra is flexible by design. A model does not need that much freedom. It needs a smaller contract: a set of app-approved components, typed props, and action boundaries that render through Chakra but do not expose the whole design system.

OpenUI is a useful fit for that pattern because its component library is the contract between the model and the renderer. You define the components with Zod schemas, generate prompt instructions from that library, stream OpenUI Lang from the model, and render the result through React. Chakra can stay where it belongs: inside the implementation of your approved components.

## The wrong integration: expose everything

A tempting first pass is to let the model output generic layout primitives:

```tsx
Box({ padding: "37px", color: "blue.713", borderRadius: "22px" })
Button({ variant: "maybePrimary", size: "large-ish" })
```

That looks flexible, but it gives the model responsibility for details your design system already solved. It can invent token names, mix incompatible variants, build inaccessible color combinations, or create layouts that technically render but do not match the product.

The better approach is to define product-level components:

```tsx
SupportSummaryCard(...)
EscalationBanner(...)
TicketActionGroup(...)
```

Those components can use Chakra internally, but the model only sees the safe interface. In other words, Chakra is the renderer vocabulary for your team. OpenUI is the model-facing vocabulary for the generated response.

## Build a narrow Chakra-backed library

Start by defining a few components around a real workflow. Imagine an internal support console where the assistant can summarize a ticket, show severity, and present safe next actions.

```tsx
import { defineComponent, createLibrary } from "@openuidev/react-lang";
import { Badge, Box, Button, HStack, Text, VStack } from "@chakra-ui/react";
import { z } from "zod/v4";

const SeverityBadge = defineComponent({
  name: "SeverityBadge",
  description: "Displays a support severity label using approved product colors.",
  props: z.object({
    level: z.enum(["low", "medium", "high", "critical"]),
  }),
  component: ({ props }) => {
    const colorScheme = {
      low: "green",
      medium: "yellow",
      high: "orange",
      critical: "red",
    }[props.level];

    return <Badge colorScheme={colorScheme}>{props.level}</Badge>;
  },
});
```

Notice what is missing: the model cannot choose arbitrary colors, spacing, typography, or badge variants. It can only choose a severity level. Chakra still handles the UI, but your application owns the design mapping.

Now add a card component that composes smaller references.

```tsx
const SupportSummaryCard = defineComponent({
  name: "SupportSummaryCard",
  description: "Summarizes a support case with a title, severity, and next step.",
  props: z.object({
    title: z.string(),
    summary: z.string(),
    severity: SeverityBadge.ref,
    nextStep: z.string(),
  }),
  component: ({ props, renderNode }) => (
    <Box borderWidth="1px" borderRadius="lg" p={4} bg="white">
      <VStack align="stretch" gap={3}>
        <HStack justify="space-between">
          <Text fontWeight="semibold">{props.title}</Text>
          {renderNode(props.severity)}
        </HStack>
        <Text color="gray.700">{props.summary}</Text>
        <Text fontSize="sm" color="gray.600">
          Next step: {props.nextStep}
        </Text>
      </VStack>
    </Box>
  ),
});
```

The model sees a component that means "support summary". The user sees a Chakra card that follows the product's spacing and typography. The application keeps control of both.

## Keep actions structured

Generated UI becomes useful when it can trigger actions. It also becomes risky if those actions are vague. Do not ask the model to generate arbitrary JavaScript. Give it named action intents and validate them.

```tsx
const TicketActionGroup = defineComponent({
  name: "TicketActionGroup",
  description: "Renders approved support-ticket actions.",
  props: z.object({
    primaryLabel: z.string(),
    primaryAction: z.enum(["assign_to_tier_2", "request_logs", "refund_review"]),
    secondaryLabel: z.string().optional(),
    secondaryAction: z.enum(["close_as_duplicate", "add_internal_note"]).optional(),
  }),
  component: ({ props }) => (
    <HStack gap={2}>
      <Button colorScheme="blue" data-action={props.primaryAction}>
        {props.primaryLabel}
      </Button>
      {props.secondaryAction && (
        <Button variant="outline" data-action={props.secondaryAction}>
          {props.secondaryLabel}
        </Button>
      )}
    </HStack>
  ),
});
```

In a real app, you would connect `data-action` to the renderer's action callback or your own component event handler. The important part is the boundary: the model can choose among approved intents, but the application decides what each intent does, whether the current user may do it, and whether confirmation is required.

## Assemble the OpenUI library

Once the components exist, expose only the set that belongs in this generated surface.

```tsx
export const supportLibrary = createLibrary({
  root: "SupportSummaryCard",
  components: [SeverityBadge, SupportSummaryCard, TicketActionGroup],
  componentGroups: [
    {
      name: "Support",
      components: ["SupportSummaryCard", "SeverityBadge", "TicketActionGroup"],
      notes: [
        "Use SeverityBadge for every SupportSummaryCard.",
        "Only render TicketActionGroup when the user is expected to take action.",
        "Never invent action names outside the enum.",
      ],
    },
  ],
});
```

The `root` matters. A predictable root gives the model a stable entry point, and it helps the streamed UI render a useful shell early. The component group notes are also part of the contract. They tell the model how these components should be combined without forcing that logic into every user prompt.

## Render inside ChakraProvider

The final React integration is straightforward. Keep Chakra at the app boundary and pass the OpenUI library to the renderer.

```tsx
import { ChakraProvider } from "@chakra-ui/react";
import { Renderer } from "@openuidev/react-lang";
import { supportLibrary } from "./support-library";

export function SupportAssistantMessage({
  content,
  isStreaming,
}: {
  content: string | null;
  isStreaming: boolean;
}) {
  return (
    <ChakraProvider>
      <Renderer
        library={supportLibrary}
        response={content}
        isStreaming={isStreaming}
        onError={(errors) => {
          if (errors.length > 0) {
            console.warn("Generated UI error", errors);
          }
        }}
      />
    </ChakraProvider>
  );
}
```

The model is not generating Chakra code. It is generating OpenUI Lang that resolves to your Chakra-backed components. That distinction is what makes the integration production-shaped instead of demo-shaped.

## Practical guardrails

Keep the model-facing library smaller than the design system. A model does not need every layout primitive in your app. Start with the components that represent complete product concepts: a quote summary, a billing issue card, a deployment checklist, a risk table, an approval form.

Prefer enums over free-form styling. If severity can only be `low`, `medium`, `high`, or `critical`, make that a schema rule. If a button can only be a safe action, make that an enum too.

Use Chakra variants inside the renderer, not in the generated payload. The app should decide that `critical` maps to a red badge, not the model.

Design for streaming. Smaller child components with `.ref` composition are easier to stream and validate than one enormous object with deeply nested props. If the root renders first and children arrive later, the user gets a stable interface instead of a blank wait.

Treat generated UI as untrusted input. Even when the output validates, actions still need permission checks, confirmation steps, and server-side authorization. OpenUI can constrain what the model describes. Your app still owns what happens.

## The adoption path

This is the strongest reason to pair Chakra UI with OpenUI: you do not need to choose between generative UI and your existing product language.

OpenUI gives the model a compact, typed language for describing useful interfaces. Chakra gives your app a mature implementation layer for rendering them consistently. The bridge is the component contract you write between the two.

That contract is where most of the engineering taste lives. Keep it narrow. Name components after product concepts. Hide tokens and variants behind schemas. Make actions explicit. Let the model assemble the interface, but make sure it can only assemble things your product is willing to render.

When you do that, generative UI stops feeling like a separate experimental surface. It becomes another way your existing design system can respond to user intent.
