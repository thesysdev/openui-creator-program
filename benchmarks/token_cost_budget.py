#!/usr/bin/env python3
"""Count output tokens for equivalent generated-UI payloads.

Run with:
  uv run --with tiktoken python benchmarks/token_cost_budget.py
"""

from __future__ import annotations

from dataclasses import dataclass

try:
    import tiktoken
except ImportError as exc:  # pragma: no cover - friendly CLI failure
    raise SystemExit(
        "Install tiktoken first, or run with: "
        "uv run --with tiktoken python benchmarks/token_cost_budget.py"
    ) from exc


OUTPUT_PRICE_PER_MILLION = 1.60
ENCODING = "o200k_base"


@dataclass(frozen=True)
class Scenario:
    name: str
    openui_lang: str
    compact_json: str
    ai_sdk_envelope: str


SCENARIOS = [
    Scenario(
        name="Renewal risk dashboard",
        openui_lang="""root = Stack([title, summary, table, actions])
title = TextContent("Renewal risk review", "large-heavy")
summary = Cards([risk, blocked, upsell])
risk = Card("High risk", "$182k", "3 accounts need action")
blocked = Card("Legal blocked", "2", "Waiting on redlines")
upsell = Card("Expansion", "$48k", "Qualified this week")
table = Table([acct, owner, riskScore, next])
acct = Col("Account", ["Northwind", "Globex", "Initech"])
owner = Col("Owner", ["Mina", "Raj", "Tess"])
riskScore = Col("Risk", [87, 74, 68], "number")
next = Col("Next action", ["Escalate legal", "Book exec call", "Send ROI memo"])
actions = Buttons([save, export], "row")
save = Button("Save view", "action:save", "primary")
export = Button("Export CSV", "action:export", "secondary")""",
        compact_json="""{
  "component": "Stack",
  "props": {
    "children": [
      {"component": "TextContent", "props": {"text": "Renewal risk review", "size": "large-heavy"}},
      {"component": "Cards", "props": {"children": [
        {"component": "Card", "props": {"title": "High risk", "value": "$182k", "description": "3 accounts need action"}},
        {"component": "Card", "props": {"title": "Legal blocked", "value": "2", "description": "Waiting on redlines"}},
        {"component": "Card", "props": {"title": "Expansion", "value": "$48k", "description": "Qualified this week"}}
      ]}},
      {"component": "Table", "props": {"columns": [
        {"label": "Account", "values": ["Northwind", "Globex", "Initech"]},
        {"label": "Owner", "values": ["Mina", "Raj", "Tess"]},
        {"label": "Risk", "values": [87, 74, 68], "type": "number"},
        {"label": "Next action", "values": ["Escalate legal", "Book exec call", "Send ROI memo"]}
      ]}},
      {"component": "Buttons", "props": {"layout": "row", "children": [
        {"component": "Button", "props": {"label": "Save view", "action": "action:save", "variant": "primary"}},
        {"component": "Button", "props": {"label": "Export CSV", "action": "action:export", "variant": "secondary"}}
      ]}}
    ]
  }
}""",
        ai_sdk_envelope="""{
  "id": "msg_renewal_risk",
  "role": "assistant",
  "parts": [{
    "type": "tool-renderDashboard",
    "state": "output-available",
    "toolCallId": "call_dashboard_01",
    "input": {"intent": "show renewal risk review"},
    "output": {
      "ui": {
        "type": "Stack",
        "props": {
          "children": [
            {"type": "TextContent", "props": {"text": "Renewal risk review", "size": "large-heavy"}},
            {"type": "Cards", "props": {"items": [
              {"title": "High risk", "value": "$182k", "description": "3 accounts need action"},
              {"title": "Legal blocked", "value": "2", "description": "Waiting on redlines"},
              {"title": "Expansion", "value": "$48k", "description": "Qualified this week"}
            ]}},
            {"type": "Table", "props": {"columns": [
              {"label": "Account", "values": ["Northwind", "Globex", "Initech"]},
              {"label": "Owner", "values": ["Mina", "Raj", "Tess"]},
              {"label": "Risk", "values": [87, 74, 68], "type": "number"},
              {"label": "Next action", "values": ["Escalate legal", "Book exec call", "Send ROI memo"]}
            ]}},
            {"type": "Buttons", "props": {"layout": "row", "children": [
              {"type": "Button", "props": {"label": "Save view", "action": "action:save", "variant": "primary"}},
              {"type": "Button", "props": {"label": "Export CSV", "action": "action:export", "variant": "secondary"}}
            ]}}
          ]
        }
      }
    }
  }]
}""",
    ),
    Scenario(
        name="Validated onboarding form",
        openui_lang="""root = Stack([title, form, help])
title = TextContent("Create workspace", "large-heavy")
form = Form([name, url, region, submit])
name = TextInput("Workspace name", "workspaceName", "Acme AI")
url = TextInput("Public URL", "workspaceUrl", "https://acme.example")
region = Select("Region", "region", ["us-east", "eu-west", "ap-south"], "us-east")
submit = Button("Create workspace", "action:create-workspace", "primary")
help = Callout("Use a production domain if this workspace will receive webhooks.", "info")""",
        compact_json="""{
  "component": "Stack",
  "props": {
    "children": [
      {"component": "TextContent", "props": {"text": "Create workspace", "size": "large-heavy"}},
      {"component": "Form", "props": {"children": [
        {"component": "TextInput", "props": {"label": "Workspace name", "name": "workspaceName", "placeholder": "Acme AI"}},
        {"component": "TextInput", "props": {"label": "Public URL", "name": "workspaceUrl", "placeholder": "https://acme.example"}},
        {"component": "Select", "props": {"label": "Region", "name": "region", "options": ["us-east", "eu-west", "ap-south"], "defaultValue": "us-east"}},
        {"component": "Button", "props": {"label": "Create workspace", "action": "action:create-workspace", "variant": "primary"}}
      ]}},
      {"component": "Callout", "props": {"message": "Use a production domain if this workspace will receive webhooks.", "tone": "info"}}
    ]
  }
}""",
        ai_sdk_envelope="""{
  "id": "msg_workspace_form",
  "role": "assistant",
  "parts": [{
    "type": "tool-renderForm",
    "state": "output-available",
    "toolCallId": "call_form_01",
    "input": {"intent": "create workspace form"},
    "output": {
      "ui": {
        "type": "Stack",
        "props": {
          "children": [
            {"type": "TextContent", "props": {"text": "Create workspace", "size": "large-heavy"}},
            {"type": "Form", "props": {"children": [
              {"type": "TextInput", "props": {"label": "Workspace name", "name": "workspaceName", "placeholder": "Acme AI"}},
              {"type": "TextInput", "props": {"label": "Public URL", "name": "workspaceUrl", "placeholder": "https://acme.example"}},
              {"type": "Select", "props": {"label": "Region", "name": "region", "options": ["us-east", "eu-west", "ap-south"], "defaultValue": "us-east"}},
              {"type": "Button", "props": {"label": "Create workspace", "action": "action:create-workspace", "variant": "primary"}}
            ]}},
            {"type": "Callout", "props": {"message": "Use a production domain if this workspace will receive webhooks.", "tone": "info"}}
          ]
        }
      }
    }
  }]
}""",
    ),
    Scenario(
        name="Support triage queue",
        openui_lang="""root = Stack([title, filters, queue])
title = TextContent("Support triage", "large-heavy")
filters = Chips(["Billing", "Enterprise", "SLA breach"], "Billing")
queue = Table([ticket, customer, severity, owner])
ticket = Col("Ticket", ["#4182", "#4188", "#4190"])
customer = Col("Customer", ["Rill Labs", "Blue Oak", "Vertex"])
severity = Col("Severity", ["P1", "P2", "P2"])
owner = Col("Owner", ["Sam", "No owner", "Priya"])""",
        compact_json="""{
  "component": "Stack",
  "props": {
    "children": [
      {"component": "TextContent", "props": {"text": "Support triage", "size": "large-heavy"}},
      {"component": "Chips", "props": {"items": ["Billing", "Enterprise", "SLA breach"], "selected": "Billing"}},
      {"component": "Table", "props": {"columns": [
        {"label": "Ticket", "values": ["#4182", "#4188", "#4190"]},
        {"label": "Customer", "values": ["Rill Labs", "Blue Oak", "Vertex"]},
        {"label": "Severity", "values": ["P1", "P2", "P2"]},
        {"label": "Owner", "values": ["Sam", "No owner", "Priya"]}
      ]}}
    ]
  }
}""",
        ai_sdk_envelope="""{
  "id": "msg_support_triage",
  "role": "assistant",
  "parts": [{
    "type": "tool-renderQueue",
    "state": "output-available",
    "toolCallId": "call_queue_01",
    "input": {"intent": "support triage queue"},
    "output": {
      "ui": {
        "type": "Stack",
        "props": {
          "children": [
            {"type": "TextContent", "props": {"text": "Support triage", "size": "large-heavy"}},
            {"type": "Chips", "props": {"items": ["Billing", "Enterprise", "SLA breach"], "selected": "Billing"}},
            {"type": "Table", "props": {"columns": [
              {"label": "Ticket", "values": ["#4182", "#4188", "#4190"]},
              {"label": "Customer", "values": ["Rill Labs", "Blue Oak", "Vertex"]},
              {"label": "Severity", "values": ["P1", "P2", "P2"]},
              {"label": "Owner", "values": ["Sam", "No owner", "Priya"]}
            ]}}
          ]
        }
      }
    }
  }]
}""",
    ),
]


