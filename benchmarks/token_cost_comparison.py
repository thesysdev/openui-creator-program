#!/usr/bin/env python3
"""Reproducible token-count fixtures for the OpenUI token-cost article.

Run with:
    python3 -m pip install tiktoken
    python3 benchmarks/token_cost_comparison.py
"""

from __future__ import annotations

import json
import warnings
from dataclasses import dataclass

warnings.filterwarnings("ignore", category=Warning, module="urllib3")

import tiktoken


@dataclass(frozen=True)
class Fixture:
    name: str
    openui_lang: str
    json_payload: dict
    ai_sdk_payload: dict


FIXTURES = [
    Fixture(
        name="Renewal risk review",
        openui_lang="""
<Panel title="Renewal risk review">
  <Metric label="At-risk ARR" value="$184k" tone="warning" />
  <Table columns={["Account","Risk","Reason","Action"]} rows={[
    ["Northstar","High","No exec sponsor","Schedule call"],
    ["Luma","Medium","Usage down 23%","Send playbook"],
    ["Atlas","Low","Expansion open","Create quote"]
  ]} />
  <Actions items={["Assign CSM","Export CSV","Create renewal plan"]} />
</Panel>
""",
        json_payload={
            "component": "Panel",
            "props": {
                "title": "Renewal risk review",
                "children": [
                    {
                        "component": "Metric",
                        "props": {
                            "label": "At-risk ARR",
                            "value": "$184k",
                            "tone": "warning",
                        },
                    },
                    {
                        "component": "Table",
                        "props": {
                            "columns": ["Account", "Risk", "Reason", "Action"],
                            "rows": [
                                ["Northstar", "High", "No exec sponsor", "Schedule call"],
                                ["Luma", "Medium", "Usage down 23%", "Send playbook"],
                                ["Atlas", "Low", "Expansion open", "Create quote"],
                            ],
                        },
                    },
                    {
                        "component": "Actions",
                        "props": {
                            "items": [
                                "Assign CSM",
                                "Export CSV",
                                "Create renewal plan",
                            ]
                        },
                    },
                ],
            },
        },
        ai_sdk_payload={
            "toolCallId": "call_renewal_review",
            "toolName": "renderComponent",
            "args": {
                "component": "Panel",
                "props": {
                    "title": "Renewal risk review",
                    "blocks": [
                        {
                            "type": "metric",
                            "label": "At-risk ARR",
                            "value": "$184k",
                            "tone": "warning",
                        },
                        {
                            "type": "table",
                            "columns": ["Account", "Risk", "Reason", "Action"],
                            "rows": [
                                {
                                    "account": "Northstar",
                                    "risk": "High",
                                    "reason": "No exec sponsor",
                                    "action": "Schedule call",
                                },
                                {
                                    "account": "Luma",
                                    "risk": "Medium",
                                    "reason": "Usage down 23%",
                                    "action": "Send playbook",
                                },
                                {
                                    "account": "Atlas",
                                    "risk": "Low",
                                    "reason": "Expansion open",
                                    "action": "Create quote",
                                },
                            ],
                        },
                        {
                            "type": "actions",
                            "items": [
                                "Assign CSM",
                                "Export CSV",
                                "Create renewal plan",
                            ],
                        },
                    ],
                },
            },
        },
    ),
    Fixture(
        name="Onboarding checklist",
        openui_lang="""
<Stepper title="Workspace setup" current={2}>
  <Step label="Connect data source" status="done" />
  <Step label="Invite reviewers" status="active">
    <Form fields={["Reviewer email","Role","Due date"]} submit="Send invite" />
  </Step>
  <Step label="Publish workflow" status="blocked" note="Needs one reviewer" />
</Stepper>
""",
        json_payload={
            "component": "Stepper",
            "props": {
                "title": "Workspace setup",
                "current": 2,
                "steps": [
                    {"label": "Connect data source", "status": "done"},
                    {
                        "label": "Invite reviewers",
                        "status": "active",
                        "children": [
                            {
                                "component": "Form",
                                "props": {
                                    "fields": [
                                        "Reviewer email",
                                        "Role",
                                        "Due date",
                                    ],
                                    "submit": "Send invite",
                                },
                            }
                        ],
                    },
                    {
                        "label": "Publish workflow",
                        "status": "blocked",
                        "note": "Needs one reviewer",
                    },
                ],
            },
        },
        ai_sdk_payload={
            "toolCallId": "call_workspace_setup",
            "toolName": "renderComponent",
            "args": {
                "component": "Stepper",
                "props": {
                    "title": "Workspace setup",
                    "current": 2,
                    "steps": [
                        {
                            "id": "connect_data_source",
                            "label": "Connect data source",
                            "status": "done",
                        },
                        {
                            "id": "invite_reviewers",
                            "label": "Invite reviewers",
                            "status": "active",
                            "form": {
                                "fields": [
                                    {"name": "reviewer_email", "label": "Reviewer email"},
                                    {"name": "role", "label": "Role"},
                                    {"name": "due_date", "label": "Due date"},
                                ],
                                "submitLabel": "Send invite",
                            },
                        },
                        {
                            "id": "publish_workflow",
                            "label": "Publish workflow",
                            "status": "blocked",
                            "note": "Needs one reviewer",
                        },
                    ],
                },
            },
        },
    ),
    Fixture(
        name="Support triage",
        openui_lang="""
<TriageBoard title="Support queue">
  <Summary text="9 tickets need action; 3 are billing blockers." />
  <Kanban columns={[
    ["Urgent", ["Refund failed", "Invoice locked", "Enterprise outage"]],
    ["Waiting", ["Need logs", "Customer replied"]],
    ["Done", ["Password reset", "Plan changed"]]
  ]} />
  <Button action="escalate_billing" label="Escalate billing blockers" />
</TriageBoard>
""",
        json_payload={
            "component": "TriageBoard",
            "props": {
                "title": "Support queue",
                "children": [
                    {
                        "component": "Summary",
                        "props": {
                            "text": "9 tickets need action; 3 are billing blockers."
                        },
                    },
                    {
                        "component": "Kanban",
                        "props": {
                            "columns": [
                                {
                                    "title": "Urgent",
                                    "cards": [
                                        "Refund failed",
                                        "Invoice locked",
                                        "Enterprise outage",
                                    ],
                                },
                                {
                                    "title": "Waiting",
                                    "cards": ["Need logs", "Customer replied"],
                                },
                                {
                                    "title": "Done",
                                    "cards": ["Password reset", "Plan changed"],
                                },
                            ]
                        },
                    },
                    {
                        "component": "Button",
                        "props": {
                            "action": "escalate_billing",
                            "label": "Escalate billing blockers",
                        },
                    },
                ],
            },
        },
        ai_sdk_payload={
            "toolCallId": "call_support_triage",
            "toolName": "renderComponent",
            "args": {
                "component": "TriageBoard",
                "props": {
                    "title": "Support queue",
                    "summary": "9 tickets need action; 3 are billing blockers.",
                    "columns": [
                        {
                            "id": "urgent",
                            "title": "Urgent",
                            "cards": [
                                "Refund failed",
                                "Invoice locked",
                                "Enterprise outage",
                            ],
                        },
                        {
                            "id": "waiting",
                            "title": "Waiting",
                            "cards": ["Need logs", "Customer replied"],
                        },
                        {
                            "id": "done",
                            "title": "Done",
                            "cards": ["Password reset", "Plan changed"],
                        },
                    ],
                    "primaryAction": {
                        "action": "escalate_billing",
                        "label": "Escalate billing blockers",
                    },
                },
            },
        },
    ),
]


