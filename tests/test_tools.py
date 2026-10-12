from __future__ import annotations

from multi_agent_prod.tools import check_contact_rules, load_customer, retrieve


def test_retrieve_grounds_known_topic():
    ev = retrieve("term deposit options and rate", top_k=3)
    assert ev, "expected grounding for a known topic"
    assert ev[0].source_id == "COMMS-01"
    # scores are sorted descending
    assert ev == sorted(ev, key=lambda e: (-e.score, e.source_id))


def test_retrieve_refuses_unknown_topic():
    ev = retrieve("crypto staking rewards program apr", top_k=3)
    assert ev == []


def test_contact_rules_flag_opt_out_and_vulnerability():
    customer = load_customer("QUIET001")
    flags = check_contact_rules(customer)
    codes = {f.code for f in flags}
    assert "CR-OPT" in codes
    assert "CR-VULN" in codes


def test_contact_rules_clear_for_engaged_customer():
    customer = load_customer("RIVER001")
    assert check_contact_rules(customer) == []
