"""
Reviewer Agent — 12 Gate Validation System
============================================
Automated validation of AI staff submissions against The Joyn Standard v2.

Gates 1-5: Quality (Does it work?)
Gates 6-8: Safety (Is it safe?)
Gates 9-10: Trust (Can hirers trust it?)
Gates 11-12: Compliance (Is it legal?)
"""

import re
import json
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum


class GateResult(Enum):
    PASS = "pass"
    CONDITIONAL = "conditional"
    FAIL = "fail"


@dataclass
class GateCheck:
    """Individual check within a gate"""
    name: str
    passed: bool
    message: str
    evidence: Optional[str] = None
    severity: str = "standard"  # standard, critical


@dataclass
class GateVerdict:
    """Result of a single gate evaluation"""
    gate_number: int
    gate_name: str
    category: str  # quality, safety, trust, compliance
    result: GateResult
    checks: List[GateCheck] = field(default_factory=list)
    feedback: str = ""
    remediation: Optional[str] = None


@dataclass
class ReviewVerdict:
    """Overall review verdict"""
    result: str  # PASS, CONDITIONAL_PASS, RESUBMIT
    gates: List[GateVerdict] = field(default_factory=list)
    summary: str = ""
    resubmit_gates: List[int] = field(default_factory=list)
    time_taken_seconds: float = 0


# =============================================================================
# GATE 1: Role Clarity
# =============================================================================

def validate_gate_1_role_clarity(submission: Dict[str, Any]) -> GateVerdict:
    """
    Gate 1: Role Clarity
    - One-sentence role description
    - Clear scope boundaries
    - No category confusion
    """
    checks = []
    identity = submission.get("identity_brief", {})
    
    # Check 1: One-sentence role description
    role_desc = identity.get("role_description", "")
    sentences = [s.strip() for s in re.split(r'[.!?]', role_desc) if s.strip()]
    
    if len(sentences) == 1:
        # Check for "and" splitting scope
        if " and " in role_desc.lower() and role_desc.count(" and ") > 0:
            # Allow one "and" for natural language, fail on multiple
            and_count = role_desc.lower().count(" and ")
            if and_count > 1:
                checks.append(GateCheck(
                    name="single_sentence",
                    passed=False,
                    message=f"Role description uses 'and' {and_count} times, suggesting multiple scopes",
                    evidence=role_desc
                ))
            else:
                checks.append(GateCheck(
                    name="single_sentence",
                    passed=True,
                    message="Role description is a single sentence",
                    evidence=role_desc
                ))
        else:
            checks.append(GateCheck(
                name="single_sentence",
                passed=True,
                message="Role description is a single sentence",
                evidence=role_desc
            ))
    elif len(sentences) == 0:
        checks.append(GateCheck(
            name="single_sentence",
            passed=False,
            message="Role description is missing",
            severity="critical"
        ))
    else:
        checks.append(GateCheck(
            name="single_sentence",
            passed=False,
            message=f"Role description has {len(sentences)} sentences, should be exactly 1",
            evidence=role_desc
        ))
    
    # Check 2: Word count
    word_count = len(role_desc.split())
    if word_count <= 25:
        checks.append(GateCheck(
            name="word_count",
            passed=True,
            message=f"Role description is {word_count} words (max 25)"
        ))
    else:
        checks.append(GateCheck(
            name="word_count",
            passed=False,
            message=f"Role description is {word_count} words, exceeds 25 word limit"
        ))
    
    # Check 3: No vague terms
    vague_terms = ["assists with", "helps manage", "supports", "handles various", "works on"]
    found_vague = [term for term in vague_terms if term in role_desc.lower()]
    if found_vague:
        checks.append(GateCheck(
            name="no_vague_terms",
            passed=False,
            message=f"Role description uses vague terms: {', '.join(found_vague)}",
            evidence=role_desc
        ))
    else:
        checks.append(GateCheck(
            name="no_vague_terms",
            passed=True,
            message="Role description uses specific, clear language"
        ))
    
    # Check 4: Scope boundaries defined
    does_not = identity.get("does_not", "")
    if does_not and len(does_not.strip()) > 10:
        checks.append(GateCheck(
            name="scope_boundaries",
            passed=True,
            message="Scope boundaries defined (what staff does NOT do)",
            evidence=does_not[:100]
        ))
    else:
        checks.append(GateCheck(
            name="scope_boundaries",
            passed=False,
            message="Missing 'does not do' scope boundaries"
        ))
    
    # Determine result
    critical_failures = [c for c in checks if not c.passed and c.severity == "critical"]
    standard_failures = [c for c in checks if not c.passed and c.severity == "standard"]
    
    if critical_failures:
        result = GateResult.FAIL
        feedback = "Critical issues found in role clarity"
        remediation = "Provide a single-sentence role description that clearly states what this staff does"
    elif len(standard_failures) >= 2:
        result = GateResult.FAIL
        feedback = f"{len(standard_failures)} issues found in role clarity"
        remediation = "; ".join([c.message for c in standard_failures])
    elif standard_failures:
        result = GateResult.CONDITIONAL
        feedback = "Minor issues in role clarity"
        remediation = standard_failures[0].message
    else:
        result = GateResult.PASS
        feedback = "Role clarity meets standards"
        remediation = None
    
    return GateVerdict(
        gate_number=1,
        gate_name="Role Clarity",
        category="quality",
        result=result,
        checks=checks,
        feedback=feedback,
        remediation=remediation
    )


# =============================================================================
# GATE 2: Output Standard
# =============================================================================

