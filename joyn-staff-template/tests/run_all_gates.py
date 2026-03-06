#!/usr/bin/env python
"""
Self-Test Runner
=================
Run all 12 gate self-tests before submission.

Usage:
    python tests/run_all_gates.py

Output:
    - Console summary of pass/fail per gate
    - JSON report at tests/results/self_test_report.json
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def load_staff_spec() -> dict:
    """Load STAFF-SPEC.md and parse into dict structure."""
    spec_path = Path(__file__).parent.parent / "STAFF-SPEC.md"
    if not spec_path.exists():
        return {"error": "STAFF-SPEC.md not found"}
    
    # Basic parsing - in production, use proper markdown parser
    with open(spec_path, 'r') as f:
        content = f.read()
    
    return {
        "raw_content": content,
        "has_name": "**Staff Name:**" in content and len(content.split("**Staff Name:**")[1].split("\n")[0].strip()) > 0,
        "has_description": "**One-Sentence Description:**" in content,
        "has_tasks": content.count("### Task") >= 3,
        "has_outputs": content.count("### Output") >= 2,
    }


def check_gate_1_role_clarity(spec: dict) -> dict:
    """Gate 1: Role Clarity self-check."""
    checks = []
    
    # Check: Has staff name
    if spec.get("has_name"):
        checks.append({"name": "has_name", "passed": True, "message": "Staff name provided"})
    else:
        checks.append({"name": "has_name", "passed": False, "message": "Missing staff name in STAFF-SPEC.md"})
    
    # Check: Has description
    if spec.get("has_description"):
        checks.append({"name": "has_description", "passed": True, "message": "Role description provided"})
    else:
        checks.append({"name": "has_description", "passed": False, "message": "Missing role description"})
    
    passed = all(c["passed"] for c in checks)
    return {
        "gate": 1,
        "name": "Role Clarity",
        "passed": passed,
        "checks": checks
    }


def check_gate_2_outputs(spec: dict) -> dict:
    """Gate 2: Output Standard self-check."""
    checks = []
    
    # Check: Has outputs defined
    if spec.get("has_outputs"):
        checks.append({"name": "has_outputs", "passed": True, "message": "Named outputs defined"})
    else:
        checks.append({"name": "has_outputs", "passed": False, "message": "Need at least 2 named outputs"})
    
    # Check: Specimens exist
    specimens_dir = Path(__file__).parent.parent / "docs" / "specimens"
    if specimens_dir.exists() and list(specimens_dir.glob("*")):
        checks.append({"name": "has_specimens", "passed": True, "message": "Output specimens found"})
    else:
        checks.append({"name": "has_specimens", "passed": False, "message": "No specimens in docs/specimens/"})
    
    passed = all(c["passed"] for c in checks)
    return {
        "gate": 2,
        "name": "Output Standard",
        "passed": passed,
        "checks": checks
    }


def check_gate_3_hirer_experience(spec: dict) -> dict:
    """Gate 3: Hirer Experience self-check."""
    checks = []
    
    # Check for sections in spec
    raw = spec.get("raw_content", "")
    
    if "### Autonomous Decisions" in raw:
        checks.append({"name": "autonomous_decisions", "passed": True, "message": "Autonomous decisions documented"})
    else:
        checks.append({"name": "autonomous_decisions", "passed": False, "message": "Document autonomous decisions"})
    
    if "### Escalation Triggers" in raw:
        checks.append({"name": "escalation_triggers", "passed": True, "message": "Escalation triggers documented"})
    else:
        checks.append({"name": "escalation_triggers", "passed": False, "message": "Document escalation triggers"})
    
    passed = all(c["passed"] for c in checks)
    return {
        "gate": 3,
        "name": "Hirer Experience",
        "passed": passed,
        "checks": checks
    }


def check_gate_4_failure_handling(spec: dict) -> dict:
    """Gate 4: Failure Handling self-check."""
    checks = []
    
    raw = spec.get("raw_content", "")
    
    sections = [
        ("declined_data", "### When Data is Declined"),
        ("ambiguous_input", "### When Input is Ambiguous"),
        ("out_of_scope", "### When Request is Out of Scope"),
        ("hallucination", "### No Hallucination Policy"),
    ]
    
    for name, header in sections:
        if header in raw:
            checks.append({"name": name, "passed": True, "message": f"{name} documented"})
        else:
            checks.append({"name": name, "passed": False, "message": f"Document {name} handling"})
    
    passed = all(c["passed"] for c in checks)
    return {
        "gate": 4,
        "name": "Failure Handling",
        "passed": passed,
        "checks": checks
    }


def check_gate_5_calibration(spec: dict) -> dict:
    """Gate 5: Calibration Architecture self-check."""
    checks = []
    
    raw = spec.get("raw_content", "")
    
    if "### Feedback Questions" in raw:
        checks.append({"name": "feedback_questions", "passed": True, "message": "Feedback questions defined"})
    else:
        checks.append({"name": "feedback_questions", "passed": False, "message": "Define feedback questions"})
    
    # Check for calibration module
    calibration_path = Path(__file__).parent.parent / "backend" / "calibration"
    if calibration_path.exists():
        checks.append({"name": "calibration_module", "passed": True, "message": "Calibration module exists"})
    else:
        checks.append({"name": "calibration_module", "passed": False, "message": "Create backend/calibration/"})
    
    passed = all(c["passed"] for c in checks)
    return {
        "gate": 5,
        "name": "Calibration Architecture",
        "passed": passed,
        "checks": checks
    }


def check_gate_6_security() -> dict:
    """Gate 6: Security by Design self-check."""
    checks = []
    
    # Check security module exists
    security_path = Path(__file__).parent.parent / "backend" / "utils" / "security.py"
    if security_path.exists():
        checks.append({"name": "security_module", "passed": True, "message": "Security module exists"})
    else:
        checks.append({"name": "security_module", "passed": False, "message": "Create backend/utils/security.py"})
    
    # Check for .env.example (no hardcoded secrets)
    env_example = Path(__file__).parent.parent / "backend" / ".env.example"
    if env_example.exists():
        checks.append({"name": "env_example", "passed": True, "message": "Environment template exists"})
    else:
        checks.append({"name": "env_example", "passed": False, "message": "Create backend/.env.example"})
    
    passed = all(c["passed"] for c in checks)
    return {
        "gate": 6,
        "name": "Security by Design",
        "passed": passed,
        "checks": checks
    }


def check_gate_7_harm() -> dict:
    """Gate 7: AI Harm Prevention self-check."""
    checks = []
    
    # Check for content safety in security module
    security_path = Path(__file__).parent.parent / "backend" / "utils" / "security.py"
    if security_path.exists():
        with open(security_path, 'r') as f:
            content = f.read()
        
        if "content_safety" in content.lower() or "check_content" in content:
            checks.append({"name": "content_safety", "passed": True, "message": "Content safety check found"})
        else:
            checks.append({"name": "content_safety", "passed": False, "message": "Add content safety checks"})
    else:
        checks.append({"name": "content_safety", "passed": False, "message": "Security module missing"})
    
    passed = all(c["passed"] for c in checks)
    return {
        "gate": 7,
        "name": "AI Harm Prevention",
        "passed": passed,
        "checks": checks
    }


def check_gate_8_resilience() -> dict:
    """Gate 8: Operational Resilience self-check."""
    checks = []
    
    # Check for error handling in agents
    agents_path = Path(__file__).parent.parent / "backend" / "agents"
    if agents_path.exists():
        has_error_handling = False
        for py_file in agents_path.glob("*.py"):
            with open(py_file, 'r') as f:
                content = f.read()
            if "try:" in content and "except" in content:
                has_error_handling = True
                break
        
        if has_error_handling:
            checks.append({"name": "error_handling", "passed": True, "message": "Error handling found in agents"})
        else:
            checks.append({"name": "error_handling", "passed": False, "message": "Add try/except to agents"})
    else:
        checks.append({"name": "error_handling", "passed": False, "message": "Agents module missing"})
    
    passed = all(c["passed"] for c in checks)
    return {
        "gate": 8,
        "name": "Operational Resilience",
        "passed": passed,
        "checks": checks
    }


def check_gate_9_listing() -> dict:
    """Gate 9: Listing Accuracy self-check."""
    checks = []
    
    # Check listing.html exists
    listing_path = Path(__file__).parent.parent / "frontend" / "listing.html"
    if listing_path.exists():
        checks.append({"name": "listing_exists", "passed": True, "message": "listing.html found"})
    else:
        checks.append({"name": "listing_exists", "passed": False, "message": "Create frontend/listing.html"})
    
    # Check for screenshots
    frontend_path = Path(__file__).parent.parent / "frontend"
    screenshots = list(frontend_path.glob("*.png")) + list(frontend_path.glob("*.jpg"))
    if len(screenshots) >= 3:
        checks.append({"name": "screenshots", "passed": True, "message": f"Found {len(screenshots)} screenshots"})
    else:
        checks.append({"name": "screenshots", "passed": False, "message": "Need at least 3 screenshots"})
    
    passed = all(c["passed"] for c in checks)
    return {
        "gate": 9,
        "name": "Listing Accuracy",
        "passed": passed,
        "checks": checks
    }


def check_gate_10_pricing(spec: dict) -> dict:
    """Gate 10: Transparent Pricing self-check."""
    checks = []
    
    raw = spec.get("raw_content", "")
    
    if "## Pricing" in raw:
        checks.append({"name": "pricing_defined", "passed": True, "message": "Pricing section found"})
    else:
        checks.append({"name": "pricing_defined", "passed": False, "message": "Add pricing to STAFF-SPEC.md"})
    
    if "$" in raw:
        checks.append({"name": "price_amount", "passed": True, "message": "Price amount specified"})
    else:
        checks.append({"name": "price_amount", "passed": False, "message": "Specify price amounts"})
    
    passed = all(c["passed"] for c in checks)
    return {
        "gate": 10,
        "name": "Transparent Pricing",
        "passed": passed,
        "checks": checks
    }


def check_gate_11_data(spec: dict) -> dict:
    """Gate 11: Data Protection self-check."""
    checks = []
    
    # Check for COMPLIANCE.md
    compliance_path = Path(__file__).parent.parent / "docs" / "COMPLIANCE.md"
    if compliance_path.exists():
        checks.append({"name": "compliance_doc", "passed": True, "message": "COMPLIANCE.md found"})
    else:
        checks.append({"name": "compliance_doc", "passed": False, "message": "Create docs/COMPLIANCE.md"})
    
    passed = all(c["passed"] for c in checks)
    return {
        "gate": 11,
        "name": "Data Protection & Privacy",
        "passed": passed,
        "checks": checks
    }


def check_gate_12_governance(spec: dict) -> dict:
    """Gate 12: AI Governance self-check."""
    checks = []
    
    raw = spec.get("raw_content", "")
    
    if "## Risk Classification" in raw:
        checks.append({"name": "risk_classification", "passed": True, "message": "Risk classification found"})
    else:
        checks.append({"name": "risk_classification", "passed": False, "message": "Add risk classification"})
    
    passed = all(c["passed"] for c in checks)
    return {
        "gate": 12,
        "name": "AI Governance & Ethics",
        "passed": passed,
        "checks": checks
    }


def run_all_gates() -> dict:
    """Run all 12 gate self-tests."""
    print("=" * 60)
    print("JOYN STAFF TEMPLATE — SELF-TEST")
    print("=" * 60)
    print()
    
    # Load spec
    spec = load_staff_spec()
    if spec.get("error"):
        print(f"ERROR: {spec['error']}")
        return {"error": spec["error"]}
    
    # Run all gates
    results = []
    
    # Quality Gates
    results.append(check_gate_1_role_clarity(spec))
    results.append(check_gate_2_outputs(spec))
    results.append(check_gate_3_hirer_experience(spec))
    results.append(check_gate_4_failure_handling(spec))
    results.append(check_gate_5_calibration(spec))
    
    # Safety Gates
    results.append(check_gate_6_security())
    results.append(check_gate_7_harm())
    results.append(check_gate_8_resilience())
    
    # Trust Gates
    results.append(check_gate_9_listing())
    results.append(check_gate_10_pricing(spec))
    
    # Compliance Gates
    results.append(check_gate_11_data(spec))
    results.append(check_gate_12_governance(spec))
    
    # Print results
    passed_count = 0
    for result in results:
        status = "✓" if result["passed"] else "✗"
        print(f"Gate {result['gate']:2d}: {result['name']:<30} {status}")
        if result["passed"]:
            passed_count += 1
        else:
            for check in result["checks"]:
                if not check["passed"]:
                    print(f"         → {check['message']}")
    
    print()
    print("-" * 60)
    print(f"RESULT: {passed_count}/12 gates passed")
    
    if passed_count == 12:
        print("STATUS: Ready for submission!")
    else:
        print(f"STATUS: Fix {12 - passed_count} gate(s) before submission")
    
    print("=" * 60)
    
    # Save report
    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "passed": passed_count,
        "total": 12,
        "ready_for_submission": passed_count == 12,
        "gates": results
    }
    
    results_dir = Path(__file__).parent / "results"
    results_dir.mkdir(exist_ok=True)
    
    with open(results_dir / "self_test_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\nReport saved to: tests/results/self_test_report.json")
    
    return report


if __name__ == "__main__":
    run_all_gates()
