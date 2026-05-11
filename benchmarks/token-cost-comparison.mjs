import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { encodingForModel } = require("js-tiktoken");

const scenarios = [
  {
    name: "support-ticket-summary",
    description:
      "A support dashboard response with metrics, a table, and an action card.",
    json: JSON.stringify({
      component: "Dashboard",
      props: {
        title: "Escalation risk",
        children: [
          {
            component: "MetricCard",
            props: {
              label: "Open tickets",
              value: 42,
              trend: "up",
              change: "+18%",
            },
          },
          {
            component: "MetricCard",
            props: {
              label: "At-risk accounts",
              value: 7,
              trend: "up",
              change: "+3",
            },
          },
          {
            component: "Table",
            props: {
              columns: ["Account", "SLA", "Owner", "Next action"],
              rows: [
                ["Acme", "2h overdue", "Rina", "Escalate to success lead"],
                ["Northwind", "45m left", "Mateo", "Send workaround"],
                ["Globex", "3h left", "Ari", "Confirm patch ETA"],
              ],
            },
          },
          {
            component: "ActionCard",
            props: {
              title: "Recommended action",
              body: "Notify owners for Acme and Northwind before the next support standup.",
              actionLabel: "Draft owner update",
            },
          },
        ],
      },
    }),
    aiSdk: JSON.stringify({
      toolName: "renderSupportDashboard",
      toolCallId: "call_support_001",
      state: "output-available",
      input: {
        accountSegment: "enterprise",
        includeActionCard: true,
      },
      output: {
        openTickets: 42,
        atRiskAccounts: 7,
        rows: [
          {
            account: "Acme",
            sla: "2h overdue",
            owner: "Rina",
            nextAction: "Escalate to success lead",
          },
          {
            account: "Northwind",
            sla: "45m left",
            owner: "Mateo",
            nextAction: "Send workaround",
          },
          {
            account: "Globex",
            sla: "3h left",
            owner: "Ari",
            nextAction: "Confirm patch ETA",
          },
        ],
        recommendation:
          "Notify owners for Acme and Northwind before the next support standup.",
      },
    }),
    openui: `dashboard "Escalation risk" {
  metric "Open tickets" 42 trend=up change="+18%"
  metric "At-risk accounts" 7 trend=up change="+3"
  table columns=["Account","SLA","Owner","Next action"] [
    ["Acme","2h overdue","Rina","Escalate to success lead"]
    ["Northwind","45m left","Mateo","Send workaround"]
    ["Globex","3h left","Ari","Confirm patch ETA"]
  ]
  actionCard "Recommended action" body="Notify owners for Acme and Northwind before the next support standup." action="Draft owner update"
}`,
  },
  {
    name: "plan-comparison",
    description:
      "A buyer-facing plan comparison with three cards and a highlighted recommendation.",
    json: JSON.stringify({
      component: "Comparison",
      props: {
        title: "Choose a workspace plan",
        recommended: "Team",
        children: [
          {
            component: "PlanCard",
            props: {
              name: "Starter",
              price: "$19",
              features: ["3 projects", "Basic analytics", "Email support"],
              cta: "Start small",
            },
          },
          {
            component: "PlanCard",
            props: {
              name: "Team",
              price: "$49",
              features: [
                "Unlimited projects",
                "Role-based access",
                "Priority support",
              ],
              cta: "Choose Team",
              highlighted: true,
            },
          },
          {
            component: "PlanCard",
            props: {
              name: "Scale",
              price: "$149",
              features: ["SAML SSO", "Audit logs", "Dedicated success"],
              cta: "Talk to sales",
            },
          },
        ],
      },
    }),
    aiSdk: JSON.stringify({
      toolName: "displayPlans",
      toolCallId: "call_plans_002",
      state: "output-available",
      input: {
        seats: 12,
        needsSso: false,
        supportLevel: "priority",
      },
      output: {
        title: "Choose a workspace plan",
        recommended: "Team",
        plans: [
          {
            name: "Starter",
            price: "$19",
            features: ["3 projects", "Basic analytics", "Email support"],
            cta: "Start small",
          },
          {
            name: "Team",
            price: "$49",
            features: [
              "Unlimited projects",
              "Role-based access",
              "Priority support",
            ],
            cta: "Choose Team",
            highlighted: true,
          },
          {
            name: "Scale",
            price: "$149",
            features: ["SAML SSO", "Audit logs", "Dedicated success"],
            cta: "Talk to sales",
          },
        ],
      },
    }),
    openui: `comparison "Choose a workspace plan" recommended="Team" {
  plan "Starter" price="$19" features=["3 projects","Basic analytics","Email support"] cta="Start small"
  plan "Team" price="$49" features=["Unlimited projects","Role-based access","Priority support"] cta="Choose Team" highlighted
  plan "Scale" price="$149" features=["SAML SSO","Audit logs","Dedicated success"] cta="Talk to sales"
}`,
  },
  {
    name: "incident-intake-form",
    description:
      "A generated incident form with validation hints and conditional routing.",
    json: JSON.stringify({
      component: "Form",
      props: {
        title: "Report a production incident",
        submitLabel: "Create incident",
        fields: [
          {
            component: "TextInput",
            props: {
              name: "summary",
              label: "Summary",
              required: true,
              maxLength: 120,
            },
          },
          {
            component: "Select",
            props: {
              name: "severity",
              label: "Severity",
              options: ["SEV1", "SEV2", "SEV3"],
              required: true,
            },
          },
          {
            component: "Textarea",
            props: { name: "impact", label: "Customer impact", required: true },
          },
          {
            component: "Checkbox",
            props: {
              name: "pageOnCall",
              label: "Page on-call engineer",
              defaultValue: true,
            },
          },
        ],
        validation: {
          summary: "Keep it specific enough for the incident channel title.",
          severity: "Use SEV1 only when production is down or data is at risk.",
        },
      },
    }),
    aiSdk: JSON.stringify({
      toolName: "renderIncidentForm",
      toolCallId: "call_incident_003",
      state: "output-available",
      input: {
        userRole: "support_lead",
        defaultPageOnCall: true,
      },
      output: {
        title: "Report a production incident",
        submitLabel: "Create incident",
        fields: [
          {
            type: "text",
            name: "summary",
            label: "Summary",
            required: true,
            maxLength: 120,
          },
          {
            type: "select",
            name: "severity",
            label: "Severity",
            options: ["SEV1", "SEV2", "SEV3"],
            required: true,
          },
          {
            type: "textarea",
            name: "impact",
            label: "Customer impact",
            required: true,
          },
          {
            type: "checkbox",
            name: "pageOnCall",
            label: "Page on-call engineer",
            defaultValue: true,
          },
        ],
        validationHints: {
          summary: "Keep it specific enough for the incident channel title.",
          severity: "Use SEV1 only when production is down or data is at risk.",
        },
      },
    }),
    openui: `form "Report a production incident" submit="Create incident" {
  text summary "Summary" required max=120 hint="Keep it specific enough for the incident channel title."
  select severity "Severity" options=["SEV1","SEV2","SEV3"] required hint="Use SEV1 only when production is down or data is at risk."
  textarea impact "Customer impact" required
  checkbox pageOnCall "Page on-call engineer" default=true
}`,
  },
];

