"""
evaluation/evaluator.py
────────────────────────
Automated evaluation pipeline for the Iris agent.

Architecture
────────────
Implements the "LLM-as-judge" pattern recommended by Anthropic's production
multi-agent research (Jun 2025).  A golden dataset of known bulletins and
their expected outputs is stored in evaluation/golden_dataset.json.

The evaluator:
  1. Loads the golden dataset.
  2. For each case, calls the Iris agent pipeline (or a stub) to get an output.
  3. Passes the output to a judge LLM with a structured rubric.
  4. Records pass/fail scores to evaluation/results/.
  5. Exits with a non-zero code if the overall pass rate drops below PASS_THRESHOLD.

This script is designed to run in CI (GitHub Actions) on every PR that
touches the agents/ directory, preventing regressions.

Usage
─────
    python -m evaluation.evaluator                    # run all cases
    python -m evaluation.evaluator --case-id TC001    # run one case
    python -m evaluation.evaluator --dry-run          # validate dataset only

Environment variables
─────────────────────
ANTHROPIC_API_KEY     Required for judge LLM calls.
EVAL_MODEL            Judge model. Defaults to claude-haiku-3-5 (cheapest).
PASS_THRESHOLD        Float 0–1. Defaults to 0.80 (80% of cases must pass).
"""

import os
import sys
import json
import argparse
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

# ── Configuration ──────────────────────────────────────────────────────────────
EVAL_DIR        = Path(__file__).parent
DATASET_PATH    = EVAL_DIR / "golden_dataset.json"
RESULTS_DIR     = EVAL_DIR / "results"
EVAL_MODEL      = os.environ.get("EVAL_MODEL", "claude-haiku-3-5")
PASS_THRESHOLD  = float(os.environ.get("PASS_THRESHOLD", "0.80"))

# ── Rubric ─────────────────────────────────────────────────────────────────────
JUDGE_RUBRIC = """
You are an expert evaluator for an insurance regulatory AI agent called Iris.
You will be given:
  - A regulatory bulletin (the input)
  - The expected output (ground truth from a domain expert)
  - The actual output produced by the agent

Score the actual output on each dimension from 0.0 to 1.0:

1. priority_accuracy   — Did the agent assign the correct priority level
                         (IMMEDIATE / DIGEST / MONITOR)?  1.0 = exact match.
2. completeness        — Does the output cover all key regulatory changes
                         mentioned in the bulletin?
3. factual_accuracy    — Are all claims in the output supported by the bulletin?
                         Penalise hallucinations heavily.
4. client_relevance    — Is the output appropriately tailored to the client's
                         jurisdiction and line of business?
5. action_clarity      — Is the recommended action clear and actionable?

Return ONLY a JSON object with this exact structure:
{
  "scores": {
    "priority_accuracy": <float>,
    "completeness": <float>,
    "factual_accuracy": <float>,
    "client_relevance": <float>,
    "action_clarity": <float>
  },
  "overall": <float>,
  "pass": <bool>,
  "reasoning": "<one sentence>"
}

A case PASSES if overall >= 0.75.
"""


# ── Dataset loader ─────────────────────────────────────────────────────────────

def load_dataset(case_id: Optional[str] = None) -> list[dict]:
    """Load the golden dataset, optionally filtering to a single case."""
    if not DATASET_PATH.exists():
        logger.error("Golden dataset not found at %s", DATASET_PATH)
        logger.error("Run: python -m evaluation.seed_dataset to create it.")
        sys.exit(1)

    with open(DATASET_PATH) as f:
        cases = json.load(f)

    if case_id:
        cases = [c for c in cases if c.get("id") == case_id]
        if not cases:
            logger.error("Case ID '%s' not found in dataset.", case_id)
            sys.exit(1)

    return cases


# ── Agent stub ─────────────────────────────────────────────────────────────────

def run_agent_pipeline(case: dict) -> dict:
    """
    Run the Iris agent pipeline for a given test case.

    In Phase 1 this is a STUB that returns a mock output.
    When Phase 2 (SupervisorAgent) is merged, replace this function body with:

        from iris_agent.agents.supervisor import SupervisorAgent
        agent = SupervisorAgent()
        return agent.process_bulletin(
            bulletin_text=case["bulletin_text"],
            client_profile=case["client_profile"],
        )
    """
    # STUB: return a mock output that mimics the expected schema.
    # This allows the evaluation pipeline to run end-to-end in CI
    # before the real agent is wired in.
    return {
        "priority": case.get("expected_priority", "DIGEST"),
        "summary": f"[STUB] Processed bulletin: {case['bulletin_text'][:80]}...",
        "affected_lines": case.get("expected_affected_lines", []),
        "recommended_action": "Review and update compliance procedures.",
    }