def validate_gate_2_output_standard(submission: Dict[str, Any]) -> GateVerdict:
    """
    Gate 2: Output Standard
    - Named outputs with specific names
    - Format specification for each
    - Frequency/trigger defined
    - Sample specimens provided
    """
    checks = []
    outputs = submission.get("outputs", [])
    specimens = submission.get("output_specimens", [])
    
    # Check 1: Has named outputs
    if outputs and len(outputs) >= 1:
        checks.append(GateCheck(
            name="has_outputs",
            passed=True,
            message=f"Defines {len(outputs)} named output(s)"
        ))
    else:
        checks.append(GateCheck(
            name="has_outputs",
            passed=False,
            message="No named outputs defined",
            severity="critical"
        ))
    
    # Check 2: Each output has required fields
    for i, output in enumerate(outputs):
        name = output.get("name", "")
        format_spec = output.get("format", "")
        frequency = output.get("frequency", "")
        
        if not name:
            checks.append(GateCheck(
                name=f"output_{i}_name",
                passed=False,
                message=f"Output {i+1} missing name"
            ))
        
        if not format_spec:
            checks.append(GateCheck(
                name=f"output_{i}_format",
                passed=False,
                message=f"Output '{name}' missing format specification"
            ))
        
        if not frequency:
            checks.append(GateCheck(
                name=f"output_{i}_frequency",
                passed=False,
                message=f"Output '{name}' missing frequency/trigger"
            ))
    
    # Check 3: Specimens provided
    if specimens and len(specimens) >= len(outputs):
        checks.append(GateCheck(
            name="specimens_provided",
            passed=True,
            message=f"All {len(outputs)} output(s) have specimens"
        ))
    elif specimens:
        checks.append(GateCheck(
            name="specimens_provided",
            passed=False,
            message=f"Only {len(specimens)} specimens for {len(outputs)} outputs"
        ))
    else:
        checks.append(GateCheck(
            name="specimens_provided",
            passed=False,
            message="No output specimens provided",
            severity="critical"
        ))
    
    # Check 4: Specimens are real (not templates)
    for i, specimen in enumerate(specimens):
        if specimen.get("is_template", False):
            checks.append(GateCheck(
                name=f"specimen_{i}_real",
                passed=False,
                message=f"Specimen {i+1} appears to be a template, not a completed artifact"
            ))
    
    # Determine result
    critical_failures = [c for c in checks if not c.passed and c.severity == "critical"]
    standard_failures = [c for c in checks if not c.passed and c.severity == "standard"]
    
    if critical_failures:
        result = GateResult.FAIL
        feedback = "Critical: Missing named outputs or specimens"
        remediation = "Define all outputs with name, format, frequency. Provide real specimens for each."
    elif len(standard_failures) >= 3:
        result = GateResult.FAIL
        feedback = f"{len(standard_failures)} output specification issues"
        remediation = "; ".join([c.message for c in standard_failures[:3]])
    elif standard_failures:
        result = GateResult.CONDITIONAL
        feedback = "Minor output specification issues"
        remediation = "; ".join([c.message for c in standard_failures])
    else:
        result = GateResult.PASS
        feedback = "Output standards meet requirements"
        remediation = None
    
    return GateVerdict(
        gate_number=2,
        gate_name="Output Standard",
        category="quality",
        result=result,
        checks=checks,
        feedback=feedback,
        remediation=remediation
    )


# =============================================================================
# GATE 3: Hirer Experience
# =============================================================================

def validate_gate_3_hirer_experience(submission: Dict[str, Any]) -> GateVerdict:
    """
    Gate 3: Hirer Experience
    - Autonomous decisions documented
    - Escalation triggers defined
    - Intervention points (Supervised mode)
    - Time commitment disclosed
    """
    checks = []
    identity = submission.get("identity_brief", {})
    mode = identity.get("mode", "autonomous").lower()
    hirer_exp = submission.get("hirer_experience", {})
    
    # Check 1: Autonomous decisions documented
    autonomous_decisions = hirer_exp.get("autonomous_decisions", [])
    if autonomous_decisions and len(autonomous_decisions) >= 1:
        checks.append(GateCheck(
            name="autonomous_decisions",
            passed=True,
            message=f"Documents {len(autonomous_decisions)} autonomous decision type(s)"
        ))
    else:
        checks.append(GateCheck(
            name="autonomous_decisions",
            passed=False,
            message="No autonomous decisions documented"
        ))
    
    # Check 2: Escalation triggers
    escalation_triggers = hirer_exp.get("escalation_triggers", [])
    if escalation_triggers and len(escalation_triggers) >= 1:
        checks.append(GateCheck(
            name="escalation_triggers",
            passed=True,
            message=f"Defines {len(escalation_triggers)} escalation trigger(s)"
        ))
    else:
        checks.append(GateCheck(
            name="escalation_triggers",
            passed=False,
            message="No escalation triggers defined",
            severity="critical"
        ))
    
    # Check 3: Intervention points (Supervised mode only)
    if mode == "supervised":
        intervention_points = hirer_exp.get("intervention_points", [])
        if intervention_points and len(intervention_points) >= 1:
            checks.append(GateCheck(
                name="intervention_points",
                passed=True,
                message=f"Defines {len(intervention_points)} intervention point(s)"
            ))
        else:
            checks.append(GateCheck(
                name="intervention_points",
                passed=False,
                message="Supervised mode requires at least one intervention point",
                severity="critical"
            ))
    
    # Check 4: Time commitment disclosed
    time_commitment = hirer_exp.get("time_commitment", "")
    if time_commitment:
        checks.append(GateCheck(
            name="time_commitment",
            passed=True,
            message=f"Time commitment disclosed: {time_commitment}"
        ))
    else:
        checks.append(GateCheck(
            name="time_commitment",
            passed=False,
            message="Hirer time commitment not disclosed"
        ))
    
    # Check 5: Not every output requires approval (broken workflow check)
    outputs = submission.get("outputs", [])
    requires_approval = [o for o in outputs if o.get("requires_approval", False)]
    if len(requires_approval) == len(outputs) and len(outputs) > 1:
        checks.append(GateCheck(
            name="not_broken_workflow",
            passed=False,
            message="Every output requires hirer approval — this is a broken workflow"
        ))
    else:
        checks.append(GateCheck(
            name="not_broken_workflow",
            passed=True,
            message="Workflow allows autonomous operation between checkpoints"
        ))
    
    # Determine result
    critical_failures = [c for c in checks if not c.passed and c.severity == "critical"]
    standard_failures = [c for c in checks if not c.passed and c.severity == "standard"]
    
    if critical_failures:
        result = GateResult.FAIL
        feedback = f"Critical hirer experience issue: {critical_failures[0].message}"
        remediation = "Define escalation triggers and intervention points appropriate for mode"
    elif len(standard_failures) >= 2:
        result = GateResult.FAIL
        feedback = f"{len(standard_failures)} hirer experience issues"
        remediation = "; ".join([c.message for c in standard_failures])
    elif standard_failures:
        result = GateResult.CONDITIONAL
        feedback = "Minor hirer experience issue"
        remediation = standard_failures[0].message
    else:
        result = GateResult.PASS
        feedback = "Hirer experience well-defined"
        remediation = None
    
    return GateVerdict(
        gate_number=3,
        gate_name="Hirer Experience",
        category="quality",
        result=result,
        checks=checks,
        feedback=feedback,
        remediation=remediation
    )


