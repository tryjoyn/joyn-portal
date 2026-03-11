"""
shared/gate_scoring.py — Shared Gate Scoring Logic

Used by both Sage (real-time during conversation) and Reviewer Agent (final evaluation).
Single source of truth for gate criteria.
"""
from __future__ import annotations
import re
from typing import Optional

# Gate definitions with scoring criteria
GATES = {
    "01_role_clarity": {
        "name": "Role Clarity",
        "weight": 20,
        "criteria": {
            "has_target_hirer": "Specifies who hires this (job title, industry, or company type)",
            "has_deliverable": "States what the hirer gets",
            "is_specific": "Not vague (no 'helps with', 'assists', 'manages')",
            "is_concise": "Under 30 words"
        }
    },
    "02_output_standard": {
        "name": "Output Standard", 
        "weight": 25,
        "criteria": {
            "has_named_outputs": "At least one named output",
            "has_format": "Format specified (email, PDF, Slack, etc.)",
            "has_trigger": "Trigger condition defined",
            "has_frequency": "Frequency/schedule specified"
        }
    },
    "03_hirer_experience": {
        "name": "Hirer Experience",
        "weight": 20,
        "criteria": {
            "has_onboarding_time": "Onboarding duration specified",
            "has_intervention_points": "At least one intervention point defined",
            "has_time_commitment": "Ongoing time commitment stated"
        }
    },
    "04_failure_handling": {
        "name": "Failure Handling",
        "weight": 20,
        "criteria": {
            "has_scenarios": "At least one failure scenario",
            "has_three_scenarios": "Three distinct failure scenarios",
            "has_responses": "Specific responses defined (not 'handles gracefully')"
        }
    },
    "05_calibration": {
        "name": "Calibration Architecture",
        "weight": 15,
        "criteria": {
            "has_feedback_mechanism": "Feedback collection method defined",
            "has_improvement_logic": "How feedback improves the staff",
            "has_calibration_questions": "At least one calibration question"
        }
    }
}

# Vague phrases that indicate low quality
VAGUE_PHRASES = [
    "helps with", "assists with", "manages", "handles things",
    "various tasks", "multiple things", "as needed", "when necessary",
    "efficiently", "effectively", "seamlessly", "gracefully",
    "comprehensive", "robust", "powerful", "advanced",
    "ai-powered", "intelligent", "smart"
]


