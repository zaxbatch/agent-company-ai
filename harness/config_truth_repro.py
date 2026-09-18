#!/usr/bin/env python3
"""config_truth_repro.py - "config flags are lying" reproduction recorder.

Reproduces, verbatim, what the live agent tools return for the money-path calls
when config.yaml claims an integration is enabled but has no credentials.

Wiring mirrors `src/agent_company_ai/core/company.py` exactly (same setters, same
order, same guard conditions), so the output here is the output an agent sees.

Usage:
    venv/bin/python harness/config_truth_repro.py
    venv/bin/python harness/config_truth_repro.py stripe gumroad calcom invoice revenue

Always exits 0 - this is a repro recorder, not a gate.
`scripts/integration_truth_check.py` is the gate.
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from agent_company_ai.config import load_config  # noqa: E402
from agent_company_ai.storage.database import Database  # noqa: E402

CONFIG_PATH = ROOT / ".agent-company-ai" / "default" / "config.yaml"


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


async def main(which: list) -> int:
    _load_dotenv(ROOT / ".env")

    config = load_config(CONFIG_PATH)
    intg = config.integrations

    db = Database(Path("/tmp/config-truth-repro.db"))
    await db.connect()

    from agent_company_ai.tools import booking_tool, gumroad_tools, invoice_tool, stripe_tools  # noqa: F401
    from agent_company_ai.tools.registry import ToolRegistry

    # --- wiring copied from core/company.py (guards included) ---
    if intg.stripe.enabled:
        stripe_tools.set_stripe_config(api_key=intg.stripe.api_key)
    stripe_tools.set_stripe_db(db)
    stripe_tools.set_stripe_rate_limits(intg.rate_limits.max_payment_amount_usd)

    if intg.gumroad.enabled:
        gumroad_tools.set_gumroad_config(access_token=intg.gumroad.access_token)
    gumroad_tools.set_gumroad_db(db)

    invoice_tool.set_invoice_company_dir(ROOT / ".agent-company-ai" / "default")
    if intg.invoice.enabled:
        invoice_tool.set_invoice_config(
            company_name=intg.invoice.company_name,
            company_address=intg.invoice.company_address,
            payment_instructions=intg.invoice.payment_instructions,
            currency=intg.invoice.currency,
        )
    invoice_tool.set_invoice_db(db)

    if intg.calcom.enabled:
        booking_tool.set_booking_config(
            api_key=intg.calcom.api_key,
            default_duration=intg.calcom.default_duration,
        )
    booking_tool.set_booking_db(db)

    reg = ToolRegistry.get()

    print("=" * 78)
    print("CONFIG-AS-WRITTEN  (.agent-company-ai/default/config.yaml)")
    print("=" * 78)
    print("  stripe.enabled       = %s" % intg.stripe.enabled)
    print("  stripe.api_key       = %s" % ("<set>" if intg.stripe.api_key else "<EMPTY>"))
    print("  gumroad.enabled      = %s" % intg.gumroad.enabled)
    print("  gumroad.access_token = %s" % ("<set>" if intg.gumroad.access_token else "<EMPTY>"))
    print("  calcom.enabled       = %s" % intg.calcom.enabled)
    print("  calcom.api_key       = %s" % ("<set>" if intg.calcom.api_key else "<EMPTY>"))
    print("  invoice.enabled      = %s" % intg.invoice.enabled)
    print("  invoice.company_name = %r" % intg.invoice.company_name)
    print("  invoice.company_addr = %r" % intg.invoice.company_address)
    print("  invoice.payment_inst = %r" % intg.invoice.payment_instructions)
    print()

    calls = [
        ("stripe", "check_payments", {}),
        ("gumroad", "list_gumroad_products", {}),
        ("calcom", "list_bookings", {}),
        ("invoice", "list_invoices", {}),
        ("revenue", "check_revenue", {}),
    ]

    for tag, name, kwargs in calls:
        if which and tag not in which:
            continue
        tool = reg.get_tool(name)
        print("-" * 78)
        print("%s()" % name)
        print("-" * 78)
        if tool is None:
            print("  >>> TOOL NOT REGISTERED in this process: %s" % name)
            print()
            continue
        try:
            out = await tool.execute(**kwargs)
        except Exception as exc:  # noqa: BLE001
            out = "Tool error: %s: %s" % (type(exc).__name__, exc)
        print("  >>> %s" % out)
        print()

    await db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main(sys.argv[1:])))