# =============================================================================
# GATE 4: Failure Handling
# =============================================================================

def validate_gate_4_failure_handling(submission: Dict[str, Any]) -> GateVerdict:
    """
    Gate 4: Failure Handling
    - Declined data handling
    - Ambiguous input handling
    - Out-of-scope handling
    - No hallucination policy
    """
    checks = []
    failure_handling = submission.get("failure_handling", {})
    test_results = submission.get("failure_test_results", {})
    
    # Check 1: Declined data handling documented
    declined_data = failure_handling.get("declined_data", "")
    if declined_data and len(declined_data) > 20:
        checks.append(GateCheck(
            name="declined_data_handling",
            passed=True,
            message="Declined data handling documented"
        ))
    else:
        checks.append(GateCheck(
            name="declined_data_handling",
            passed=False,
            message="Missing declined data handling documentation"
        ))
    
    # Check 2: Ambiguous input handling
    ambiguous_input = failure_handling.get("ambiguous_input", "")
    if ambiguous_input:
        # Check if it mentions asking ONE question
        if "one" in ambiguous_input.lower() or "single" in ambiguous_input.lower():
            checks.append(GateCheck(
                name="ambiguous_input_handling",
                passed=True,
                message="Ambiguous input handling: asks single clarifying question"
            ))
        else:
            checks.append(GateCheck(
                name="ambiguous_input_handling",
                passed=True,
                message="Ambiguous input handling documented"
            ))
    else:
        checks.append(GateCheck(
            name="ambiguous_input_handling",
            passed=False,
            message="Missing ambiguous input handling"
        ))
    
    # Check 3: Out-of-scope handling
    out_of_scope = failure_handling.get("out_of_scope", "")
    if out_of_scope and len(out_of_scope) > 20:
        checks.append(GateCheck(
            name="out_of_scope_handling",
            passed=True,
            message="Out-of-scope handling documented"
        ))
    else:
        checks.append(GateCheck(
            name="out_of_scope_handling",
            passed=False,
            message="Missing out-of-scope handling"
        ))
    
    # Check 4: No hallucination policy
    hallucination_policy = failure_handling.get("hallucination_policy", "")
    if hallucination_policy or "never" in str(failure_handling).lower():
        checks.append(GateCheck(
            name="no_hallucination",
            passed=True,
            message="No-hallucination policy stated"
        ))
    else:
        checks.append(GateCheck(
            name="no_hallucination",
            passed=False,
            message="No-hallucination policy not explicitly stated"
        ))
    
    # Check 5: Failure test results (if provided)
    if test_results:
        declined_test = test_results.get("declined_data_test", {})
        if declined_test.get("passed", False):
            checks.append(GateCheck(
                name="declined_data_test",
                passed=True,
                message="Declined data test passed"
            ))
        elif declined_test:
            checks.append(GateCheck(
                name="declined_data_test",
                passed=False,
                message="Declined data test failed: staff proceeded as if data was provided",
                severity="critical"
            ))
        
        ambiguous_test = test_results.get("ambiguous_input_test", {})
        if ambiguous_test.get("passed", False):
            checks.append(GateCheck(
                name="ambiguous_input_test",
                passed=True,
                message="Ambiguous input test passed"
            ))
        elif ambiguous_test:
            questions_asked = ambiguous_test.get("questions_asked", 0)
            if questions_asked > 2:
                checks.append(GateCheck(
                    name="ambiguous_input_test",
                    passed=False,
                    message=f"Ambiguous input test: asked {questions_asked} questions (max 1-2)"
                ))
    
    # Determine result
    critical_failures = [c for c in checks if not c.passed and c.severity == "critical"]
    standard_failures = [c for c in checks if not c.passed and c.severity == "standard"]
    
    if critical_failures:
        result = GateResult.FAIL
        feedback = f"Critical failure handling issue: {critical_failures[0].message}"
        remediation = "Staff must never hallucinate missing data. Fix test failures."
    elif len(standard_failures) >= 3:
        result = GateResult.FAIL
        feedback = f"{len(standard_failures)} failure handling issues"
        remediation = "Document handling for: declined data, ambiguous input, out-of-scope"
    elif standard_failures:
        result = GateResult.CONDITIONAL
        feedback = "Minor failure handling gaps"
        remediation = "; ".join([c.message for c in standard_failures])
    else:
        result = GateResult.PASS
        feedback = "Failure handling meets standards"
        remediation = None
    
    return GateVerdict(
        gate_number=4,
        gate_name="Failure Handling",
        category="quality",
        result=result,
        checks=checks,
        feedback=feedback,
        remediation=remediation
    )


# =============================================================================
# GATE 5: Calibration Architecture
# =============================================================================

