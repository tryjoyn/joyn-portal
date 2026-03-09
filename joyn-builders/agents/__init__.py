"""
Joyn Builder Agent System

Four agents, each with a defined role in the builder journey:

1. IntakeAgent    — validates and enriches builder applications
2. ArchitectAgent — generates the Visionary Spec from the Creator Brief
3. ReviewerAgent  — evaluates submissions against The Bar's five gates
4. DeploymentAgent — generates the marketplace listing HTML page

All agents are designed for graceful degradation:
- If the LLM is unavailable, they fall back to rule-based or template logic
- No agent ever fails silently — errors are logged and surfaced to the caller
- All agents are stateless — they receive inputs and return outputs, no side effects
"""
from .intake_agent import run as intake
from .architect_agent import run as architect
from .reviewer_agent import run as reviewer
from .deployment_agent import run as deployment

__all__ = ['intake', 'architect', 'reviewer', 'deployment']