def score_gate(gate_id: str, content: str) -> dict:
    """
    Score a single gate based on content provided.
    
    Returns:
        {
            "gate": "01_role_clarity",
            "name": "Role Clarity",
            "score": 75,  # 0-100
            "status": "partial",  # pass|partial|fail
            "met_criteria": ["has_target_hirer", "has_deliverable"],
            "missing_criteria": ["is_specific"],
            "feedback": "Good start, but be more specific about..."
        }
    """
    if gate_id not in GATES:
        return {"gate": gate_id, "score": 0, "status": "fail", "feedback": "Unknown gate"}
    
    gate = GATES[gate_id]
    met = []
    missing = []
    
    content_lower = content.lower()
    word_count = len(content.split())
    
    if gate_id == "01_role_clarity":
        # Check for target hirer indicators
        hirer_indicators = ["broker", "agent", "manager", "owner", "director", "team", "firm", "practice", "company", "business"]
        if any(ind in content_lower for ind in hirer_indicators):
            met.append("has_target_hirer")
        else:
            missing.append("has_target_hirer")
        
        # Check for deliverable
        deliverable_indicators = ["get", "receive", "deliver", "provide", "send", "alert", "report", "produce"]
        if any(ind in content_lower for ind in deliverable_indicators):
            met.append("has_deliverable")
        else:
            missing.append("has_deliverable")
        
        # Check for vagueness
        if any(vague in content_lower for vague in VAGUE_PHRASES):
            missing.append("is_specific")
        else:
            met.append("is_specific")
        
        # Check conciseness
        if word_count <= 30:
            met.append("is_concise")
        else:
            missing.append("is_concise")
    
    elif gate_id == "02_output_standard":
        # Check for named outputs
        if re.search(r'[A-Z][a-z]+\s+(Alert|Report|Digest|Summary|Score|Update|Notification)', content):
            met.append("has_named_outputs")
        elif any(word in content_lower for word in ["alert", "report", "digest", "summary", "notification", "email", "pdf"]):
            met.append("has_named_outputs")
        else:
            missing.append("has_named_outputs")
        
        # Check for format
        formats = ["email", "pdf", "slack", "sms", "dashboard", "spreadsheet", "csv", "document"]
        if any(fmt in content_lower for fmt in formats):
            met.append("has_format")
        else:
            missing.append("has_format")
        
        # Check for trigger
        triggers = ["when", "trigger", "after", "upon", "if", "every", "daily", "weekly", "monthly", "scheduled"]
        if any(trg in content_lower for trg in triggers):
            met.append("has_trigger")
        else:
            missing.append("has_trigger")
        
        # Check for frequency
        frequencies = ["daily", "weekly", "monthly", "hourly", "real-time", "immediately", "8am", "morning", "end of day"]
        if any(freq in content_lower for freq in frequencies):
            met.append("has_frequency")
        else:
            missing.append("has_frequency")
    
    elif gate_id == "03_hirer_experience":
        # Check for onboarding time
        if re.search(r'\d+\s*(min|minute|hour|day)', content_lower):
            met.append("has_onboarding_time")
        else:
            missing.append("has_onboarding_time")
        
        # Check for intervention points
        intervention_words = ["review", "approve", "confirm", "check", "intervene", "step in", "sign off"]
        if any(word in content_lower for word in intervention_words):
            met.append("has_intervention_points")
        else:
            missing.append("has_intervention_points")
        
        # Check for time commitment
        if re.search(r'\d+\s*(min|minute|hour).*per\s*(week|day|month)', content_lower) or "per week" in content_lower:
            met.append("has_time_commitment")
        else:
            missing.append("has_time_commitment")
    
    elif gate_id == "04_failure_handling":
        # Count scenarios (look for numbered lists or scenario descriptions)
        scenario_count = len(re.findall(r'(?:^|\n)\s*(?:\d+[.\):]|\-|\•)', content)) or content_lower.count("scenario") or content_lower.count("if ")
        
        if scenario_count >= 1:
            met.append("has_scenarios")
        else:
            missing.append("has_scenarios")
        
        if scenario_count >= 3:
            met.append("has_three_scenarios")
        else:
            missing.append("has_three_scenarios")
        
        # Check for specific responses (not vague)
        vague_failure = ["handle gracefully", "handle appropriately", "deal with", "manage the error"]
        if not any(vague in content_lower for vague in vague_failure):
            if any(word in content_lower for word in ["retry", "notify", "flag", "escalate", "pause", "queue", "log"]):
                met.append("has_responses")
            else:
                missing.append("has_responses")
        else:
            missing.append("has_responses")
    
    elif gate_id == "05_calibration":
        # Check for feedback mechanism
        feedback_words = ["feedback", "thumbs", "rating", "survey", "question", "ask", "review"]
        if any(word in content_lower for word in feedback_words):
            met.append("has_feedback_mechanism")
        else:
            missing.append("has_feedback_mechanism")
        
        # Check for improvement logic
        improvement_words = ["improve", "learn", "adjust", "update", "refine", "train", "carry forward", "remember"]
        if any(word in content_lower for word in improvement_words):
            met.append("has_improvement_logic")
        else:
            missing.append("has_improvement_logic")
        
        # Check for calibration questions
        if "?" in content or "question" in content_lower:
            met.append("has_calibration_questions")
        else:
            missing.append("has_calibration_questions")
    
    # Calculate score
    total_criteria = len(met) + len(missing)
    score = int((len(met) / total_criteria) * 100) if total_criteria > 0 else 0
    
    # Determine status
    if score >= 80:
        status = "pass"
    elif score >= 50:
        status = "partial"
    else:
        status = "fail"
    
    # Generate feedback
    feedback = _generate_feedback(gate_id, met, missing, content)
    
    return {
        "gate": gate_id,
        "name": gate["name"],
        "score": score,
        "status": status,
        "met_criteria": met,
        "missing_criteria": missing,
        "feedback": feedback
    }


