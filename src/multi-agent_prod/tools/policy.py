"""Deterministic contact-rule checks over synthetic customer data."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from multi_agent_prod.config import get_settings
from multi_agent_prod.state import Flag


@lru_cache(maxsize=1)
def _load_all() -> dict:
    path = Path(get_settings().customers_file)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_customer(customer_id: str | None) -> dict | None:
    if not customer_id:
        return None
    return _load_all().get(customer_id)


def check_contact_rules(customer: dict | None) -> list[Flag]:
    """Return hard-rule flags for a customer. Empty list means clear to draft.

    Mirrors COMMS-02: opt-out, frequency cap, extra-care/vulnerability.
    """
    if not customer:
        return []

    flags: list[Flag] = []
    if not customer.get("opted_in", False):
        flags.append(
            Flag("CR-OPT", "customer has not opted in / has opted out", "high")
        )
    cap = int(customer.get("frequency_cap_30d", 0))
    used = int(customer.get("contacts_30d", 0))
    if cap and used >= cap:
        flags.append(
            Flag("CR-FREQ", f"frequency cap reached ({used}/{cap} in 30d)", "medium")
        )
    if customer.get("extra_care", False):
        flags.append(
            Flag("CR-VULN", "extra-care / vulnerability indicator present", "high")
        )
    return flags