def validate_gate_5_calibration(submission: Dict[str, Any]) -> GateVerdict:
    """
    Gate 5: Calibration Architecture
    - Feedback collection mechanism
    - Corpus structure defined
    - Forward reference evidence
    - Hirer ownership stated
    """
    checks = []
    calibration = submission.get("calibration", {})
    
    # Check 1: Feedback questions defined
    feedback_questions = calibration.get("feedback_questions", [])
    if feedback_questions and len(feedback_questions) >= 2:
        checks.append(GateCheck(
            name="feedback_questions",
            passed=True,
            message=f"Defines {len(feedback_questions)} feedback question(s)"
        ))
    else:
        checks.append(GateCheck(
            name="feedback_questions",
            passed=False,
            message="Missing or insufficient feedback questions (need at least 2)"
        ))
    
    # Check 2: Corpus structure
    corpus_structure = calibration.get("corpus_structure", "")
    if corpus_structure and ("json" in corpus_structure.lower() or "structured" in corpus_structure.lower()):
        checks.append(GateCheck(
            name="corpus_structure",
            passed=True,
            message="Calibration corpus structure defined"
        ))
    elif corpus_structure:
        checks.append(GateCheck(
            name="corpus_structure",
            passed=True,
            message="Corpus structure documented"
        ))
    else:
        checks.append(GateCheck(
            name="corpus_structure",
            passed=False,
            message="Calibration corpus structure not defined"
        ))
    
    # Check 3: Forward reference
    forward_reference = calibration.get("forward_reference", False)
    forward_reference_desc = calibration.get("forward_reference_description", "")
    if forward_reference or forward_reference_desc:
        checks.append(GateCheck(
            name="forward_reference",
            passed=True,
            message="Corpus referenced in future engagements"
        ))
    else:
        checks.append(GateCheck(
            name="forward_reference",
            passed=False,
            message="No evidence that corpus influences future engagements"
        ))
    
    # Check 4: Hirer ownership
    hirer_ownership = calibration.get("hirer_ownership", False)
    if hirer_ownership or "hirer" in str(calibration).lower():
        checks.append(GateCheck(
            name="hirer_ownership",
            passed=True,
            message="Calibration data owned by hirer"
        ))
    else:
        checks.append(GateCheck(
            name="hirer_ownership",
            passed=False,
            message="Hirer ownership of calibration data not stated"
        ))
    
    # Determine result
    failures = [c for c in checks if not c.passed]
    
    if len(failures) >= 3:
        result = GateResult.FAIL
        feedback = "Calibration architecture incomplete"
        remediation = "Define: feedback questions, corpus structure, forward reference, hirer ownership"
    elif len(failures) >= 2:
        result = GateResult.CONDITIONAL
        feedback = "Calibration architecture needs improvement"
        remediation = "; ".join([c.message for c in failures])
    elif failures:
        result = GateResult.CONDITIONAL
        feedback = "Minor calibration issue"
        remediation = failures[0].message
    else:
        result = GateResult.PASS
        feedback = "Calibration architecture complete"
        remediation = None
    
    return GateVerdict(
        gate_number=5,
        gate_name="Calibration Architecture",
        category="quality",
        result=result,
        checks=checks,
        feedback=feedback,
        remediation=remediation
    )


# =============================================================================
# GATE 6: Security by Design
# =============================================================================

def validate_gate_6_security(submission: Dict[str, Any]) -> GateVerdict:
    """
    Gate 6: Security by Design
    - Input validation / prompt injection protection
    - Output filtering / PII detection
    - Least privilege access
    - Secret management
    - Code execution sandboxing (if applicable)
    """
    checks = []
    security = submission.get("security", {})
    security_tests = submission.get("security_test_results", {})
    
    # Check 1: Input validation
    input_validation = security.get("input_validation", False)
    if input_validation:
        checks.append(GateCheck(
            name="input_validation",
            passed=True,
            message="Input validation implemented"
        ))
    else:
        checks.append(GateCheck(
            name="input_validation",
            passed=False,
            message="Input validation not documented"
        ))
    
    # Check 2: Prompt injection tests
    prompt_injection_tests = security_tests.get("prompt_injection", {})
    if prompt_injection_tests:
        passed = prompt_injection_tests.get("passed", 0)
        total = prompt_injection_tests.get("total", 10)
        if passed == total:
            checks.append(GateCheck(
                name="prompt_injection_tests",
                passed=True,
                message=f"All {total} prompt injection tests passed"
            ))
        else:
            checks.append(GateCheck(
                name="prompt_injection_tests",
                passed=False,
                message=f"Prompt injection: {passed}/{total} tests passed",
                severity="critical"
            ))
    
    # Check 3: PII filtering
    pii_filtering = security.get("pii_filtering", False)
    pii_test = security_tests.get("pii_leakage", {})
    if pii_test.get("passed", True) and pii_filtering:
        checks.append(GateCheck(
            name="pii_filtering",
            passed=True,
            message="PII filtering in place"
        ))
    elif pii_test.get("passed") is False:
        checks.append(GateCheck(
            name="pii_filtering",
            passed=False,
            message="PII leakage detected in tests",
            severity="critical"
        ))
    elif not pii_filtering:
        checks.append(GateCheck(
            name="pii_filtering",
            passed=False,
            message="PII filtering not documented"
        ))
    
    # Check 4: Least privilege
    least_privilege = security.get("least_privilege", False)
    if least_privilege:
        checks.append(GateCheck(
            name="least_privilege",
            passed=True,
            message="Least privilege access documented"
        ))
    else:
        checks.append(GateCheck(
            name="least_privilege",
            passed=False,
            message="Least privilege access not documented"
        ))
    
    # Check 5: Secret management
    secret_scan = security_tests.get("secret_scan", {})
    if secret_scan.get("secrets_found", 0) == 0:
        checks.append(GateCheck(
            name="secret_management",
            passed=True,
            message="No hardcoded secrets found"
        ))
    elif secret_scan.get("secrets_found"):
        checks.append(GateCheck(
            name="secret_management",
            passed=False,
            message=f"Found {secret_scan['secrets_found']} hardcoded secret(s)",
            severity="critical"
        ))
    
    # Determine result
    critical_failures = [c for c in checks if not c.passed and c.severity == "critical"]
    standard_failures = [c for c in checks if not c.passed and c.severity == "standard"]
    
    if critical_failures:
        result = GateResult.FAIL
        feedback = f"CRITICAL security failure: {critical_failures[0].message}"
        remediation = "Fix all security test failures before resubmitting"
    elif len(standard_failures) >= 3:
        result = GateResult.FAIL
        feedback = f"{len(standard_failures)} security documentation gaps"
        remediation = "Document: input validation, PII filtering, least privilege, secret management"
    elif standard_failures:
        result = GateResult.CONDITIONAL
        feedback = "Minor security documentation gaps"
        remediation = "; ".join([c.message for c in standard_failures])
    else:
        result = GateResult.PASS
        feedback = "Security standards met"
        remediation = None
    
    return GateVerdict(
        gate_number=6,
        gate_name="Security by Design",
        category="safety",
        result=result,
        checks=checks,
        feedback=feedback,
        remediation=remediation
    )


