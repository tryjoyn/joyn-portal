"""
agents/architect_agent.py — Joyn Builder Architect Agent

Takes a completed Creator Brief and generates the Visionary Spec —
a structured, machine-readable specification of the AI staff that
the builder uses to guide their actual build.

The Visionary Spec is the contract between the builder's intent and
The Bar's evaluation criteria. It is generated once, reviewed by the
builder, and then locked as the reference for the Reviewer Agent.

Architecture: Single-pass LLM call with structured output.
Triggered when: builder completes all Creator Brief questions and
calls /api/builder/brief (POST) with completed=True.

Outputs the full Visionary Spec as a JSON document stored in
builders.visionary_spec.
"""
from __future__ import annotations
import json
import logging
import os

logger = logging.getLogger(__name__)

try:
    from openai import OpenAI
    _client = OpenAI()
    _MODEL = os.environ.get("ARCHITECT_MODEL", "gpt-4.1-mini")
    _LLM_AVAILABLE = True
except ImportError:
    _LLM_AVAILABLE = False
    logger.warning("openai package not available — ArchitectAgent running in template mode")


SYSTEM_PROMPT = """You are the Joyn Architect Agent. Your job is to take a completed Creator Brief
from a domain expert and generate a Visionary Spec — a precise, structured specification for
their AI staff.

The Visionary Spec is the blueprint that:
1. Defines exactly what the AI staff does and does not do
2. Specifies every named output (format, trigger, frequency)
3. Defines the hirer experience (touchpoints, time required, intervention points)
4. Specifies failure handling for three common failure modes
5. Defines the calibration architecture (how the staff learns from feedback)
6. Identifies the moat asset (what makes this staff uniquely valuable over time)

The spec must be specific enough that a builder can implement it AND that a reviewer
can evaluate it against The Bar's five gates.

The Bar's five gates:
1. Role Clarity — one sentence, unambiguous, no jargon
2. Output Standard — every output named, formatted, triggered, and frequency defined
3. Hirer Experience — total hirer time, intervention points, touchpoints mapped
4. Failure Handling — three failure scenarios, each with defined response
5. Calibration Architecture — feedback mechanism, corpus structure, carry-forward logic

Return ONLY valid JSON with this exact structure:
{
  "staff_name": "<name of the AI staff>",
  "role_definition": "<one sentence, specific, no jargon>",
  "mode": "<autonomous or supervised>",
  "vertical": "<vertical>",
  "target_hirer": "<specific description of who hires this>",
  "core_pain": "<the specific problem this solves>",
  "agent_roster": [
    {
      "name": "<agent name>",
      "function": "<what it does>",
      "consumes": "<what input it takes>",
      "produces": "<what output it creates>",
      "handoff_condition": "<when it passes to the next agent>",
      "failure_behaviour": "<what it does when it fails>"
    }
  ],
  "named_outputs": [
    {
      "name": "<output name>",
      "format": "<Email/PDF/Slack/SMS/etc>",
      "trigger": "<what causes this output>",
      "frequency": "<how often>",
      "recipient": "<who receives it>"
    }
  ],
  "hirer_experience": {
    "total_time_minutes": <integer>,
    "intervention_points": [
      {"point": "<name>", "action_required": "<what hirer does>", "time_minutes": <integer>}
    ],
    "onboarding_steps": ["<step 1>", "<step 2>"]
  },
  "failure_handling": [
    {
      "scenario": "<failure scenario name>",
      "trigger": "<what causes this failure>",
      "response": "<how the staff handles it>",
      "hirer_notification": "<yes/no and how>"
    }
  ],
  "calibration_architecture": {
    "feedback_mechanism": "<how feedback is collected>",
    "corpus_structure": "<how the corpus is organised>",
    "carry_forward_logic": "<what is carried forward to future runs>",
    "calibration_questions": ["<question 1>", "<question 2>", "<question 3>"]
  },
  "moat_asset": "<what this staff builds over time that makes it uniquely valuable>",
  "build_complexity": "<simple/moderate/complex>",
  "estimated_weeks": "<e.g. 2-4>",
  "recommended_tools": ["<tool 1>", "<tool 2>"],
  "bar_readiness_notes": "<specific advice on what the builder must demonstrate to pass The Bar>"
}"""


