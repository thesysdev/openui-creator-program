type VisualFrameStatus = "streaming" | "ready" | "superseded" | "error";

type VisualFrame = {
  conversationId: string;
  turnId: string;
  status: VisualFrameStatus;
  openui: string;
};

type FlightOption = {
  id: string;
  label: string;
  priceDelta: string;
  seatStatus: string;
};

const conversationId = "room_flight_support_42";

const refundableOptions: FlightOption[] = [
  { id: "flight_0710", label: "7:10 AM", priceDelta: "$42 more", seatStatus: "Window available" },
  { id: "flight_1020", label: "10:20 AM", priceDelta: "$38 more", seatStatus: "Window available" },
];

export function buildFlightOptionsFrame(turnId: string, options: FlightOption[]): VisualFrame {
  return {
    conversationId,
    turnId,
    status: "ready",
    openui: [
      "root = Stack([summary, progress, options, confirm])",
      'summary = SummaryCard("Flight change", "Tomorrow morning, same airline preferred")',
      'progress = ToolProgress("Found refundable options", "complete")',
      `options = OptionList([${options.map((option) => option.id).join(", ")}])`,
      ...options.map(
        (option) =>
          `${option.id} = OptionRow("${option.label}", "${option.priceDelta}", "${option.seatStatus}")`,
      ),
      'confirm = ConfirmationPanel("Choose a flight", [chooseLate, keepSearching])',
      'chooseLate = ActionButton("Choose 10:20 AM", "flight.select", "flight_1020")',
      'keepSearching = ActionButton("Keep searching", "flight.search.more")',
    ].join("\n"),
  };
}

export function markSuperseded(frame: VisualFrame, nextTurnId: string): VisualFrame {
  return {
    ...frame,
    turnId: nextTurnId,
    status: "superseded",
  };
}

const actions = {
  "flight.select": async (optionId: string) => {
    const option = refundableOptions.find((candidate) => candidate.id === optionId);
    if (!option) throw new Error("Selected flight option is no longer available.");
    return { selected: option.id, requiresConfirmation: true };
  },
  "flight.search.more": async () => ({ searchExpanded: true }),
};

export async function handleGeneratedAction(actionId: keyof typeof actions, payload?: string) {
  if (!(actionId in actions)) {
    throw new Error(`Unknown generated action: ${actionId}`);
  }

  return actions[actionId](payload ?? "");
}

export const readyFrame = buildFlightOptionsFrame("turn_12", refundableOptions);
export const interruptedFrame = markSuperseded(readyFrame, "turn_13");