# =============================================================================
# GATE 7: AI Harm Prevention
# =============================================================================

def validate_gate_7_ai_harm(submission: Dict[str, Any]) -> GateVerdict:
    """
    Gate 7: AI Harm Prevention
    - Content safety
    - Bias detection
    - Manipulation prevention
    - Confidence disclosure
    - Human escalation for high-stakes
    """
    checks = []
    harm_prevention = submission.get("harm_prevention", {})
    harm_tests = submission.get("harm_test_results", {})
    
    # Check 1: Content safety
    content_safety = harm_prevention.get("content_safety", False)
    content_test = harm_tests.get("content_safety", {})
    if content_test.get("passed", True) and content_safety:
        checks.append(GateCheck(
            name="content_safety",
            passed=True,
            message="Content safety controls in place"
        ))
    elif content_test.get("passed") is False:
        checks.append(GateCheck(
            name="content_safety",
            passed=False,
            message="Content safety test failed",
            severity="critical"
        ))
    else:
        checks.append(GateCheck(
            name="content_safety",
            passed=False,
            message="Content safety not documented"
        ))
    
    # Check 2: Bias detection
    bias_detection = harm_prevention.get("bias_detection", False)
    bias_test = harm_tests.get("bias_audit", {})
    if bias_test.get("passed", True):
        checks.append(GateCheck(
            name="bias_detection",
            passed=True,
            message="Bias audit passed"
        ))
    elif bias_test.get("passed") is False:
        checks.append(GateCheck(
            name="bias_detection",
            passed=False,
            message="Statistically significant bias detected",
            severity="critical"
        ))
    elif not bias_detection:
        checks.append(GateCheck(
            name="bias_detection",
            passed=False,
            message="Bias detection not documented"
        ))
    
    # Check 3: No manipulation
    manipulation_test = harm_tests.get("manipulation", {})
    if manipulation_test.get("passed", True):
        checks.append(GateCheck(
            name="no_manipulation",
            passed=True,
            message="Manipulation tests passed"
        ))
    elif manipulation_test.get("passed") is False:
        checks.append(GateCheck(
            name="no_manipulation",
            passed=False,
            message="Staff was successfully manipulated in tests",
            severity="critical"
        ))
    
    # Check 4: Confidence disclosure
    confidence_disclosure = harm_prevention.get("confidence_disclosure", False)
    if confidence_disclosure:
        checks.append(GateCheck(
            name="confidence_disclosure",
            passed=True,
            message="Confidence levels disclosed in outputs"
        ))
    else:
        checks.append(GateCheck(
            name="confidence_disclosure",
            passed=False,
            message="Confidence disclosure not implemented"
        ))
    
    # Check 5: High-stakes escalation
    high_stakes_escalation = harm_prevention.get("high_stakes_escalation", False)
    if high_stakes_escalation:
        checks.append(GateCheck(
            name="high_stakes_escalation",
            passed=True,
            message="High-stakes decisions require human approval"
        ))
    else:
        checks.append(GateCheck(
            name="high_stakes_escalation",
            passed=False,
            message="High-stakes escalation path not defined"
        ))
    
    # Determine result
    critical_failures = [c for c in checks if not c.passed and c.severity == "critical"]
    standard_failures = [c for c in checks if not c.passed and c.severity == "standard"]
    
    if critical_failures:
        result = GateResult.FAIL
        feedback = f"CRITICAL AI harm issue: {critical_failures[0].message}"
        remediation = "Address all AI harm test failures"
    elif len(standard_failures) >= 3:
        result = GateResult.FAIL
        feedback = f"{len(standard_failures)} AI harm prevention gaps"
        remediation = "Document: content safety, bias detection, confidence disclosure, high-stakes escalation"
    elif standard_failures:
        result = GateResult.CONDITIONAL
        feedback = "Minor AI harm prevention gaps"
        remediation = "; ".join([c.message for c in standard_failures])
    else:
        result = GateResult.PASS
        feedback = "AI harm prevention standards met"
        remediation = None
    
    return GateVerdict(
        gate_number=7,
        gate_name="AI Harm Prevention",
        category="safety",
        result=result,
        checks=checks,
        feedback=feedback,
        remediation=remediation
    )


# =============================================================================
# GATE 8: Operational Resilience
# =============================================================================