def run(brief_data: dict, builder: dict) -> dict:
    """
    Generate the Visionary Spec from a completed Creator Brief.
    
    Parameters
    ----------
    brief_data : dict
        Completed Creator Brief answers
    builder : dict
        Builder record from the database
    
    Returns
    -------
    dict
        Visionary Spec JSON document
    """
    if _LLM_AVAILABLE:
        return _llm_spec(brief_data, builder)
    else:
        return _template_spec(brief_data, builder)


def _llm_spec(brief_data: dict, builder: dict) -> dict:
    """Use LLM to generate the Visionary Spec."""
    
    # Build the brief summary for the prompt
    brief_summary = _format_brief(brief_data, builder)
    
    prompt = f"""Generate the Visionary Spec for this AI staff build:

{brief_summary}

The builder is a domain expert — trust their knowledge of the domain.
Your job is to translate their intent into a precise, buildable specification
that will pass The Bar's five gates.

Be specific. Be concrete. Use the builder's own language where possible.
Do not invent capabilities — only specify what the builder described."""

    try:
        response = _client.chat.completions.create(
            model=_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=2000,
            response_format={"type": "json_object"}
        )
        spec = json.loads(response.choices[0].message.content)
        spec["_meta"] = {
            "agent": "architect",
            "model": _MODEL,
            "generated_from": "creator_brief",
            "builder_id": builder.get("id"),
        }
        return spec
    except Exception as e:
        logger.error(f"ArchitectAgent LLM error: {e}")
        return _template_spec(brief_data, builder)


def _format_brief(brief_data: dict, builder: dict) -> str:
    """Format the Creator Brief answers into a readable summary."""
    lines = [
        f"Builder: {builder.get('full_name', 'Unknown')}",
        f"Vertical: {builder.get('vertical', 'Unknown')}",
        f"Staff concept: {builder.get('staff_concept', 'Not provided')}",
        f"Track: {'Build from Brief (A)' if builder.get('track') == 'A' else 'Franchise Your Build (B)'}",
        "",
        "Creator Brief Answers:",
    ]
    
    # Map brief question keys to readable labels
    question_labels = {
        "q1_staff_name": "Staff name",
        "q2_role_definition": "Role definition (one sentence)",
        "q3_mode": "Mode (autonomous/supervised)",
        "q4_target_hirer": "Target hirer",
        "q5_core_pain": "Core pain solved",
        "q6_core_tasks": "Core tasks (what the staff does)",
        "q7_named_outputs": "Named outputs",
        "q8_hirer_touchpoints": "Hirer touchpoints and time",
        "q9_failure_scenarios": "Failure scenarios and handling",
        "q10_calibration": "Calibration and feedback mechanism",
        "q11_moat": "Moat asset (what makes this uniquely valuable over time)",
        "q12_tools": "Build tools",
        "q13_existing_build": "Existing build description (Track B only)",
        "q14_data_sources": "Key data sources",
        "q15_hardest_part": "Hardest part of the build",
    }
    
    for key, label in question_labels.items():
        if key in brief_data and brief_data[key]:
            lines.append(f"\n{label}:\n{brief_data[key]}")
    
    # Include any additional keys not in the label map
    for key, value in brief_data.items():
        if key not in question_labels and value:
            lines.append(f"\n{key}:\n{value}")
    
    return "\n".join(lines)