def compact_json(payload: dict) -> str:
    return json.dumps(payload, separators=(",", ":"), ensure_ascii=False)


def count_tokens(encoding: tiktoken.Encoding, value: str) -> int:
    return len(encoding.encode(value.strip()))


def main() -> None:
    encoding = tiktoken.get_encoding("o200k_base")
    rows = []

    for fixture in FIXTURES:
        openui_tokens = count_tokens(encoding, fixture.openui_lang)
        json_tokens = count_tokens(encoding, compact_json(fixture.json_payload))
        ai_sdk_tokens = count_tokens(encoding, compact_json(fixture.ai_sdk_payload))
        rows.append((fixture.name, openui_tokens, json_tokens, ai_sdk_tokens))

    print("| Fixture | OpenUI Lang | Compact JSON | AI SDK-style tool envelope |")
    print("| --- | ---: | ---: | ---: |")
    for row in rows:
        print(f"| {row[0]} | {row[1]} | {row[2]} | {row[3]} |")

    openui_total = sum(row[1] for row in rows)
    json_total = sum(row[2] for row in rows)
    ai_sdk_total = sum(row[3] for row in rows)
    print(f"| **Total** | **{openui_total}** | **{json_total}** | **{ai_sdk_total}** |")
    print()
    print("Savings vs compact JSON: {:.1%}".format(1 - openui_total / json_total))
    print("Savings vs AI SDK-style envelope: {:.1%}".format(1 - openui_total / ai_sdk_total))


if __name__ == "__main__":
    main()
