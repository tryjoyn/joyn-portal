"""
agents/intake_agent.py — Joyn Builder Intake Agent

Validates and enriches a builder application. Called immediately after
/api/builder/apply to assess application quality and suggest the best
catalogue role match.

Architecture: Single-pass LLM call (no tool loop needed — deterministic
validation + one enrichment pass). Uses OpenAI-compatible API.

Outputs:
  - quality_score: 0-100 (how specific and credible the application is)
  - suggested_role_id: best matching catalogue role (or None)
  - suggested_role_name: human-readable name
  - vertical_match: True/False
  - feedback: 1-2 sentences for the builder (positive framing)
  - flags: list of issues to surface in the dashboard
  - track_recommendation: 'A' (build from brief) or 'B' (franchise your build)
"""
from __future__ import annotations
import json
import logging
import os
import sqlite3
from typing import Optional

logger = logging.getLogger(__name__)

# Use OpenAI-compatible endpoint (supports gpt-4.1-mini, gemini-2.5-flash)
try:
    from openai import OpenAI
    _client = OpenAI()
    _MODEL = os.environ.get("INTAKE_MODEL", "gpt-4.1-mini")
    _LLM_AVAILABLE = True
except ImportError:
    _LLM_AVAILABLE = False
    logger.warning("openai package not available — IntakeAgent running in rule-based mode")


SYSTEM_PROMPT = """You are the Joyn Intake Agent. Your job is to evaluate a builder application
for the Joyn AI Staff Marketplace and return a structured JSON assessment.

Joyn is a marketplace where domain experts build AI staff — autonomous or supervised AI workers
that businesses hire to do specific professional jobs. The builder is the domain expert who
creates and maintains the AI staff. The hirer is the business that pays to use it.

Evaluate the application against these criteria:
1. SPECIFICITY: Is the staff concept specific enough to be a real job? "AI assistant" fails. 
   "Insurance renewal specialist for Florida P&C carriers" passes.
2. DOMAIN CREDIBILITY: Does the builder's background match the vertical they're building for?
3. MANUAL TASK CLARITY: Is the manual task being replaced clearly described?
4. CATALOGUE FIT: Does this match an open role in the catalogue, or is it genuinely novel?
5. TRACK FIT: Track A = building from scratch. Track B = franchising something already built.

Return ONLY valid JSON with this exact structure:
{
  "quality_score": <integer 0-100>,
  "suggested_role_id": <string or null>,
  "suggested_role_name": <string or null>,
  "vertical_match": <boolean>,
  "feedback": "<1-2 sentences, positive framing, addressed to the builder>",
  "flags": [<list of strings — issues to surface, empty if none>],
  "track_recommendation": "<A or B>",
  "track_reasoning": "<one sentence explaining the track recommendation>"
}"""


def run(application: dict, db_path: str = "joyn_builders.db") -> dict:
    """
    Evaluate a builder application.
    
    Parameters
    ----------
    application : dict
        Builder application data from /api/builder/apply
    db_path : str
        Path to the SQLite database
    
    Returns
    -------
    dict
        Structured assessment result
    """
    # Load relevant catalogue roles for context
    catalogue_context = _load_catalogue_context(application.get('vertical'), db_path)
    
    if _LLM_AVAILABLE:
        return _llm_assessment(application, catalogue_context)
    else:
        return _rule_based_assessment(application, catalogue_context)


def _load_catalogue_context(vertical: Optional[str], db_path: str) -> list:
    """Load up to 10 catalogue roles from the builder's vertical for matching."""
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        if vertical:
            rows = conn.execute(
                "SELECT id, name, role, mode, hirer, pain FROM catalogue WHERE vertical=? AND status='open' LIMIT 10",
                (vertical,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, name, role, mode, hirer, pain FROM catalogue WHERE status='open' LIMIT 10"
            ).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        logger.warning(f"IntakeAgent: could not load catalogue context: {e}")
        return []


def _llm_assessment(application: dict, catalogue_context: list) -> dict:
    """Use LLM to assess the application."""
    prompt = f"""Builder Application:
- Name: {application.get('full_name', 'Unknown')}
- Current role: {application.get('current_role', 'Not provided')}
- Domain/company: {application.get('domain', 'Not provided')}
- Years experience: {application.get('years_experience', 'Not provided')}
- Vertical: {application.get('vertical', 'Not provided')}
- Staff concept: {application.get('staff_concept', 'Not provided')}
- Manual task being replaced: {application.get('manual_task_replaced', 'Not provided')}
- Build tools comfortable with: {application.get('build_tools', 'Not provided')}
- Track preference: {application.get('track', 'A')}

Open catalogue roles in this vertical (for matching):
{json.dumps(catalogue_context, indent=2) if catalogue_context else 'No roles loaded'}

Assess this application and return the JSON assessment."""

    try:
        response = _client.chat.completions.create(
            model=_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=600,
            response_format={"type": "json_object"}
        )
        result = json.loads(response.choices[0].message.content)
        # Ensure required fields exist
        return {
            "quality_score": int(result.get("quality_score", 50)),
            "suggested_role_id": result.get("suggested_role_id"),
            "suggested_role_name": result.get("suggested_role_name"),
            "vertical_match": bool(result.get("vertical_match", True)),
            "feedback": str(result.get("feedback", "Your application has been received.")),
            "flags": list(result.get("flags", [])),
            "track_recommendation": str(result.get("track_recommendation", "A")),
            "track_reasoning": str(result.get("track_reasoning", "")),
            "agent": "intake",
            "model": _MODEL,
        }
    except Exception as e:
        logger.error(f"IntakeAgent LLM error: {e}")
        return _rule_based_assessment(application, catalogue_context)


def _rule_based_assessment(application: dict, catalogue_context: list) -> dict:
    """Fallback rule-based assessment when LLM is unavailable."""
    concept = application.get('staff_concept', '')
    manual_task = application.get('manual_task_replaced', '')
    vertical = application.get('vertical', '')
    
    score = 50
    flags = []
    
    # Specificity check
    if len(concept) > 50:
        score += 15
    elif len(concept) < 20:
        score -= 20
        flags.append("Staff concept is too vague — describe the specific job this AI staff will do")
    
    # Manual task check
    if len(manual_task) > 30:
        score += 10
    else:
        flags.append("Manual task description is brief — more detail helps calibrate the build")
    
    # Vertical check
    if vertical:
        score += 10
    
    # Track recommendation
    track = application.get('track', 'A')
    track_reasoning = "Building from a brief is the standard path for new builders."
    if track == 'B':
        track_reasoning = "You indicated you have an existing build to franchise — Track B is the right path."
    
    # Catalogue match (simple name matching)
    suggested_role_id = None
    suggested_role_name = None
    for role in catalogue_context:
        role_words = set(role.get('role', '').lower().split())
        concept_words = set(concept.lower().split())
        if len(role_words & concept_words) >= 2:
            suggested_role_id = role['id']
            suggested_role_name = role['name']
            score += 5
            break
    
    score = max(0, min(100, score))
    
    return {
        "quality_score": score,
        "suggested_role_id": suggested_role_id,
        "suggested_role_name": suggested_role_name,
        "vertical_match": bool(vertical),
        "feedback": "Your application has been received. Your builder dashboard will guide you through each stage.",
        "flags": flags,
        "track_recommendation": track,
        "track_reasoning": track_reasoning,
        "agent": "intake",
        "model": "rule-based",
    }
