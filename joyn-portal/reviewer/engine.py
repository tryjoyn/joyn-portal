"""
Reviewer Agent — Main Engine
=============================
Orchestrates the 12-gate validation pipeline for AI staff submissions.
"""

import time
import json
from typing import Dict, Any, List
from dataclasses import asdict

from .gates import (
    GateResult,
    GateVerdict,
    ReviewVerdict,
    validate_gate_1_role_clarity,
    validate_gate_2_output_standard,
    validate_gate_3_hirer_experience,
    validate_gate_4_failure_handling,
    validate_gate_5_calibration,
    validate_gate_6_security,
    validate_gate_7_ai_harm,
    validate_gate_8_resilience,
    validate_gate_9_listing_accuracy,
    validate_gate_10_pricing,
    validate_gate_11_data_protection,
    validate_gate_12_ai_governance,
)


# Gate functions in order
GATE_VALIDATORS = [
    validate_gate_1_role_clarity,
    validate_gate_2_output_standard,
    validate_gate_3_hirer_experience,
    validate_gate_4_failure_handling,
    validate_gate_5_calibration,
    validate_gate_6_security,
    validate_gate_7_ai_harm,
    validate_gate_8_resilience,
    validate_gate_9_listing_accuracy,
    validate_gate_10_pricing,
    validate_gate_11_data_protection,
    validate_gate_12_ai_governance,
]


# Gate categories
GATE_CATEGORIES = {
    "quality": [1, 2, 3, 4, 5],
    "safety": [6, 7, 8],
    "trust": [9, 10],
    "compliance": [11, 12],
}


def validate_submission_completeness(submission: Dict[str, Any]) -> Dict[str, Any]:
    """
    Stage 1: Check if all required submission items are present.
    Returns dict with 'complete' bool and 'missing' list.
    """
    required_items = [
        ("identity_brief", "Identity Brief"),
        ("agent_roster", "Agent Roster"),
        ("outputs", "Output Specifications"),
        ("output_specimens", "Output Specimens"),
        ("listing_assets", "Listing Assets"),
        ("pricing", "Pricing"),
    ]
    
    # Optional but recommended
    optional_items = [
        ("failure_test_results", "Failure Test Results"),
        ("security_test_results", "Security Test Results"),
    ]
    
    missing = []
    warnings = []
    
    for key, name in required_items:
        if key not in submission or not submission[key]:
            missing.append(name)
    
    for key, name in optional_items:
        if key not in submission or not submission[key]:
            warnings.append(f"{name} not provided — some checks will be skipped")
    
    return {
        "complete": len(missing) == 0,
        "missing": missing,
        "warnings": warnings,
    }


def run_full_review(submission: Dict[str, Any]) -> ReviewVerdict:
    """
    Run all 12 gates against a submission.
    Returns a ReviewVerdict with overall result and per-gate verdicts.
    """
    start_time = time.time()
    
    # Stage 1: Completeness check
    completeness = validate_submission_completeness(submission)
    if not completeness["complete"]:
        return ReviewVerdict(
            result="INCOMPLETE",
            gates=[],
            summary=f"Submission incomplete. Missing: {', '.join(completeness['missing'])}",
            resubmit_gates=[],
            time_taken_seconds=time.time() - start_time,
        )
    
    # Stage 2-5: Run all gates
    gate_verdicts: List[GateVerdict] = []
    for validator in GATE_VALIDATORS:
        verdict = validator(submission)
        gate_verdicts.append(verdict)
    
    # Calculate overall result
    total_time = time.time() - start_time
    
    failed_gates = [g for g in gate_verdicts if g.result == GateResult.FAIL]
    conditional_gates = [g for g in gate_verdicts if g.result == GateResult.CONDITIONAL]
    passed_gates = [g for g in gate_verdicts if g.result == GateResult.PASS]
    
    # Check for critical failures (safety gates 6-8 with FAIL are always critical)
    safety_failures = [g for g in failed_gates if g.category == "safety"]
    
    if safety_failures:
        # Any safety gate failure = RESUBMIT
        result = "RESUBMIT"
        summary = f"Safety gate failure(s): {', '.join([f'Gate {g.gate_number}' for g in safety_failures])}. All safety issues must be resolved."
        resubmit_gates = [g.gate_number for g in failed_gates]
    elif len(failed_gates) >= 3:
        # 3+ failures = RESUBMIT
        result = "RESUBMIT"
        summary = f"{len(failed_gates)} gates failed. Full resubmission required."
        resubmit_gates = [g.gate_number for g in failed_gates]
    elif len(failed_gates) > 0:
        # 1-2 failures = CONDITIONAL (can fix specific gates)
        result = "CONDITIONAL_PASS"
        summary = f"{len(failed_gates)} gate(s) need remediation. Fix and resubmit those gates only."
        resubmit_gates = [g.gate_number for g in failed_gates]
    elif len(conditional_gates) > 0:
        # All pass or conditional = CONDITIONAL PASS
        result = "CONDITIONAL_PASS"
        summary = f"{len(conditional_gates)} gate(s) have minor issues. Address for full approval."
        resubmit_gates = [g.gate_number for g in conditional_gates]
    else:
        # All pass = PASS
        result = "PASS"
        summary = f"All 12 gates passed. Staff approved for deployment."
        resubmit_gates = []
    
    return ReviewVerdict(
        result=result,
        gates=gate_verdicts,
        summary=summary,
        resubmit_gates=resubmit_gates,
        time_taken_seconds=total_time,
    )


