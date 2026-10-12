"""Deterministic mock model.

No weights, no network, no randomness. It reads the role tag and a few markers
in the prompt and returns the structured output the agents parse. This is what
makes tests, evals and CI reproducible to the byte. The *same* agent code runs
against a real self-hosted model by swapping the client (see ``openai_compat``).
"""

from __future__ import annotations


class DeterministicLLM:
    name = "mock-deterministic"

    def complete(self, system: str, user: str) -> str:
        text = f"{system}\n{user}".lower()

        if "role: critic" in text:
            return self._critic(text)
        if "role: drafter" in text:
            return self._drafter(text)
        if "role: planner" in text:
            return self._planner(text)
        return "OK"

    # ---- role behaviours ------------------------------------------------
    @staticmethod
    def _planner(text: str) -> str:
        return (
            "PLAN:\n"
            "1. retrieve grounding from policy corpus\n"
            "2. check contact rules for the customer (if any)\n"
            "3. draft a grounded answer or refuse, then critique\n"
            "ROUTE: orchestrate"
        )

    @staticmethod
    def _drafter(text: str) -> str:
        # A grounded, non-committal, policy-safe draft. Citations are appended
        # by the drafter agent from real evidence ids, so grounding never
        # depends on the model inventing a reference.
        return (
            "DRAFT: Based only on published product and policy information, "
            "here is a plain-language summary with no guaranteed outcomes and "
            "no pressure to act.\n"
            "DECISION: draft"
        )

    @staticmethod
    def _critic(text: str) -> str:
        if "sec-injection" in text or "injection" in text:
            return (
                "VERDICT: escalate\n"
                "REASON: instruction-injection detected in source content; a "
                "human must review before anything proceeds."
            )
        if "cr-opt" in text or "cr-vuln" in text or "cr-freq" in text:
            return (
                "VERDICT: escalate\n"
                "REASON: contact-rule or extra-care flag present; a human must "
                "decide, not the agent."
            )
        if "[comms" not in text and "[pol" not in text:
            return (
                "VERDICT: revise\n"
                "REASON: the draft is not grounded in a cited policy."
            )
        return (
            "VERDICT: pass\n"
            "REASON: grounded in cited policy and policy-safe; a human must "
            "still approve before it is customer-ready."
        )
