from __future__ import annotations

import json
from pathlib import Path

from evals.run_evals import main as run_evals_main


def test_eval_gate_passes_all_cases():
    assert run_evals_main() == 0


def test_eval_report_written():
    run_evals_main()
    report = Path(__file__).resolve().parents[1] / "evals" / "reports" / "last_run.json"
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["passed"] == payload["total"]