def _template_spec(brief_data: dict, builder: dict) -> dict:
    """Fallback template spec when LLM is unavailable."""
    staff_name = brief_data.get("q1_staff_name") or builder.get("claimed_role_name") or builder.get("staff_concept", "AI Staff")
    role_def = brief_data.get("q2_role_definition") or builder.get("staff_concept", "Performs specialised professional tasks autonomously.")
    mode = brief_data.get("q3_mode") or "autonomous"
    vertical = builder.get("vertical", "Operations")
    target_hirer = brief_data.get("q4_target_hirer") or "Businesses in this vertical"
    core_pain = brief_data.get("q5_core_pain") or "Manual, repetitive professional tasks consuming expert time"
    moat = brief_data.get("q11_moat") or "Domain-specific pattern intelligence built from every engagement"
    tools = brief_data.get("q12_tools") or ["Manus"]
    
    return {
        "staff_name": staff_name,
        "role_definition": role_def,
        "mode": mode,
        "vertical": vertical,
        "target_hirer": target_hirer,
        "core_pain": core_pain,
        "agent_roster": [
            {
                "name": "Intake Agent",
                "function": "Receives and validates incoming work",
                "consumes": "Hirer request or scheduled trigger",
                "produces": "Validated work package",
                "handoff_condition": "Validation passes",
                "failure_behaviour": "Returns error to hirer with specific reason"
            },
            {
                "name": "Processing Agent",
                "function": "Executes the core task",
                "consumes": "Validated work package",
                "produces": "Draft output",
                "handoff_condition": "Processing complete",
                "failure_behaviour": "Logs failure, notifies hirer, retries once"
            },
            {
                "name": "Output Agent",
                "function": "Formats and delivers the output",
                "consumes": "Draft output",
                "produces": "Final delivered output",
                "handoff_condition": "Delivery confirmed",
                "failure_behaviour": "Retries delivery, escalates after 3 failures"
            }
        ],
        "named_outputs": [
            {
                "name": "Primary Output",
                "format": "Email",
                "trigger": "Task completion",
                "frequency": "Per task",
                "recipient": "Hirer"
            }
        ],
        "hirer_experience": {
            "total_time_minutes": 30,
            "intervention_points": [
                {"point": "Onboarding", "action_required": "Provide context and preferences", "time_minutes": 20},
                {"point": "Review", "action_required": "Review output and provide feedback", "time_minutes": 10}
            ],
            "onboarding_steps": [
                "Complete the onboarding brief",
                "Review the first output",
                "Provide calibration feedback"
            ]
        },
        "failure_handling": [
            {
                "scenario": "Insufficient data",
                "trigger": "Required input data is missing or incomplete",
                "response": "Proceeds with available data, notes gaps in output",
                "hirer_notification": "Yes — included in output with specific gaps listed"
            },
            {
                "scenario": "Ambiguous input",
                "trigger": "Input is unclear or contradictory",
                "response": "Applies most conservative interpretation, flags ambiguity",
                "hirer_notification": "Yes — flags ambiguity and asks for clarification"
            },
            {
                "scenario": "Scope change mid-task",
                "trigger": "Hirer changes requirements after task has started",
                "response": "Completes current task with original scope, queues new task with updated scope",
                "hirer_notification": "Yes — confirms scope change received and queued"
            }
        ],
        "calibration_architecture": {
            "feedback_mechanism": "Post-output survey (3-4 questions) after each delivery",
            "corpus_structure": "Organised by engagement, stores hirer preferences and methodology notes",
            "carry_forward_logic": "Hirer preferences, domain context, and quality benchmarks carried forward",
            "calibration_questions": [
                "Was the output accurate and complete?",
                "Did the output meet your quality standard?",
                "What would you change about the output?"
            ]
        },
        "moat_asset": moat,
        "build_complexity": "moderate",
        "estimated_weeks": "2-4",
        "recommended_tools": tools if isinstance(tools, list) else [tools],
        "bar_readiness_notes": "Ensure you have at least one real output specimen from a test run before submitting to The Bar.",
        "_meta": {
            "agent": "architect",
            "model": "template",
            "generated_from": "creator_brief",
            "builder_id": builder.get("id"),
        }
    }
