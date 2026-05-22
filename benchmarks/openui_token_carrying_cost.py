#!/usr/bin/env python3
"""Offline cost model for the OpenUI token-cost article.

The token counts are copied from the OpenUI public benchmark table:
https://github.com/thesysdev/openui/tree/main/benchmarks

This script intentionally avoids network calls and package installs. It is a
small arithmetic check for the article's cost projection tables, not a tokenizer.
"""

from __future__ import annotations

from dataclasses import dataclass


PRICE_PER_MILLION_OUTPUT_TOKENS_USD = {
    "low_cost": 0.60,
    "mid_tier": 10.00,
    "premium": 30.00,
}


@dataclass(frozen=True)
class Scenario:
    name: str
    openui_lang: int
    yaml: int
    vercel_json_render: int
    thesys_c1_json: int


SCENARIOS = [
    Scenario("simple-table", 148, 316, 340, 357),
    Scenario("chart-with-data", 231, 464, 520, 516),
    Scenario("contact-form", 294, 762, 893, 849),
    Scenario("dashboard", 1226, 2128, 2247, 2261),
    Scenario("pricing-page", 1195, 2230, 2487, 2379),
    Scenario("settings-panel", 540, 1077, 1244, 1205),
    Scenario("e-commerce-product", 1166, 2145, 2449, 2381),
]


def monthly_cost(tokens_per_generation: int, generations_per_month: int, price: float) -> float:
    return tokens_per_generation * generations_per_month / 1_000_000 * price


def pct_savings(baseline: int, candidate: int) -> float:
    return (baseline - candidate) / baseline * 100


def main() -> None:
    totals = {
        "OpenUI Lang": sum(s.openui_lang for s in SCENARIOS),
        "YAML": sum(s.yaml for s in SCENARIOS),
        "Vercel JSON-Render": sum(s.vercel_json_render for s in SCENARIOS),
        "Thesys C1 JSON": sum(s.thesys_c1_json for s in SCENARIOS),
    }

    print("# Token totals from OpenUI benchmark fixtures")
    for label, tokens in totals.items():
        print(f"{label}: {tokens:,}")

    print("\n# Savings versus OpenUI Lang")
    for label in ("YAML", "Vercel JSON-Render", "Thesys C1 JSON"):
        print(f"{label}: {pct_savings(totals[label], totals['OpenUI Lang']):.1f}%")

    print("\n# Monthly output-token cost at 100,000 generated UI responses")
    for model_tier, price in PRICE_PER_MILLION_OUTPUT_TOKENS_USD.items():
        openui_cost = monthly_cost(totals["OpenUI Lang"], 100_000, price)
        vercel_cost = monthly_cost(totals["Vercel JSON-Render"], 100_000, price)
        c1_cost = monthly_cost(totals["Thesys C1 JSON"], 100_000, price)
        print(
            f"{model_tier}: OpenUI=${openui_cost:,.2f}, "
            f"Vercel JSON-Render=${vercel_cost:,.2f}, "
            f"Thesys C1 JSON=${c1_cost:,.2f}"
        )

    print("\n# Sensitivity: retry rate on Vercel JSON-Render at mid-tier pricing")
    base = totals["Vercel JSON-Render"]
    for retry_rate in (0.01, 0.03, 0.05, 0.10):
        effective_tokens = int(base * (1 + retry_rate))
        cost = monthly_cost(effective_tokens, 100_000, PRICE_PER_MILLION_OUTPUT_TOKENS_USD["mid_tier"])
        print(f"{retry_rate:.0%} retry rate: {effective_tokens:,} tokens/response, ${cost:,.2f}/month")


if __name__ == "__main__":
    main()