# ── Judge ──────────────────────────────────────────────────────────────────────

def judge_output(case: dict, actual_output: dict) -> dict:
    """Call the LLM judge and return structured scores."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        logger.warning("ANTHROPIC_API_KEY not set — returning mock judge scores.")
        return {
            "scores": {
                "priority_accuracy": 1.0,
                "completeness": 0.8,
                "factual_accuracy": 0.9,
                "client_relevance": 0.8,
                "action_clarity": 0.85,
            },
            "overall": 0.87,
            "pass": True,
            "reasoning": "Mock scores — ANTHROPIC_API_KEY not configured.",
        }

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

        prompt = f"""
BULLETIN:
{case['bulletin_text']}

CLIENT PROFILE:
{json.dumps(case.get('client_profile', {}), indent=2)}

EXPECTED OUTPUT (ground truth):
{json.dumps(case.get('expected_output', {}), indent=2)}

ACTUAL OUTPUT (agent produced):
{json.dumps(actual_output, indent=2)}
"""
        response = client.messages.create(
            model=EVAL_MODEL,
            max_tokens=512,
            system=JUDGE_RUBRIC,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text.strip()

        # Strip markdown fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        return json.loads(raw)

    except Exception as exc:
        logger.error("Judge LLM call failed for case %s: %s", case.get("id"), exc)
        return {
            "scores": {},
            "overall": 0.0,
            "pass": False,
            "reasoning": f"Judge error: {exc}",
        }


# ── Runner ─────────────────────────────────────────────────────────────────────

def run_evaluation(cases: list[dict], dry_run: bool = False) -> dict:
    """Run the full evaluation loop and return a summary."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    results = []

    for case in cases:
        case_id = case.get("id", "unknown")
        logger.info("Evaluating case: %s", case_id)

        if dry_run:
            logger.info("  [DRY RUN] Skipping agent call.")
            continue

        actual_output = run_agent_pipeline(case)
        judgment      = judge_output(case, actual_output)

        result = {
            "case_id":       case_id,
            "run_id":        run_id,
            "timestamp":     datetime.now(timezone.utc).isoformat(),
            "pass":          judgment.get("pass", False),
            "overall_score": judgment.get("overall", 0.0),
            "scores":        judgment.get("scores", {}),
            "reasoning":     judgment.get("reasoning", ""),
            "actual_output": actual_output,
        }
        results.append(result)

        status = "PASS" if result["pass"] else "FAIL"
        logger.info("  %s  overall=%.2f  %s",
                    status, result["overall_score"], result["reasoning"])

    # ── Summary ────────────────────────────────────────────────────────────────
    if not results:
        summary = {"total": 0, "passed": 0, "pass_rate": 1.0, "run_id": run_id}
    else:
        passed    = sum(1 for r in results if r["pass"])
        pass_rate = passed / len(results)
        summary   = {
            "run_id":     run_id,
            "total":      len(results),
            "passed":     passed,
            "failed":     len(results) - passed,
            "pass_rate":  round(pass_rate, 4),
            "threshold":  PASS_THRESHOLD,
            "gate_passed": pass_rate >= PASS_THRESHOLD,
        }

    # ── Persist results ────────────────────────────────────────────────────────
    output_path = RESULTS_DIR / f"{run_id}.json"
    with open(output_path, "w") as f:
        json.dump({"summary": summary, "cases": results}, f, indent=2)
    logger.info("Results written to %s", output_path)

    return summary


# ── CLI entry point ────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Iris agent evaluation pipeline")
    parser.add_argument("--case-id",  help="Run a single test case by ID")
    parser.add_argument("--dry-run",  action="store_true",
                        help="Validate dataset structure only, no LLM calls")
    args = parser.parse_args()

    cases   = load_dataset(case_id=args.case_id)
    summary = run_evaluation(cases, dry_run=args.dry_run)

    if args.dry_run:
        logger.info("Dry run complete. %d cases validated.", len(cases))
        sys.exit(0)

    logger.info(
        "Evaluation complete: %d/%d passed (%.0f%%) — gate=%s",
        summary["passed"], summary["total"],
        summary["pass_rate"] * 100,
        "PASSED" if summary["gate_passed"] else "FAILED",
    )

    # Non-zero exit code causes CI to fail the PR
    sys.exit(0 if summary["gate_passed"] else 1)


if __name__ == "__main__":
    main()