def validate_gate_8_resilience(submission: Dict[str, Any]) -> GateVerdict:
    """
    Gate 8: Operational Resilience
    - Graceful degradation
    - Error logging
    - Recovery procedure
    - Kill switch
    - Incident notification
    """
    checks = []
    resilience = submission.get("resilience", {})
    resilience_tests = submission.get("resilience_test_results", {})
    
    # Check 1: Graceful degradation
    graceful_degradation = resilience.get("graceful_degradation", False)
    degradation_test = resilience_tests.get("degradation", {})
    if degradation_test.get("data_preserved", True):
        checks.append(GateCheck(
            name="graceful_degradation",
            passed=True,
            message="Graceful degradation: no data loss on failure"
        ))
    elif degradation_test.get("data_preserved") is False:
        checks.append(GateCheck(
            name="graceful_degradation",
            passed=False,
            message="Data loss detected during simulated failure",
            severity="critical"
        ))
    elif not graceful_degradation:
        checks.append(GateCheck(
            name="graceful_degradation",
            passed=False,
            message="Graceful degradation not documented"
        ))
    
    # Check 2: Error logging
    error_logging = resilience.get("error_logging", False)
    if error_logging:
        checks.append(GateCheck(
            name="error_logging",
            passed=True,
            message="Error logging implemented"
        ))
    else:
        checks.append(GateCheck(
            name="error_logging",
            passed=False,
            message="Error logging not documented"
        ))
    
    # Check 3: Recovery procedure
    recovery_procedure = resilience.get("recovery_procedure", "")
    if recovery_procedure and len(recovery_procedure) > 20:
        checks.append(GateCheck(
            name="recovery_procedure",
            passed=True,
            message="Recovery procedure documented"
        ))
    else:
        checks.append(GateCheck(
            name="recovery_procedure",
            passed=False,
            message="Recovery procedure not documented"
        ))
    
    # Check 4: Kill switch
    kill_switch = resilience.get("kill_switch", False)
    kill_switch_test = resilience_tests.get("kill_switch", {})
    if kill_switch_test.get("response_time_seconds", 999) <= 30:
        checks.append(GateCheck(
            name="kill_switch",
            passed=True,
            message=f"Kill switch works ({kill_switch_test['response_time_seconds']}s response)"
        ))
    elif kill_switch_test.get("response_time_seconds", 999) > 30:
        checks.append(GateCheck(
            name="kill_switch",
            passed=False,
            message="Kill switch too slow (>30s response)",
            severity="critical"
        ))
    elif not kill_switch:
        checks.append(GateCheck(
            name="kill_switch",
            passed=False,
            message="Kill switch not implemented"
        ))
    
    # Check 5: Incident notification
    incident_notification = resilience.get("incident_notification", False)
    if incident_notification:
        checks.append(GateCheck(
            name="incident_notification",
            passed=True,
            message="Incident notification to hirers implemented"
        ))
    else:
        checks.append(GateCheck(
            name="incident_notification",
            passed=False,
            message="Incident notification not documented"
        ))
    
    # Determine result
    critical_failures = [c for c in checks if not c.passed and c.severity == "critical"]
    standard_failures = [c for c in checks if not c.passed and c.severity == "standard"]
    
    if critical_failures:
        result = GateResult.FAIL
        feedback = f"CRITICAL resilience issue: {critical_failures[0].message}"
        remediation = "Fix data loss and kill switch issues"
    elif len(standard_failures) >= 3:
        result = GateResult.FAIL
        feedback = f"{len(standard_failures)} resilience gaps"
        remediation = "Document: graceful degradation, error logging, recovery, kill switch, notifications"
    elif standard_failures:
        result = GateResult.CONDITIONAL
        feedback = "Minor resilience gaps"
        remediation = "; ".join([c.message for c in standard_failures])
    else:
        result = GateResult.PASS
        feedback = "Operational resilience standards met"
        remediation = None
    
    return GateVerdict(
        gate_number=8,
        gate_name="Operational Resilience",
        category="safety",
        result=result,
        checks=checks,
        feedback=feedback,
        remediation=remediation
    )


# =============================================================================
# GATE 9: Listing Accuracy
# =============================================================================

def validate_gate_9_listing_accuracy(submission: Dict[str, Any]) -> GateVerdict:
    """
    Gate 9: Listing Accuracy
    - Claims verification
    - Screenshot authenticity
    - Demo video authenticity
    - No misleading language
    """
    checks = []
    listing = submission.get("listing_assets", {})
    accuracy_tests = submission.get("accuracy_test_results", {})
    
    # Check 1: ROI claims have evidence
    roi_claims = listing.get("roi_chips", [])
    roi_evidence = listing.get("roi_evidence", {})
    
    claims_with_evidence = 0
    for claim in roi_claims:
        if claim in roi_evidence or any(claim in str(v) for v in roi_evidence.values()):
            claims_with_evidence += 1
    
    if roi_claims and claims_with_evidence == len(roi_claims):
        checks.append(GateCheck(
            name="roi_claims_verified",
            passed=True,
            message=f"All {len(roi_claims)} ROI claims have supporting evidence"
        ))
    elif roi_claims:
        checks.append(GateCheck(
            name="roi_claims_verified",
            passed=False,
            message=f"Only {claims_with_evidence}/{len(roi_claims)} ROI claims have evidence"
        ))
    
    # Check 2: Screenshots match live UI
    screenshot_test = accuracy_tests.get("screenshot_verification", {})
    if screenshot_test.get("passed", True):
        checks.append(GateCheck(
            name="screenshots_authentic",
            passed=True,
            message="Screenshots match live staff UI"
        ))
    elif screenshot_test.get("passed") is False:
        checks.append(GateCheck(
            name="screenshots_authentic",
            passed=False,
            message="Screenshots do not match live UI",
            severity="critical"
        ))
    
    # Check 3: Demo video authentic
    video_test = accuracy_tests.get("video_verification", {})
    if video_test.get("passed", True):
        checks.append(GateCheck(
            name="demo_video_authentic",
            passed=True,
            message="Demo video shows real staff operation"
        ))
    elif video_test.get("passed") is False:
        checks.append(GateCheck(
            name="demo_video_authentic",
            passed=False,
            message="Demo video shows features not in submission"
        ))
    
    # Check 4: No weasel words
    description = listing.get("description", "")
    weasel_words = ["up to", "as much as", "potentially", "may", "could", "might"]
    found_weasel = [w for w in weasel_words if w in description.lower()]
    if found_weasel:
        checks.append(GateCheck(
            name="no_weasel_words",
            passed=False,
            message=f"Description uses hedging language: {', '.join(found_weasel)}"
        ))
    else:
        checks.append(GateCheck(
            name="no_weasel_words",
            passed=True,
            message="Description uses clear, confident language"
        ))
    
    # Determine result
    critical_failures = [c for c in checks if not c.passed and c.severity == "critical"]
    standard_failures = [c for c in checks if not c.passed and c.severity == "standard"]
    
    if critical_failures:
        result = GateResult.FAIL
        feedback = f"CRITICAL accuracy issue: {critical_failures[0].message}"
        remediation = "Screenshots and video must match actual staff"
    elif len(standard_failures) >= 2:
        result = GateResult.FAIL
        feedback = f"{len(standard_failures)} listing accuracy issues"
        remediation = "; ".join([c.message for c in standard_failures])
    elif standard_failures:
        result = GateResult.CONDITIONAL
        feedback = "Minor listing accuracy issues"
        remediation = standard_failures[0].message
    else:
        result = GateResult.PASS
        feedback = "Listing accuracy verified"
        remediation = None
    
    return GateVerdict(
        gate_number=9,
        gate_name="Listing Accuracy",
        category="trust",
        result=result,
        checks=checks,
        feedback=feedback,
        remediation=remediation
    )