def score_all_gates(collected_data: dict) -> dict:
    """
    Score all gates based on collected conversation data.
    
    Args:
        collected_data: {
            "role_clarity": "...",
            "output_standard": "...",
            "hirer_experience": "...",
            "failure_handling": "...",
            "calibration": "..."
        }
    
    Returns:
        {
            "overall_score": 72,
            "overall_status": "partial",
            "gates": [...],
            "ready_for_spec": False,
            "blocking_gates": ["04_failure_handling"]
        }
    """
    gate_mapping = {
        "role_clarity": "01_role_clarity",
        "output_standard": "02_output_standard",
        "hirer_experience": "03_hirer_experience",
        "failure_handling": "04_failure_handling",
        "calibration": "05_calibration"
    }
    
    results = []
    total_weighted_score = 0
    total_weight = 0
    
    for key, gate_id in gate_mapping.items():
        content = collected_data.get(key, "")
        if content:
            result = score_gate(gate_id, content)
            results.append(result)
            
            weight = GATES[gate_id]["weight"]
            total_weighted_score += result["score"] * weight
            total_weight += weight
    
    overall_score = int(total_weighted_score / total_weight) if total_weight > 0 else 0
    
    if overall_score >= 80:
        overall_status = "pass"
    elif overall_score >= 60:
        overall_status = "partial"
    else:
        overall_status = "fail"
    
    blocking_gates = [r["gate"] for r in results if r["status"] == "fail"]
    ready_for_spec = overall_score >= 70 and len(blocking_gates) == 0
    
    return {
        "overall_score": overall_score,
        "overall_status": overall_status,
        "gates": results,
        "ready_for_spec": ready_for_spec,
        "blocking_gates": blocking_gates
    }


def _generate_feedback(gate_id: str, met: list, missing: list, content: str) -> str:
    """Generate human-friendly feedback for a gate."""
    
    if not missing:
        return "Looking good! This gate is covered."
    
    feedback_templates = {
        "01_role_clarity": {
            "has_target_hirer": "Who specifically hires this? Give me a job title or company type.",
            "has_deliverable": "What does the hirer actually get? Be concrete.",
            "is_specific": "This is a bit vague. Can you be more specific about what the staff does?",
            "is_concise": "Try to say this in one sentence — under 30 words."
        },
        "02_output_standard": {
            "has_named_outputs": "Name your outputs. Like 'Weekly Digest' or 'Alert Email' — not just 'sends reports'.",
            "has_format": "What format? Email, PDF, Slack message, dashboard update?",
            "has_trigger": "What triggers this output? Is it scheduled or event-driven?",
            "has_frequency": "How often? Daily, weekly, real-time?"
        },
        "03_hirer_experience": {
            "has_onboarding_time": "How long does onboarding take? Give me a number — 10 minutes, 1 hour?",
            "has_intervention_points": "Where does the hirer need to step in? Review, approve, provide input?",
            "has_time_commitment": "How much of the hirer's time per week does this need?"
        },
        "04_failure_handling": {
            "has_scenarios": "Give me a failure scenario. What could go wrong?",
            "has_three_scenarios": "I need three scenarios. You've got some — what else could go sideways?",
            "has_responses": "What specifically does the staff do when this fails? Not 'handles it' — actual steps."
        },
        "05_calibration": {
            "has_feedback_mechanism": "How do you collect feedback from the hirer?",
            "has_improvement_logic": "How does that feedback make the staff better over time?",
            "has_calibration_questions": "What questions do you ask after each delivery?"
        }
    }
    
    templates = feedback_templates.get(gate_id, {})
    feedback_parts = [templates.get(m, f"Missing: {m}") for m in missing[:2]]  # Max 2 feedback items
    
    return " ".join(feedback_parts)
