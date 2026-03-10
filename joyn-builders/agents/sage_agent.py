"""
agents/sage_agent.py — Sage Conversational Agent

Handles the conversational brief collection flow. Sage guides builders
through defining their AI staff while scoring quality in real-time.

Architecture:
- Stateful conversations stored in sage_sessions table
- Real-time gate scoring after each turn
- Streaming responses via SSE
- Fallback options when builder is stuck
"""
from __future__ import annotations
import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Generator, Optional

logger = logging.getLogger(__name__)

# Fix imports for when loaded via importlib
import sys
_agent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _agent_dir not in sys.path:
    sys.path.insert(0, _agent_dir)

# Import prompts
from prompts.sage_v1 import (
    SAGE_SYSTEM_PROMPT,
    SAGE_OPENER,
    SAGE_GATE_PROMPTS,
    SAGE_FALLBACK_REVERSE_ENGINEER,
    SAGE_FALLBACK_QUICK_CHOICES,
    SAGE_COMPLETION_SUMMARY
)

# Import shared gate scoring
from shared.gate_scoring import score_all_gates, score_gate

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# OpenAI setup
_client = None
_LLM_AVAILABLE = False
_MODEL = os.environ.get("SAGE_MODEL", "gpt-4o-mini")  # gpt-4o-mini is the correct name

try:
    from openai import OpenAI
    api_key = os.environ.get("OPENAI_API_KEY")
    logger.info(f"OPENAI_API_KEY present: {bool(api_key)}, length: {len(api_key) if api_key else 0}")
    if api_key:
        _client = OpenAI(api_key=api_key)
        _LLM_AVAILABLE = True
        logger.info(f"Sage LLM initialized successfully with model: {_MODEL}")
        
        # Test the API connection
        try:
            test_response = _client.chat.completions.create(
                model=_MODEL,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5
            )
            logger.info(f"OpenAI API test successful")
        except Exception as test_err:
            logger.error(f"OpenAI API test failed: {test_err}")
            _LLM_AVAILABLE = False
    else:
        logger.warning("OPENAI_API_KEY not set — Sage running in fallback mode")
except ImportError:
    logger.warning("openai package not available — Sage running in fallback mode")
except Exception as e:
    logger.warning(f"OpenAI setup failed: {e} — Sage running in fallback mode")

# Whisper setup for voice
_WHISPER_MODEL = "whisper-1"
_VOICE_AVAILABLE = _LLM_AVAILABLE  # Uses same OpenAI client


class SageSession:
    """Represents a Sage conversation session."""
    
    def __init__(self, session_id: str, builder_id: str):
        self.session_id = session_id
        self.builder_id = builder_id
        self.messages = []  # Full conversation history
        self.collected_data = {
            "role_clarity": "",
            "output_standard": "",
            "hirer_experience": "",
            "failure_handling": "",
            "calibration": "",
            "staff_name": "",
            "mode": ""
        }
        self.current_gate = "role_clarity"
        self.gate_attempts = {}  # Track attempts per gate for fallback trigger
        self.gate_scores = {}
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.updated_at = self.created_at
        self.status = "active"  # active | completed | abandoned
    
    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "builder_id": self.builder_id,
            "messages": self.messages,
            "collected_data": self.collected_data,
            "current_gate": self.current_gate,
            "gate_attempts": self.gate_attempts,
            "gate_scores": self.gate_scores,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "status": self.status
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'SageSession':
        session = cls(data["session_id"], data["builder_id"])
        session.messages = data.get("messages", [])
        session.collected_data = data.get("collected_data", session.collected_data)
        session.current_gate = data.get("current_gate", "role_clarity")
        session.gate_attempts = data.get("gate_attempts", {})
        session.gate_scores = data.get("gate_scores", {})
        session.created_at = data.get("created_at", session.created_at)
        session.updated_at = data.get("updated_at", session.updated_at)
        session.status = data.get("status", "active")
        return session