# =============================================================================
# GATE 10: Transparent Pricing
# =============================================================================

def validate_gate_10_pricing(submission: Dict[str, Any]) -> GateVerdict:
    """
    Gate 10: Transparent Pricing
    - Price clearly stated
    - No hidden fees
    - Trial terms clear
    - Cancellation terms
    """
    checks = []
    pricing = submission.get("pricing", {})
    
    # Check 1: Price stated
    monthly_price = pricing.get("monthly", 0)
    annual_price = pricing.get("annual", 0)
    if monthly_price > 0:
        checks.append(GateCheck(
            name="price_stated",
            passed=True,
            message=f"Monthly price: ${monthly_price}"
        ))
    else:
        checks.append(GateCheck(
            name="price_stated",
            passed=False,
            message="Monthly price not specified",
            severity="critical"
        ))
    
    # Check 2: No hidden fees
    additional_fees = pricing.get("additional_fees", [])
    if not additional_fees:
        checks.append(GateCheck(
            name="no_hidden_fees",
            passed=True,
            message="No additional fees"
        ))
    else:
        fees_disclosed = pricing.get("fees_disclosed", False)
        if fees_disclosed:
            checks.append(GateCheck(
                name="no_hidden_fees",
                passed=True,
                message=f"Additional fees disclosed: {', '.join(additional_fees)}"
            ))
        else:
            checks.append(GateCheck(
                name="no_hidden_fees",
                passed=False,
                message="Additional fees exist but not disclosed in listing"
            ))
    
    # Check 3: Trial terms
    trial_duration = pricing.get("trial_days", 0)
    trial_restrictions = pricing.get("trial_restrictions", "")
    if trial_duration >= 14:
        checks.append(GateCheck(
            name="trial_terms",
            passed=True,
            message=f"Trial: {trial_duration} days, terms clear"
        ))
    elif trial_duration > 0:
        checks.append(GateCheck(
            name="trial_terms",
            passed=False,
            message=f"Trial only {trial_duration} days (minimum 14)"
        ))
    else:
        checks.append(GateCheck(
            name="trial_terms",
            passed=False,
            message="No trial offered"
        ))
    
    # Check 4: Cancellation terms
    cancellation = pricing.get("cancellation_terms", "")
    if cancellation and len(cancellation) > 10:
        checks.append(GateCheck(
            name="cancellation_terms",
            passed=True,
            message="Cancellation terms documented"
        ))
    else:
        checks.append(GateCheck(
            name="cancellation_terms",
            passed=False,
            message="Cancellation terms not documented"
        ))
    
    # Determine result
    critical_failures = [c for c in checks if not c.passed and c.severity == "critical"]
    standard_failures = [c for c in checks if not c.passed and c.severity == "standard"]
    
    if critical_failures:
        result = GateResult.FAIL
        feedback = "Pricing not transparent"
        remediation = "Specify monthly price clearly"
    elif len(standard_failures) >= 2:
        result = GateResult.CONDITIONAL
        feedback = "Pricing transparency issues"
        remediation = "; ".join([c.message for c in standard_failures])
    elif standard_failures:
        result = GateResult.CONDITIONAL
        feedback = "Minor pricing documentation gap"
        remediation = standard_failures[0].message
    else:
        result = GateResult.PASS
        feedback = "Pricing transparent"
        remediation = None
    
    return GateVerdict(
        gate_number=10,
        gate_name="Transparent Pricing",
        category="trust",
        result=result,
        checks=checks,
        feedback=feedback,
        remediation=remediation
    )


# =============================================================================
# GATE 11: Data Protection & Privacy
# =============================================================================

