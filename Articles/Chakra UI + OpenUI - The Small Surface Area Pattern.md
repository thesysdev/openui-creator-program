# Chakra UI + OpenUI: The Small Surface Area Pattern for Design-System-Aware Generative UI

Most teams evaluating generative UI do not start with an empty React app. They start with a design system, a pile of production constraints, and a reasonable fear: if a model can generate UI, will it also generate off-brand layouts, unsafe actions, and components no one can maintain?

That approach risks violating design tokens, creating unmaintainable component trees, and turning every generated answer into a one-off layout review.

OpenUI works best with Chakra UI when you do not expose Chakra as a giant box of primitives. Instead, expose a small vocabulary of product-level components that happen to be implemented with Chakra. The model should not decide whether a warning uses `orange.500`, whether a destructive button is red, or whether a card gets 16px or 24px of padding. Your design system should decide those things. The model should choose between safe interface contracts such as `MetricCard`, `SupportTicket`, `ActionPanel`, and `ApprovalForm`.

This article walks through that pattern: use Chakra UI for rendering, OpenUI for model-generated structure, and a deliberately narrow component library as the boundary between the two.

## The architecture in one sentence

OpenUI lets the model emit structured UI; Chakra UI renders that structure using your existing theme and components; your component library decides what the model is allowed to generate.

A useful mental model is:

```txt
User intent
  -> model response in OpenUI Lang
  -> OpenUI renderer parses component nodes
  -> your registered component library maps nodes to React components
  -> Chakra UI applies tokens, variants, layout, and accessibility defaults
```

The important part is the registered component library. That is the contract. If the contract is too broad, the model becomes a layout engine with too much freedom. If the contract is too narrow, responses feel like canned templates. The goal is a small set of composable components that match real product workflows.

## Do not expose raw Chakra primitives first

Chakra has excellent primitives: `Box`, `Stack`, `Card`, `Button`, `Badge`, `Table`, `Alert`, and many more. It is tempting to register those directly and let the model assemble anything.

For demos, that works. For product software, it becomes fragile.

If the model can generate arbitrary primitive combinations, you now need to review generated UI for:

- inconsistent spacing and hierarchy
- inaccessible color combinations
- unexpected button variants
- confusing action labels
- huge nested layouts that render poorly on mobile
- component combinations your design system never intended

Instead of registering `Box`, `Heading`, `Text`, `Badge`, and `Button` as a blank canvas, start with product-level components:

- `MetricCard`
- `StatusCallout`
- `TicketSummary`
- `ActionPanel`
- `DecisionForm`
- `ResultTable`

Each one can be implemented with Chakra under the hood. The model sees a stable interface. Your users see UI that still looks like your app.

## Step 1: install the pieces

A typical React app using Chakra and OpenUI needs the Chakra packages plus OpenUI's React integration and Zod for prop schemas.

```bash
npm install @chakra-ui/react @emotion/react @emotion/styled framer-motion
npm install @openuidev/react-lang @openuidev/react-ui zod
```

Your app should already have a Chakra provider near the root:

```tsx
import { ChakraProvider, extendTheme } from "@chakra-ui/react";
import type { ReactNode } from "react";

const theme = extendTheme({
  colors: {
    brand: {
      50: "#eef6ff",
      500: "#2563eb",
      700: "#1d4ed8",
    },
  },
  components: {
    Button: {
      defaultProps: { colorScheme: "brand" },
    },
  },
});

export function AppProviders({ children }: { children: ReactNode }) {
  return <ChakraProvider theme={theme}>{children}</ChakraProvider>;
}
```

OpenUI-rendered components are normal React components, so they inherit the same Chakra theme context as the rest of the app.

## Step 2: define a product component, not a primitive

Start with a component the product actually needs. Here is a `MetricCard` that can render one metric, a trend, and a severity state. The model can choose values and state. It cannot choose arbitrary colors, spacing, or typography.

```tsx
import { Badge, Card, CardBody, HStack, Stat, StatHelpText, StatLabel, StatNumber } from "@chakra-ui/react";
import { defineComponent } from "@openuidev/react-lang";
import { z } from "zod";

const MetricCardProps = z.object({
  label: z.string().describe("Short metric label, for example 'Open tickets'."),
  value: z.string().describe("Display value, already formatted for humans."),
  helperText: z.string().optional().describe("One sentence of context."),
  trend: z.enum(["up", "down", "flat"]).optional(),
  tone: z.enum(["neutral", "good", "warning", "critical"]).default("neutral"),
});

function toneToScheme(tone: z.infer<typeof MetricCardProps>["tone"]) {
  return {
    neutral: "gray",
    good: "green",
    warning: "orange",
    critical: "red",
  }[tone];
}

export const MetricCard = defineComponent({
  name: "MetricCard",
  description:
    "Show one important business or operational metric. Use for dashboards, summaries, and status reports.",
  props: MetricCardProps,
  component: ({ label, value, helperText, trend, tone }) => (
    <Card variant="outline">
      <CardBody>
        <Stat>
          <HStack justify="space-between" align="start">
            <StatLabel>{label}</StatLabel>
            <Badge colorScheme={toneToScheme(tone)}>{tone}</Badge>
          </HStack>
          <StatNumber>{value}</StatNumber>
          {helperText ? (
            <StatHelpText>
              {trend ? `${trend}: ` : null}
              {helperText}
            </StatHelpText>
          ) : null}
        </Stat>
      </CardBody>
    </Card>
  ),
});
```