def create_session(builder_id: str) -> SageSession:
    """Create a new Sage conversation session."""
    session_id = str(uuid.uuid4())
    session = SageSession(session_id, builder_id)
    
    # Add Sage's opener
    session.messages.append({
        "role": "assistant",
        "content": SAGE_OPENER,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    return session


def process_message(session: SageSession, user_message: str) -> Generator[str, None, None]:
    """
    Process a user message and generate Sage's response.
    Yields chunks for streaming.
    
    Args:
        session: Current SageSession
        user_message: Builder's message
    
    Yields:
        Response chunks for SSE streaming
    """
    if not _LLM_AVAILABLE:
        yield _fallback_response(session, user_message)
        return
    
    # Add user message to history
    session.messages.append({
        "role": "user",
        "content": user_message,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    # Update collected data based on current gate
    _update_collected_data(session, user_message)
    
    # Score current gate
    current_gate_id = f"0{list(session.collected_data.keys()).index(session.current_gate) + 1}_{session.current_gate}"
    gate_score = score_gate(current_gate_id, session.collected_data.get(session.current_gate, ""))
    session.gate_scores[session.current_gate] = gate_score
    
    # Track attempts for fallback
    session.gate_attempts[session.current_gate] = session.gate_attempts.get(session.current_gate, 0) + 1
    
    # Check if we should offer fallback
    should_fallback = session.gate_attempts.get(session.current_gate, 0) >= 3 and gate_score["status"] != "pass"
    
    # Build messages for LLM
    llm_messages = _build_llm_messages(session, gate_score, should_fallback)
    
    try:
        # Stream response from LLM
        response_content = ""
        logger.info(f"Calling LLM with model: {_MODEL}, LLM_AVAILABLE: {_LLM_AVAILABLE}")
        stream = _client.chat.completions.create(
            model=_MODEL,
            messages=llm_messages,
            temperature=0.7,
            max_tokens=300,
            stream=True
        )
        
        for chunk in stream:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                response_content += content
                yield content
        
        # Add assistant response to history
        session.messages.append({
            "role": "assistant",
            "content": response_content,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        # Check if gate passed and move to next
        if gate_score["status"] == "pass":
            _advance_gate(session)
        
        session.updated_at = datetime.now(timezone.utc).isoformat()
        
    except Exception as e:
        logger.error(f"Sage LLM error: {type(e).__name__}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        yield "I hit a snag — let me try that again. Could you rephrase what you just said?"


def process_voice(session: SageSession, audio_data: bytes) -> tuple[str, Generator[str, None, None]]:
    """
    Transcribe voice input and process as message.
    
    Args:
        session: Current SageSession
        audio_data: Raw audio bytes
    
    Returns:
        Tuple of (transcribed_text, response_generator)
    """
    if not _VOICE_AVAILABLE:
        return "", iter(["Voice input isn't available right now. Please type your response."])
    
    try:
        # Transcribe with Whisper
        transcript = _client.audio.transcriptions.create(
            model=_WHISPER_MODEL,
            file=("audio.webm", audio_data, "audio/webm"),
            response_format="text"
        )
        
        transcribed_text = transcript.strip()
        
        # Process as regular message
        response_gen = process_message(session, transcribed_text)
        
        return transcribed_text, response_gen
        
    except Exception as e:
        logger.error(f"Whisper transcription error: {e}")
        return "", iter(["I couldn't catch that. Could you try again or type your response?"])


def get_session_status(session: SageSession) -> dict:
    """Get current session status including gate scores."""
    overall = score_all_gates(session.collected_data)
    
    return {
        "session_id": session.session_id,
        "builder_id": session.builder_id,
        "status": session.status,
        "current_gate": session.current_gate,
        "overall_score": overall["overall_score"],
        "ready_for_spec": overall["ready_for_spec"],
        "gates": overall["gates"],
        "blocking_gates": overall["blocking_gates"],
        "message_count": len(session.messages),
        "created_at": session.created_at,
        "updated_at": session.updated_at
    }


def finalize_session(session: SageSession) -> dict:
    """
    Finalize session and prepare data for brief submission.
    Called when all gates pass.
    
    Returns:
        Structured data ready for /api/builder/brief
    """
    session.status = "completed"
    session.updated_at = datetime.now(timezone.utc).isoformat()
    
    # Map collected data to brief format
    answers = {
        "q1_staff_name": session.collected_data.get("staff_name", ""),
        "q2_role_definition": session.collected_data.get("role_clarity", ""),
        "q3_mode": session.collected_data.get("mode", "autonomous"),
        "q4_target_hirer": _extract_hirer(session.collected_data.get("role_clarity", "")),
        "q5_core_pain": _extract_pain(session.messages),
        "q6_core_tasks": "",
        "q7_named_outputs": session.collected_data.get("output_standard", ""),
        "q8_hirer_touchpoints": session.collected_data.get("hirer_experience", ""),
        "q9_failure_scenarios": session.collected_data.get("failure_handling", ""),
        "q10_calibration": session.collected_data.get("calibration", ""),
        "q11_moat": "",
        "q12_tools": ""
    }
    
    return {
        "builder_id": session.builder_id,
        "answers": answers,
        "completed": True,
        "sage_session_id": session.session_id,
        "conversation_turns": len(session.messages)
    }


def _build_llm_messages(session: SageSession, gate_score: dict, should_fallback: bool) -> list:
    """Build message list for LLM including context."""
    
    messages = [{"role": "system", "content": SAGE_SYSTEM_PROMPT}]
    
    # Add gate context
    gate_context = f"""
CURRENT CONTEXT:
- Current gate: {session.current_gate} ({gate_score['name']})
- Gate status: {gate_score['status']} ({gate_score['score']}%)
- Missing: {', '.join(gate_score.get('missing_criteria', []))}
- Attempts on this gate: {session.gate_attempts.get(session.current_gate, 0)}
"""
    
    if should_fallback:
        gate_context += f"""
FALLBACK TRIGGERED: Builder has attempted this gate 3+ times without passing.
Offer an alternative approach. Either:
1. Reverse engineer: "{SAGE_FALLBACK_REVERSE_ENGINEER[:100]}..."
2. Quick choices: Offer simple A/B options

Be encouraging, not frustrated."""
    
    messages.append({"role": "system", "content": gate_context})
    
    # Add conversation history (last 10 messages to manage tokens)
    for msg in session.messages[-10:]:
        messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })
    
    return messages


def _update_collected_data(session: SageSession, user_message: str):
    """Update collected data based on current gate and user message."""
    
    # Append to current gate's data
    current = session.collected_data.get(session.current_gate, "")
    if current:
        session.collected_data[session.current_gate] = f"{current}\n{user_message}"
    else:
        session.collected_data[session.current_gate] = user_message
    
    # Try to extract staff name if mentioned
    if not session.collected_data.get("staff_name"):
        # Look for "called X" or "named X" patterns
        import re
        name_match = re.search(r'(?:called|named|name is|it\'s)\s+([A-Z][a-z]+)', user_message)
        if name_match:
            session.collected_data["staff_name"] = name_match.group(1)
    
    # Try to extract mode if mentioned
    if not session.collected_data.get("mode"):
        if "autonomous" in user_message.lower() or "on its own" in user_message.lower():
            session.collected_data["mode"] = "autonomous"
        elif "supervised" in user_message.lower() or "approval" in user_message.lower():
            session.collected_data["mode"] = "supervised"


def _advance_gate(session: SageSession):
    """Move to the next gate in sequence."""
    gate_order = ["role_clarity", "output_standard", "hirer_experience", "failure_handling", "calibration"]
    
    current_idx = gate_order.index(session.current_gate) if session.current_gate in gate_order else 0
    
    if current_idx < len(gate_order) - 1:
        session.current_gate = gate_order[current_idx + 1]
        session.gate_attempts[session.current_gate] = 0  # Reset attempts for new gate


def _extract_hirer(role_text: str) -> str:
    """Extract target hirer from role clarity text."""
    # Simple extraction - could be improved with NLP
    import re
    hirer_patterns = [
        r'(?:for|helps?|serves?)\s+([^.]+(?:broker|agent|manager|owner|director|firm|practice|business)[^.]*)',
        r'([^.]*(?:broker|agent|manager|owner|director)[^.]*)\s+(?:who|that|need)',
    ]
    
    for pattern in hirer_patterns:
        match = re.search(pattern, role_text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    return ""


def _extract_pain(messages: list) -> str:
    """Extract core pain from conversation messages."""
    # Look for early messages that likely describe the problem
    for msg in messages[:5]:
        if msg["role"] == "user" and len(msg["content"]) > 50:
            return msg["content"][:500]
    return ""


def _fallback_response(session: SageSession, user_message: str) -> str:
    """Generate fallback response when LLM is unavailable."""
    return """I'm having trouble connecting right now. 

In the meantime, you can use the classic Creator Brief form — it asks the same questions, just in a different format.

[Switch to Classic Form →]"""
