"""
Reviewer Agent — API Routes
============================
REST API for submission validation.
"""

import json
from flask import Blueprint, request, jsonify, current_app
from .engine import (
    run_full_review,
    run_gate_review,
    verdict_to_dict,
    generate_feedback_report,
    validate_submission_completeness,
)

reviewer_bp = Blueprint('reviewer', __name__, url_prefix='/api/reviewer')


@reviewer_bp.route('/validate', methods=['POST'])
def validate_submission():
    """
    Full 12-gate validation of a submission.
    
    Request body: JSON submission package
    Response: Verdict with pass/fail per gate
    """
    try:
        submission = request.get_json(silent=True)
        if not submission:
            return jsonify({
                'error': 'JSON submission required',
                'hint': 'Send your submission package as JSON body'
            }), 400
        
        # Run full review
        verdict = run_full_review(submission)
        
        current_app.logger.info(
            f"Reviewer: {verdict.result} — "
            f"{len([g for g in verdict.gates if g.result.value == 'pass'])}/12 gates passed"
        )
        
        return jsonify(verdict_to_dict(verdict)), 200
        
    except Exception as e:
        current_app.logger.error(f"Reviewer error: {e}")
        return jsonify({'error': 'Review failed', 'message': str(e)}), 500


@reviewer_bp.route('/validate/gates', methods=['POST'])
def validate_specific_gates():
    """
    Validate specific gates only (for resubmission).
    
    Request body: { "submission": {...}, "gates": [1, 2, 3] }
    Response: Verdict for specified gates only
    """
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({'error': 'JSON body required'}), 400
        
        submission = data.get('submission', {})
        gates = data.get('gates', [])
        
        if not gates:
            return jsonify({'error': 'gates array required'}), 400
        
        if not all(isinstance(g, int) and 1 <= g <= 12 for g in gates):
            return jsonify({'error': 'gates must be integers 1-12'}), 400
        
        verdict = run_gate_review(submission, gates)
        
        current_app.logger.info(
            f"Reviewer (gates {gates}): {verdict.result}"
        )
        
        return jsonify(verdict_to_dict(verdict)), 200
        
    except Exception as e:
        current_app.logger.error(f"Reviewer error: {e}")
        return jsonify({'error': 'Review failed', 'message': str(e)}), 500


@reviewer_bp.route('/validate/check', methods=['POST'])
def check_completeness():
    """
    Quick completeness check before full validation.
    
    Request body: JSON submission package
    Response: { complete: bool, missing: [...], warnings: [...] }
    """
    try:
        submission = request.get_json(silent=True)
        if not submission:
            return jsonify({'error': 'JSON submission required'}), 400
        
        result = validate_submission_completeness(submission)
        return jsonify(result), 200
        
    except Exception as e:
        current_app.logger.error(f"Completeness check error: {e}")
        return jsonify({'error': 'Check failed', 'message': str(e)}), 500


@reviewer_bp.route('/report', methods=['POST'])
def generate_report():
    """
    Generate human-readable feedback report.
    
    Request body: JSON submission package
    Response: { report: "..." } (plain text report)
    """
    try:
        submission = request.get_json(silent=True)
        if not submission:
            return jsonify({'error': 'JSON submission required'}), 400
        
        verdict = run_full_review(submission)
        report = generate_feedback_report(verdict)
        
        return jsonify({
            'result': verdict.result,
            'report': report
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Report generation error: {e}")
        return jsonify({'error': 'Report failed', 'message': str(e)}), 500


@reviewer_bp.route('/gates', methods=['GET'])
def list_gates():
    """
    List all 12 gates with descriptions.
    """
    gates = [
        {
            "number": 1,
            "name": "Role Clarity",
            "category": "quality",
            "description": "One-sentence role description, clear scope boundaries"
        },
        {
            "number": 2,
            "name": "Output Standard",
            "category": "quality",
            "description": "Named outputs with format, frequency, and specimens"
        },
        {
            "number": 3,
            "name": "Hirer Experience",
            "category": "quality",
            "description": "Autonomous decisions, escalation triggers, time commitment"
        },
        {
            "number": 4,
            "name": "Failure Handling",
            "category": "quality",
            "description": "Graceful handling of declined data, ambiguous input, out-of-scope"
        },
        {
            "number": 5,
            "name": "Calibration Architecture",
            "category": "quality",
            "description": "Feedback collection, corpus structure, forward reference"
        },
        {
            "number": 6,
            "name": "Security by Design",
            "category": "safety",
            "description": "Input validation, PII filtering, least privilege, secrets"
        },
        {
            "number": 7,
            "name": "AI Harm Prevention",
            "category": "safety",
            "description": "Content safety, bias detection, manipulation prevention"
        },
        {
            "number": 8,
            "name": "Operational Resilience",
            "category": "safety",
            "description": "Graceful degradation, kill switch, incident notification"
        },
        {
            "number": 9,
            "name": "Listing Accuracy",
            "category": "trust",
            "description": "Claims verified, screenshots match reality"
        },
        {
            "number": 10,
            "name": "Transparent Pricing",
            "category": "trust",
            "description": "Clear pricing, trial terms, no hidden fees"
        },
        {
            "number": 11,
            "name": "Data Protection & Privacy",
            "category": "compliance",
            "description": "GDPR compliance, data minimization, retention policy"
        },
        {
            "number": 12,
            "name": "AI Governance & Ethics",
            "category": "compliance",
            "description": "Risk classification, human oversight, AI disclosure"
        }
    ]
    return jsonify({"gates": gates}), 200