def count_tokens(text: str) -> int:
    enc = tiktoken.get_encoding(ENCODING)
    return len(enc.encode(text))


def cost(tokens: int, requests: int) -> float:
    return tokens * requests / 1_000_000 * OUTPUT_PRICE_PER_MILLION


def savings(baseline: int, candidate: int) -> float:
    return (baseline - candidate) / baseline * 100


def main() -> None:
    totals = {"openui": 0, "json": 0, "ai_sdk": 0}
    print("| Scenario | OpenUI Lang | Compact JSON | AI SDK-style envelope |")
    print("| --- | ---: | ---: | ---: |")
    for scenario in SCENARIOS:
        openui = count_tokens(scenario.openui_lang)
        compact_json = count_tokens(scenario.compact_json)
        ai_sdk = count_tokens(scenario.ai_sdk_envelope)
        totals["openui"] += openui
        totals["json"] += compact_json
        totals["ai_sdk"] += ai_sdk
        print(f"| {scenario.name} | {openui} | {compact_json} | {ai_sdk} |")

    print(
        f"| **Total** | **{totals['openui']}** | "
        f"**{totals['json']}** | **{totals['ai_sdk']}** |"
    )
    print()
    print(f"Savings vs compact JSON: {savings(totals['json'], totals['openui']):.1f}%")
    print(
        f"Savings vs AI SDK-style envelope: "
        f"{savings(totals['ai_sdk'], totals['openui']):.1f}%"
    )
    print()
    print(
        f"Output-token cost model: ${OUTPUT_PRICE_PER_MILLION:.2f} "
        "per 1M output tokens"
    )
    print("| Monthly generated UIs | OpenUI Lang | Compact JSON | AI SDK-style envelope |")
    print("| ---: | ---: | ---: | ---: |")
    for requests in (10_000, 100_000, 1_000_000):
        print(
            f"| {requests:,} | ${cost(totals['openui'], requests):.2f} | "
            f"${cost(totals['json'], requests):.2f} | "
            f"${cost(totals['ai_sdk'], requests):.2f} |"
        )


if __name__ == "__main__":
    main()