const enc = encodingForModel("gpt-4o");

function countTokens(text) {
  return enc.encode(text).length;
}

const rows = scenarios.map((scenario) => {
  const jsonTokens = countTokens(scenario.json);
  const aiSdkTokens = countTokens(scenario.aiSdk);
  const openuiTokens = countTokens(scenario.openui);

  return {
    scenario: scenario.name,
    jsonTokens,
    aiSdkTokens,
    openuiTokens,
    openuiVsJson: Number(((1 - openuiTokens / jsonTokens) * 100).toFixed(1)),
    openuiVsAiSdk: Number(((1 - openuiTokens / aiSdkTokens) * 100).toFixed(1)),
  };
});

const totals = rows.reduce(
  (acc, row) => ({
    jsonTokens: acc.jsonTokens + row.jsonTokens,
    aiSdkTokens: acc.aiSdkTokens + row.aiSdkTokens,
    openuiTokens: acc.openuiTokens + row.openuiTokens,
  }),
  { jsonTokens: 0, aiSdkTokens: 0, openuiTokens: 0 },
);

const totalRow = {
  scenario: "total",
  jsonTokens: totals.jsonTokens,
  aiSdkTokens: totals.aiSdkTokens,
  openuiTokens: totals.openuiTokens,
  openuiVsJson: Number(
    ((1 - totals.openuiTokens / totals.jsonTokens) * 100).toFixed(1),
  ),
  openuiVsAiSdk: Number(
    ((1 - totals.openuiTokens / totals.aiSdkTokens) * 100).toFixed(1),
  ),
};

const allRows = [...rows, totalRow];

console.log(
  "| Scenario | JSON tokens | AI SDK tool-output tokens | OpenUI Lang tokens | OpenUI vs JSON | OpenUI vs AI SDK |",
);
console.log("|---|---:|---:|---:|---:|---:|");
for (const row of allRows) {
  console.log(
    `| ${row.scenario} | ${row.jsonTokens} | ${row.aiSdkTokens} | ${row.openuiTokens} | ${row.openuiVsJson}% fewer | ${row.openuiVsAiSdk}% fewer |`,
  );
}

const monthlyRequests = 1_000_000;
const outputPricePerMillion = 1.6;

console.log(
  "\nCost projection at 1M generated UI responses/month using GPT-4.1 mini output pricing:",
);
for (const row of allRows.filter((r) => r.scenario === "total")) {
  const jsonCost =
    (row.jsonTokens * monthlyRequests * outputPricePerMillion) / 1_000_000;
  const aiSdkCost =
    (row.aiSdkTokens * monthlyRequests * outputPricePerMillion) / 1_000_000;
  const openuiCost =
    (row.openuiTokens * monthlyRequests * outputPricePerMillion) / 1_000_000;
  console.log(`JSON output: $${jsonCost.toFixed(2)}`);
  console.log(`AI SDK-style tool output: $${aiSdkCost.toFixed(2)}`);
  console.log(`OpenUI Lang output: $${openuiCost.toFixed(2)}`);
}
