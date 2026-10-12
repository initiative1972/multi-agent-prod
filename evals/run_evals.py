"""Trajectory evals: score whole multi-step runs, not single turns.

For each case we run the full trajectory and check the properties that actually
matter in production:

* decision          - did it draft / refuse / escalate as expected?
* grounded          - is a draft backed by retrieved evidence (never invented)?
* customer_ready    - did anything become customer-ready only via a human?
* flags             - were the right policy/safety flags raised?
* bounded           - did reflection stay within its round budget?

Exit code is non-zero if any case fails, so this doubles as the CI gate.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from multi_agent_prod.runtime import run_desk  # noqa: E402


def _evaluate(case: dict) -> dict:
    expect = case["expect"]
    t0 = time.perf_counter()
    bb = run_desk(
        case["goal"],
        customer_id=case.get("customer_id"),
        hitl_action=case.get("hitl_action"),
        persist=False,
    )
    latency_ms = round((time.perf_counter() - t0) * 1000.0, 1)

    grounded = len(bb.evidence) > 0
    customer_ready = bb.customer_ready is not None
    flag_codes = {f.code for f in bb.flags}

    checks = {
        "decision": bb.decision.value == expect["decision"],
        "grounded": grounded == expect["grounded"],
        "customer_ready": customer_ready == expect["customer_ready"],
        "flags": all(code in flag_codes for code in expect.get("flags_include", [])),
        "bounded": bb.reflection_rounds <= expect.get("max_reflection_rounds", 2),
    }
    return {
        "id": case["id"],
        "passed": all(checks.values()),
        "checks": checks,
        "decision": bb.decision.value,
        "flags": sorted(flag_codes),
        "evidence_n": len(bb.evidence),
        "hops": bb.hops,
        "reflection_rounds": bb.reflection_rounds,
        "latency_ms": latency_ms,
    }


def main() -> int:
    cases = json.loads((Path(__file__).parent / "cases.json").read_text(encoding="utf-8"))
    results = [_evaluate(c) for c in cases]
    passed = sum(1 for r in results if r["passed"])

    payload = {"passed": passed, "total": len(cases), "results": results}
    report_dir = Path(__file__).parent / "reports"
    report_dir.mkdir(exist_ok=True)
    (report_dir / "last_run.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )
    print(json.dumps(payload, indent=2))
    return 0 if passed == len(cases) else 1


if __name__ == "__main__":
    raise SystemExit(main())