There are two boundaries here:

1. **The Zod schema** controls what the model can pass.
2. **The Chakra implementation** controls how the UI looks.

The model cannot pass `bg="hotpink"`. It cannot invent a custom size. It cannot turn a metric into a full-page layout. It can only fill the contract you gave it.

## Step 3: register a small library

A design-system-aware generative UI app needs a library of these contracts. Keep the first version small enough to audit.

```tsx
import { createLibrary } from "@openuidev/react-lang";
import { MetricCard } from "./metric-card";
import { StatusCallout } from "./status-callout";
import { ActionPanel } from "./action-panel";
import { ResultTable } from "./result-table";

export const supportDashboardLibrary = createLibrary({
  name: "SupportDashboardLibrary",
  description:
    "A Chakra UI component library for support dashboards, ticket summaries, and safe operator actions.",
  components: [MetricCard, StatusCallout, ActionPanel, ResultTable],
});
```

That list is also your review surface. When a generated interface looks wrong, you do not debug an infinite set of possible React trees. You debug a short list of registered components and their schemas.

## Step 4: make actions explicit

The riskiest part of generated UI is rarely the layout. It is the button.

A model-generated button that says "Refund customer" or "Close incident" should not be allowed to directly execute arbitrary code. Treat actions as named intents that your app validates.

```tsx
import { Button, ButtonGroup, Card, CardBody, Text } from "@chakra-ui/react";
import { defineComponent } from "@openuidev/react-lang";
import { z } from "zod";

const AllowedAction = z.enum([
  "open_ticket",
  "assign_to_me",
  "request_approval",
  "show_runbook",
]);

const ActionPanelProps = z.object({
  title: z.string(),
  explanation: z.string(),
  actions: z
    .array(
      z.object({
        label: z.string(),
        action: AllowedAction,
        payload: z.record(z.string(), z.string()).optional(),
      }),
    )
    .max(3),
});

export const ActionPanel = defineComponent({
  name: "ActionPanel",
  description:
    "Show up to three safe next actions. Use only for reversible or approval-gated workflows.",
  props: ActionPanelProps,
  component: ({ title, explanation, actions }) => (
    <Card variant="filled">
      <CardBody>
        <Text fontWeight="semibold">{title}</Text>
        <Text color="gray.600" mt={1}>{explanation}</Text>
        <ButtonGroup mt={4} spacing={3}>
          {actions.map((item) => (
            <Button
              key={item.action}
              variant={item.action === "request_approval" ? "solid" : "outline"}
              onClick={() => window.dispatchEvent(new CustomEvent("openui:action", { detail: item }))}
            >
              {item.label}
            </Button>
          ))}
        </ButtonGroup>
      </CardBody>
    </Card>
  ),
});
```

In a real app, you would probably pass an `onAction` handler through the OpenUI renderer rather than dispatching a browser event. The design principle is the same: the generated UI proposes actions; application code authorizes and executes them.

For sensitive workflows, use a two-step policy:

- The model can render `request_approval`.
- The app decides whether the current user, object state, and backend policy allow the request.

Do not let generated UI become generated authority.

## Step 5: render inside the existing Chakra app

Once the library exists, render OpenUI output wherever your app already renders assistant responses or dynamic panels.

```tsx
import { Box } from "@chakra-ui/react";
import { Renderer } from "@openuidev/react-ui";
import { supportDashboardLibrary } from "./openui-library";

export function GeneratedSupportView({ response }: { response: string }) {
  return (
    <Box maxW="5xl" mx="auto" p={{ base: 4, md: 6 }}>
      <Renderer response={response} library={supportDashboardLibrary} />
    </Box>
  );
}
```

The `response` is the model's OpenUI Lang output. A small dashboard response might look like this:

```txt
MetricCard(
  label="Open priority tickets",
  value="18",
  tone="warning",
  trend="up",
  helperText="Six more than yesterday. Most are billing escalations."
)

StatusCallout(
  title="Billing queue needs review",
  tone="warning",
  body="The queue is still inside SLA, but two enterprise accounts have repeated failed-payment contacts."
)

ActionPanel(
  title="Recommended next step",
  explanation="Review the filtered billing queue before assigning additional agents.",
  actions=[
    { label="Open filtered queue", action="open_ticket", payload={ queue: "billing-priority" } },
    { label="Show escalation runbook", action="show_runbook" }
  ]
)
```

The user sees Chakra cards, callouts, buttons, and spacing. The model sees a constrained language of support-dashboard components.

## Step 6: write prompt rules from the library contract

The component library describes available components, but production apps should also give the model behavioral rules. Keep those rules operational rather than stylistic.

Good rules:

```txt
Use MetricCard only for single numeric or status metrics.
Use ActionPanel only when every action is listed in the allowed action enum.
Prefer StatusCallout over paragraphs when the user needs a warning, success, or blocker.
Never invent component names.
Never include destructive actions. Use request_approval for anything irreversible.
If the requested view needs a component that is not available, explain the limitation in text.
```

Weak rules:

```txt
Make it look nice.
Use our brand.
Create a modern dashboard.
Be concise but detailed.
```

The first set creates predictable behavior. The second set asks the model to guess.

## Step 7: test the contract, not just the page

A normal component test checks whether `MetricCard` renders. A generative UI test should also check whether model-shaped input stays inside the safe contract.

Useful tests include:

- rendering every registered component with minimum valid props
- rendering representative OpenUI Lang responses through the full renderer
- rejecting or ignoring unknown component names
- validating action payloads before they reach backend code
- checking mobile layout with generated combinations, not only hand-authored pages
- snapshotting the generated system prompt or component schema when it changes

For example, keep fixture responses in the repo:

```txt
// fixtures/support-dashboard.openui
MetricCard(label="Tickets at risk", value="7", tone="critical")
StatusCallout(title="SLA risk", tone="critical", body="Three accounts need same-day response.")
ActionPanel(
  title="Next action",
  explanation="Escalate before closing the queue review.",
  actions=[{ label="Request approval", action="request_approval" }]
)
```

Then run a smoke test that renders those fixtures in desktop and mobile viewports. If a schema change breaks rendering, you catch it before the model starts producing unusable UI.

## How this differs from a template system

This pattern is not just a template picker.

A template system says: choose one of these complete screens.

A small-surface OpenUI library says: compose allowed product components based on user intent, but do not leave the design-system boundary.

That difference matters. A support lead might ask:

> Show me which enterprise tickets need action before end of day, grouped by risk.

A template system needs a prebuilt screen for exactly that question. A raw text assistant can summarize the answer but cannot provide a useful action surface. A small OpenUI library can compose metrics, grouped tables, warnings, and approved next actions while still using Chakra's theme and accessibility defaults.

## Where to draw the boundary

The hardest design decision is not technical. It is deciding what the model is allowed to control.

A practical split:

Model can control:

- which registered component appears
- user-facing copy inside bounded fields
- data values already approved for display
- enum-based tones such as `neutral`, `warning`, or `critical`
- ordering of safe sections when the user asks a new question

App should control:

- Chakra theme tokens
- spacing and responsive behavior
- actual backend mutations
- permission checks
- data fetching and source-of-truth validation
- destructive action confirmation
- component availability by route or user role

This is the point of using Chakra with OpenUI. Chakra keeps the UI attached to the product system. OpenUI lets the interface adapt to the user's task. Your schemas decide how much freedom is safe.

## A good first component set

For a production-style support or internal-ops assistant, start with six components:

1. `MetricCard` for one key number or state.
2. `StatusCallout` for warnings, blockers, and success messages.
3. `ResultTable` for scan-heavy structured data.
4. `EntityCard` for customers, accounts, tickets, or projects.
5. `ActionPanel` for reversible or approval-gated next steps.
6. `DecisionForm` for collecting structured input before a workflow continues.

Do not add a generic `Container` until you have a concrete need. Do not add a generic `Button` until you know how actions are authorized. Every new component expands the model's search space and your review burden.

## Common mistakes

### Mistake 1: registering the whole design system

A design system is for developers. A generative UI component library is for a model. Those are not the same audience. The model needs fewer components with stronger descriptions.

### Mistake 2: letting the model choose visual semantics

Do not ask the model to pick arbitrary colors. Give it business-level tones and map those tones to Chakra variants yourself.

### Mistake 3: treating generated buttons as trusted events

Generated UI should never bypass application authorization. Treat action payloads like user input: validate them, authorize them, log them, and require confirmation for risky paths.

### Mistake 4: testing only happy-path prose

Generated UI fails in combinations. Test component sequences, mobile widths, missing optional fields, long labels, unknown component names, and action payload validation.

### Mistake 5: making every response dynamic

Some screens should stay fixed. Compliance reports, audit logs, billing settings, and destructive admin flows often need stable layouts more than adaptive layouts. Use OpenUI where the user's question changes the shape of the answer.

## When this pattern is a good fit

Chakra plus OpenUI is a strong fit when:

- your app already uses Chakra UI
- users ask varied questions over the same domain data
- plain text answers create follow-up work
- the UI needs to be interactive, not just readable
- you can define a safe set of product-level components
- actions can be routed through existing authorization code

It is a poor fit when:

- every workflow is a fixed, regulated screen
- the model would need arbitrary layout freedom to be useful
- generated actions cannot be safely validated
- the data behind the UI is not trustworthy or current

## The takeaway

The best way to make OpenUI respect a Chakra design system is not to teach the model every Chakra primitive. It is to hide those primitives behind a small, typed, product-aware component library.

Let Chakra own presentation. Let OpenUI own structured generation. Let your app own authorization and data integrity.

That gives you the useful part of generative UI: interfaces that adapt to the user's task, without turning your design system into a suggestion.