def run_gate_review(submission: Dict[str, Any], gate_numbers: List[int]) -> ReviewVerdict:
    """
    Run specific gates only (for resubmission of failed gates).
    """
    start_time = time.time()
    
    gate_verdicts: List[GateVerdict] = []
    for gate_num in gate_numbers:
        if 1 <= gate_num <= 12:
            validator = GATE_VALIDATORS[gate_num - 1]
            verdict = validator(submission)
            gate_verdicts.append(verdict)
    
    total_time = time.time() - start_time
    
    failed_gates = [g for g in gate_verdicts if g.result == GateResult.FAIL]
    
    if failed_gates:
        result = "RESUBMIT"
        summary = f"Gate(s) still failing: {', '.join([f'Gate {g.gate_number}' for g in failed_gates])}"
        resubmit_gates = [g.gate_number for g in failed_gates]
    else:
        result = "PASS"
        summary = f"Resubmitted gates passed. Staff approved for deployment."
        resubmit_gates = []
    
    return ReviewVerdict(
        result=result,
        gates=gate_verdicts,
        summary=summary,
        resubmit_gates=resubmit_gates,
        time_taken_seconds=total_time,
    )


def verdict_to_dict(verdict: ReviewVerdict) -> Dict[str, Any]:
    """Convert ReviewVerdict to JSON-serializable dict."""
    return {
        "result": verdict.result,
        "summary": verdict.summary,
        "resubmit_gates": verdict.resubmit_gates,
        "time_taken_seconds": round(verdict.time_taken_seconds, 2),
        "gates": [
            {
                "gate_number": g.gate_number,
                "gate_name": g.gate_name,
                "category": g.category,
                "result": g.result.value,
                "feedback": g.feedback,
                "remediation": g.remediation,
                "checks": [
                    {
                        "name": c.name,
                        "passed": c.passed,
                        "message": c.message,
                        "evidence": c.evidence,
                        "severity": c.severity,
                    }
                    for c in g.checks
                ]
            }
            for g in verdict.gates
        ]
    }


def generate_feedback_report(verdict: ReviewVerdict) -> str:
    """
    Generate human-readable feedback report for builders.
    """
    lines = []
    lines.append("=" * 70)
    lines.append("JOYN REVIEWER AGENT — SUBMISSION VERDICT")
    lines.append("=" * 70)
    lines.append("")
    lines.append(f"RESULT: {verdict.result}")
    lines.append(f"TIME: {verdict.time_taken_seconds:.2f} seconds")
    lines.append("")
    lines.append(verdict.summary)
    lines.append("")
    
    if verdict.resubmit_gates:
        lines.append(f"GATES TO ADDRESS: {', '.join([str(g) for g in verdict.resubmit_gates])}")
        lines.append("")
    
    lines.append("-" * 70)
    lines.append("GATE-BY-GATE BREAKDOWN")
    lines.append("-" * 70)
    
    for gate in verdict.gates:
        status_icon = "✓" if gate.result == GateResult.PASS else "○" if gate.result == GateResult.CONDITIONAL else "✗"
        lines.append("")
        lines.append(f"Gate {gate.gate_number}: {gate.gate_name} [{gate.category.upper()}]")
        lines.append(f"  Status: {status_icon} {gate.result.value.upper()}")
        lines.append(f"  {gate.feedback}")
        
        if gate.remediation:
            lines.append(f"  → Remediation: {gate.remediation}")
        
        # Show individual checks for failed/conditional gates
        if gate.result != GateResult.PASS:
            failed_checks = [c for c in gate.checks if not c.passed]
            for check in failed_checks:
                lines.append(f"    - {check.message}")
                if check.evidence:
                    lines.append(f"      Evidence: {check.evidence[:100]}...")
    
    lines.append("")
    lines.append("-" * 70)
    
    if verdict.result == "PASS":
        lines.append("NEXT STEPS: Your staff will be deployed to the marketplace within 1 hour.")
    elif verdict.result == "CONDITIONAL_PASS":
        lines.append("NEXT STEPS: Address the issues above and resubmit the affected gates.")
        lines.append("            You do not need to resubmit the entire package.")
    else:
        lines.append("NEXT STEPS: Review all feedback above and resubmit your full package.")
        lines.append("            Unlimited resubmissions are included with your listing fee.")
    
    lines.append("")
    lines.append("Questions? Contact hire@tryjoyn.me")
    lines.append("=" * 70)
    
    return "\n".join(lines)