def validate_gate_11_data_protection(submission: Dict[str, Any]) -> GateVerdict:
    """
    Gate 11: Data Protection & Privacy
    - Data minimization
    - Lawful basis
    - Consent mechanism
    - Data subject rights
    - ADM transparency
    - Retention policy
    """
    checks = []
    data_protection = submission.get("data_protection", {})
    
    # Check 1: Data minimization
    data_collected = data_protection.get("data_collected", [])
    data_justified = data_protection.get("data_justified", {})
    
    unjustified = [d for d in data_collected if d not in data_justified]
    if not unjustified and data_collected:
        checks.append(GateCheck(
            name="data_minimization",
            passed=True,
            message="All collected data justified for function"
        ))
    elif unjustified:
        checks.append(GateCheck(
            name="data_minimization",
            passed=False,
            message=f"Unjustified data collection: {', '.join(unjustified)}"
        ))
    elif not data_collected:
        checks.append(GateCheck(
            name="data_minimization",
            passed=True,
            message="No personal data collected"
        ))
    
    # Check 2: Lawful basis
    lawful_basis = data_protection.get("lawful_basis", "")
    valid_bases = ["consent", "contract", "legitimate_interest", "legal_obligation"]
    if lawful_basis in valid_bases:
        checks.append(GateCheck(
            name="lawful_basis",
            passed=True,
            message=f"Lawful basis: {lawful_basis}"
        ))
    elif lawful_basis:
        checks.append(GateCheck(
            name="lawful_basis",
            passed=False,
            message=f"Invalid lawful basis: {lawful_basis}"
        ))
    else:
        checks.append(GateCheck(
            name="lawful_basis",
            passed=False,
            message="Lawful basis for processing not specified"
        ))
    
    # Check 3: Data subject rights
    rights_implemented = data_protection.get("rights_implemented", [])
    required_rights = ["access", "rectification", "erasure"]
    missing_rights = [r for r in required_rights if r not in rights_implemented]
    if not missing_rights:
        checks.append(GateCheck(
            name="data_subject_rights",
            passed=True,
            message="Data subject rights implemented"
        ))
    else:
        checks.append(GateCheck(
            name="data_subject_rights",
            passed=False,
            message=f"Missing data rights: {', '.join(missing_rights)}"
        ))
    
    # Check 4: Retention policy
    retention_days = data_protection.get("retention_days", 0)
    if retention_days > 0:
        checks.append(GateCheck(
            name="retention_policy",
            passed=True,
            message=f"Data retention: {retention_days} days"
        ))
    else:
        checks.append(GateCheck(
            name="retention_policy",
            passed=False,
            message="Data retention policy not specified"
        ))
    
    # Determine result
    failures = [c for c in checks if not c.passed]
    
    if len(failures) >= 3:
        result = GateResult.FAIL
        feedback = "Data protection incomplete"
        remediation = "Address: data minimization, lawful basis, subject rights, retention"
    elif len(failures) >= 2:
        result = GateResult.CONDITIONAL
        feedback = "Data protection gaps"
        remediation = "; ".join([c.message for c in failures])
    elif failures:
        result = GateResult.CONDITIONAL
        feedback = "Minor data protection gap"
        remediation = failures[0].message
    else:
        result = GateResult.PASS
        feedback = "Data protection compliant"
        remediation = None
    
    return GateVerdict(
        gate_number=11,
        gate_name="Data Protection & Privacy",
        category="compliance",
        result=result,
        checks=checks,
        feedback=feedback,
        remediation=remediation
    )


# =============================================================================
# GATE 12: AI Governance & Ethics
# =============================================================================

def validate_gate_12_ai_governance(submission: Dict[str, Any]) -> GateVerdict:
    """
    Gate 12: AI Governance & Ethics
    - Risk classification
    - Human oversight
    - AI transparency
    - Documentation
    - Incident reporting
    """
    checks = []
    governance = submission.get("ai_governance", {})
    identity = submission.get("identity_brief", {})
    
    # Check 1: Risk classification
    risk_level = governance.get("risk_level", "")
    valid_levels = ["minimal", "limited", "high"]
    prohibited_uses = governance.get("prohibited_uses", [])
    
    if risk_level in valid_levels:
        checks.append(GateCheck(
            name="risk_classification",
            passed=True,
            message=f"Risk level: {risk_level}"
        ))
    elif risk_level == "prohibited":
        checks.append(GateCheck(
            name="risk_classification",
            passed=False,
            message="Staff involves prohibited AI use case",
            severity="critical"
        ))
    else:
        checks.append(GateCheck(
            name="risk_classification",
            passed=False,
            message="Risk level not classified"
        ))
    
    # Check 2: Human oversight (required for high-risk)
    human_oversight = governance.get("human_oversight", False)
    if risk_level == "high" and not human_oversight:
        checks.append(GateCheck(
            name="human_oversight",
            passed=False,
            message="High-risk staff requires human oversight mechanism",
            severity="critical"
        ))
    elif human_oversight:
        checks.append(GateCheck(
            name="human_oversight",
            passed=True,
            message="Human oversight mechanism in place"
        ))
    else:
        checks.append(GateCheck(
            name="human_oversight",
            passed=True,
            message="Human oversight not required for risk level"
        ))
    
    # Check 3: AI transparency
    ai_disclosure = governance.get("ai_disclosure", False)
    if ai_disclosure:
        checks.append(GateCheck(
            name="ai_disclosure",
            passed=True,
            message="Users informed they're interacting with AI"
        ))
    else:
        checks.append(GateCheck(
            name="ai_disclosure",
            passed=False,
            message="AI disclosure to users not implemented"
        ))
    
    # Check 4: Documentation
    tech_docs = governance.get("technical_documentation", False)
    training_data = governance.get("training_data_documented", False)
    if tech_docs and training_data:
        checks.append(GateCheck(
            name="documentation",
            passed=True,
            message="Technical documentation complete"
        ))
    elif tech_docs or training_data:
        checks.append(GateCheck(
            name="documentation",
            passed=False,
            message="Incomplete technical documentation"
        ))
    else:
        checks.append(GateCheck(
            name="documentation",
            passed=False,
            message="Technical documentation missing"
        ))
    
    # Check 5: Incident reporting
    incident_process = governance.get("incident_reporting_process", False)
    if incident_process:
        checks.append(GateCheck(
            name="incident_reporting",
            passed=True,
            message="Incident reporting process defined"
        ))
    else:
        checks.append(GateCheck(
            name="incident_reporting",
            passed=False,
            message="Incident reporting process not defined"
        ))
    
    # Determine result
    critical_failures = [c for c in checks if not c.passed and c.severity == "critical"]
    standard_failures = [c for c in checks if not c.passed and c.severity == "standard"]
    
    if critical_failures:
        result = GateResult.FAIL
        feedback = f"CRITICAL governance issue: {critical_failures[0].message}"
        remediation = "High-risk staff must have human oversight. Prohibited uses not allowed."
    elif len(standard_failures) >= 3:
        result = GateResult.FAIL
        feedback = f"{len(standard_failures)} governance gaps"
        remediation = "Complete: risk classification, AI disclosure, documentation, incident reporting"
    elif standard_failures:
        result = GateResult.CONDITIONAL
        feedback = "Minor governance gaps"
        remediation = "; ".join([c.message for c in standard_failures])
    else:
        result = GateResult.PASS
        feedback = "AI governance standards met"
        remediation = None
    
    return GateVerdict(
        gate_number=12,
        gate_name="AI Governance & Ethics",
        category="compliance",
        result=result,
        checks=checks,
        feedback=feedback,
        remediation=remediation
    )