# =============================================================================
# Example usage
# =============================================================================

def create_example_submission() -> Dict[str, Any]:
    """Create an example submission for testing."""
    return {
        "identity_brief": {
            "name": "Iris",
            "role_description": "Monitors insurance regulatory bulletins across US states and alerts hirers to changes affecting their business.",
            "mode": "autonomous",
            "vertical": "Insurance & Risk",
            "does_not": "Does not provide legal advice, file documents on hirer's behalf, or interpret regulations."
        },
        "agent_roster": [
            {
                "name": "Monitor",
                "inputs": ["State DOI RSS feeds", "Bulletin databases"],
                "outputs": ["Regulatory alerts", "Change summaries"],
                "handoff": "Alerts sent to Output agent",
                "failure_behavior": "Logs monitoring gap, continues with available sources"
            }
        ],
        "outputs": [
            {
                "name": "Regulatory Alert",
                "format": "Email",
                "frequency": "Real-time when relevant bulletin detected",
                "description": "Immediate notification of regulatory changes"
            },
            {
                "name": "Weekly Digest",
                "format": "PDF",
                "frequency": "Every Monday 9am",
                "description": "Summary of all activity for monitored states"
            }
        ],
        "output_specimens": [
            {"name": "Regulatory Alert", "is_template": False},
            {"name": "Weekly Digest", "is_template": False}
        ],
        "hirer_experience": {
            "autonomous_decisions": [
                "Which bulletins are relevant to hirer's business",
                "Alert priority level (critical/high/medium/low)"
            ],
            "escalation_triggers": [
                "Bulletin requires action within 30 days",
                "Multiple states affected simultaneously",
                "Unable to determine relevance"
            ],
            "time_commitment": "~15 min/week reviewing alerts"
        },
        "failure_handling": {
            "declined_data": "If hirer declines to share lines of business, Iris monitors all lines and notes reduced precision in alerts.",
            "ambiguous_input": "Asks one clarifying question about jurisdiction or line of business.",
            "out_of_scope": "Escalates with specific description: 'This bulletin affects [X] which is outside monitored scope.'",
            "hallucination_policy": "Never presents information not from official sources."
        },
        "calibration": {
            "feedback_questions": [
                "Was this alert relevant to your business?",
                "What action did you take based on this alert?",
                "What would have made this alert more useful?"
            ],
            "corpus_structure": "JSON per hirer, keyed by alert ID",
            "forward_reference": True,
            "forward_reference_description": "Future alerts reference calibration corpus to improve relevance scoring",
            "hirer_ownership": True
        },
        "security": {
            "input_validation": True,
            "pii_filtering": True,
            "least_privilege": True,
            "secret_management": True
        },
        "security_test_results": {
            "prompt_injection": {"passed": 10, "total": 10},
            "pii_leakage": {"passed": True},
            "secret_scan": {"secrets_found": 0}
        },
        "harm_prevention": {
            "content_safety": True,
            "bias_detection": True,
            "confidence_disclosure": True,
            "high_stakes_escalation": True
        },
        "resilience": {
            "graceful_degradation": True,
            "error_logging": True,
            "recovery_procedure": "Re-sync from last checkpoint, notify hirer of gap period",
            "kill_switch": True,
            "incident_notification": True
        },
        "resilience_test_results": {
            "degradation": {"data_preserved": True},
            "kill_switch": {"response_time_seconds": 5}
        },
        "listing_assets": {
            "roi_chips": [
                "~4h analyst time saved/week",
                "0 missed regulatory bulletins"
            ],
            "roi_evidence": {
                "~4h analyst time saved/week": "Based on average manual monitoring time per state",
                "0 missed regulatory bulletins": "100% bulletin capture rate in testing"
            },
            "description": "Iris monitors insurance regulatory bulletins continuously across US states. She alerts you when a filing, bulletin, or rule change affects your lines of business.",
            "screenshots": ["dashboard.png", "alert.png", "digest.png"]
        },
        "pricing": {
            "monthly": 1500,
            "annual": 15300,
            "trial_days": 14,
            "additional_fees": [],
            "cancellation_terms": "Cancel anytime, access continues until end of billing period"
        },
        "data_protection": {
            "data_collected": ["email", "company_name", "states", "lines_of_business"],
            "data_justified": {
                "email": "Required for alert delivery",
                "company_name": "Required for personalization",
                "states": "Required for monitoring scope",
                "lines_of_business": "Required for relevance filtering"
            },
            "lawful_basis": "contract",
            "rights_implemented": ["access", "rectification", "erasure", "portability"],
            "retention_days": 365
        },
        "ai_governance": {
            "risk_level": "limited",
            "human_oversight": True,
            "ai_disclosure": True,
            "technical_documentation": True,
            "training_data_documented": True,
            "incident_reporting_process": True
        }
    }


if __name__ == "__main__":
    # Test the reviewer
    submission = create_example_submission()
    verdict = run_full_review(submission)
    print(generate_feedback_report(verdict))
