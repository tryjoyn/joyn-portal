"""
iris-agent/test_supervisor.py
──────────────────────────────
Integration test for the SupervisorAgent and tool registry.

Tests:
  1. All 4 tools are callable with valid inputs.
  2. assess_regulatory_impact returns a valid priority.
  3. route_action handles all three priority levels.
  4. Full supervisor loop processes a bulletin end-to-end.

Run:
  python test_supervisor.py

Exit codes:
  0 — all tests passed
  1 — one or more tests failed
"""

from __future__ import annotations

import json
import os
import sys
import traceback
from unittest.mock import MagicMock, patch

# ── Test fixtures ──────────────────────────────────────────────────────────────

SAMPLE_BULLETIN = {
    "id": "test-fl-001",
    "title": "Florida OIR Bulletin 2025-01: Homeowners Rate Filing Requirements",
    "state": "FL",
    "source": "Florida OIR",
    "published_at": "2025-01-15",
    "content": (
        "The Florida Office of Insurance Regulation hereby issues guidance on updated "
        "homeowners insurance rate filing requirements effective March 1, 2025. All "
        "insurers writing homeowners coverage in Florida must submit revised rate filings "
        "demonstrating compliance with the new actuarial standards by February 15, 2025. "
        "Failure to comply may result in suspension of writing authority."
    ),
    "url": "https://www.floir.com/bulletins/2025-01"
}

SAMPLE_CLIENT_PROFILE = {
    "client_id": 42,
    "company_name": "Test Insurance Co.",
    "jurisdictions": ["FL", "TX", "CA"],
    "lines_of_business": ["P&C", "Life"],
    "alert_frequency": "immediate",
    "iris_settings": {"alert_email": "test@example.com", "status": "active"}
}

# ── Test helpers ───────────────────────────────────────────────────────────────

PASS = "\033[92m✓ PASS\033[0m"
FAIL = "\033[91m✗ FAIL\033[0m"
results = []


def run_test(name: str, fn):
    """Run a single test function and record the result."""
    try:
        fn()
        print(f"  {PASS}  {name}")
        results.append((name, True, None))
    except Exception as exc:
        print(f"  {FAIL}  {name}")
        print(f"         {exc}")
        traceback.print_exc()
        results.append((name, False, str(exc)))


# ── Individual tests ───────────────────────────────────────────────────────────

def test_fetch_client_profile_mock():
    """fetch_client_profile returns a valid profile when JOYN_PORTAL_URL is unset."""
    from agents.tools import fetch_client_profile
    os.environ.pop("JOYN_PORTAL_URL", None)
    profile = fetch_client_profile(client_id=42)
    assert isinstance(profile, dict), "Expected dict"
    assert profile.get("client_id") == 42, f"Expected client_id=42, got {profile.get('client_id')}"
    assert "jurisdictions" in profile, "Missing 'jurisdictions' key"
    assert "_mock" in profile, "Expected _mock flag in dev response"


def test_assess_regulatory_impact_jurisdiction_filter():
    """assess_regulatory_impact fast-paths to MONITOR for out-of-jurisdiction bulletins."""
    from agents.tools import assess_regulatory_impact
    out_of_state_bulletin = dict(SAMPLE_BULLETIN, state="NY")
    result = assess_regulatory_impact(
        client_id=42,
        bulletin=out_of_state_bulletin,
        client_jurisdictions=["FL", "TX"],
        anthropic_client=None,  # Should not be called
    )
    assert result["priority"] == "MONITOR", f"Expected MONITOR, got {result['priority']}"
    assert result.get("jurisdiction_filtered") is True, "Expected jurisdiction_filtered=True"


def test_assess_regulatory_impact_with_mock_claude():
    """assess_regulatory_impact calls Claude and parses a valid JSON response."""
    from agents.tools import assess_regulatory_impact

    mock_response_content = json.dumps({
        "priority": "IMMEDIATE",
        "impact_summary": "Rate filing deadline requires immediate action.",
        "recommended_actions": ["Submit revised rate filing by Feb 15"],
        "affected_lines_of_business": ["P&C"],
        "compliance_deadline": "2025-02-15",
        "confidence": 0.95
    })

    mock_message = MagicMock()
    mock_message.content = [MagicMock(text=mock_response_content)]
    mock_message.usage = MagicMock(
        input_tokens=500,
        output_tokens=100,
        cache_read_input_tokens=0,
        cache_creation_input_tokens=0,
    )

    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_message

    result = assess_regulatory_impact(
        client_id=42,
        bulletin=SAMPLE_BULLETIN,
        client_jurisdictions=["FL", "TX"],
        client_lines_of_business=["P&C"],
        anthropic_client=mock_client,
        model="claude-sonnet-4-5",
    )

    assert result["priority"] in ("IMMEDIATE", "DIGEST", "MONITOR"), \
        f"Invalid priority: {result['priority']}"
    assert "impact_summary" in result, "Missing impact_summary"
    assert isinstance(result.get("recommended_actions"), list), \
        "recommended_actions should be a list"


def test_route_action_monitor():
    """route_action handles MONITOR priority without portal calls."""
    from agents.tools import route_action
    os.environ.pop("JOYN_PORTAL_URL", None)
    result = route_action(
        client_id=42,
        priority="MONITOR",
        bulletin_title="Test Bulletin",
        impact_summary="Low impact informational bulletin.",
    )
    assert isinstance(result, dict), "Expected dict result"
    assert result.get("priority") == "MONITOR"


def test_route_action_immediate_no_portal():
    """route_action handles IMMEDIATE priority gracefully when portal is not configured."""
    from agents.tools import route_action
    os.environ.pop("JOYN_PORTAL_URL", None)
    result = route_action(
        client_id=42,
        priority="IMMEDIATE",
        bulletin_title="Urgent: Rate Filing Deadline",
        impact_summary="Compliance deadline in 30 days.",
        recommended_actions=["Submit rate filing immediately"],
        bulletin_url="https://www.floir.com/bulletins/2025-01",
    )
    assert isinstance(result, dict)
    assert result.get("priority") == "IMMEDIATE"


def test_log_activity_no_portal():
    """log_activity handles missing portal URL gracefully."""
    from agents.tools import log_activity
    os.environ.pop("JOYN_PORTAL_URL", None)
    result = log_activity(
        client_id=42,
        action_type="analysis",
        action_description="Processed 3 bulletins.",
        status="complete",
    )
    assert isinstance(result, dict)
    assert result.get("client_id") == 42


def test_supervisor_full_loop_mock():
    """SupervisorAgent processes a bulletin end-to-end with mocked Claude responses."""
    from agents.supervisor import SupervisorAgent

    # The supervisor uses ONE shared Anthropic client for both:
    #   a) The coordinator loop (tool_use blocks → end_turn)
    #   b) The assess_regulatory_impact tool's internal LLM call
    #
    # Call sequence on the shared client:
    #   Call 0: supervisor asks Claude → Claude returns fetch_client_profile tool_use
    #   Call 1: supervisor asks Claude → Claude returns assess_regulatory_impact tool_use
    #   Call 2: assess_regulatory_impact calls Claude internally → returns JSON assessment
    #   Call 3: supervisor asks Claude → Claude returns route_action tool_use
    #   Call 4: supervisor asks Claude → Claude returns log_activity tool_use
    #   Call 5: supervisor asks Claude → Claude returns end_turn + summary text

    assessment_json = json.dumps({
        "priority": "IMMEDIATE",
        "impact_summary": "Rate filing deadline requires immediate action.",
        "recommended_actions": ["Submit revised rate filing by Feb 15"],
        "affected_lines_of_business": ["P&C"],
        "compliance_deadline": "2025-02-15",
        "confidence": 0.95
    })

    # Ordered list of responses the shared client will return
    supervisor_tool_calls = [
        ("fetch_client_profile",     {"client_id": 42}),
        ("assess_regulatory_impact", {
            "client_id": 42,
            "bulletin": SAMPLE_BULLETIN,
            "client_jurisdictions": ["FL", "TX"],
        }),
        ("route_action", {
            "client_id": 42,
            "priority": "IMMEDIATE",
            "bulletin_title": SAMPLE_BULLETIN["title"],
            "impact_summary": "Rate filing deadline requires immediate action.",
        }),
        ("log_activity", {
            "client_id": 42,
            "action_type": "analysis",
            "action_description": "Processed 1 bulletin: 1 IMMEDIATE.",
            "status": "complete",
        }),
    ]

    call_index = [0]  # tracks calls to the shared client

    def make_tool_block(tool_name, tool_input, idx):
        block = MagicMock()
        block.type = "tool_use"
        block.name = tool_name
        block.input = dict(tool_input)  # plain dict — json.dumps-safe
        block.id = f"tool_{idx}"
        return block

    def make_usage():
        return MagicMock(
            input_tokens=300, output_tokens=80,
            cache_read_input_tokens=0, cache_creation_input_tokens=0
        )

    def mock_create(**kwargs):
        """Returns scripted responses in order for all calls on the shared client."""
        idx = call_index[0]
        call_index[0] += 1

        mock_resp = MagicMock()
        mock_resp.usage = make_usage()

        # Call 0 → fetch_client_profile
        if idx == 0:
            mock_resp.stop_reason = "tool_use"
            mock_resp.content = [make_tool_block(*supervisor_tool_calls[0], idx)]

        # Call 1 → assess_regulatory_impact
        elif idx == 1:
            mock_resp.stop_reason = "tool_use"
            mock_resp.content = [make_tool_block(*supervisor_tool_calls[1], idx)]

        # Call 2 → assess_regulatory_impact's INTERNAL LLM call (returns JSON, not tool_use)
        elif idx == 2:
            mock_resp.stop_reason = "end_turn"
            text_block = MagicMock()
            text_block.type = "text"
            text_block.text = assessment_json
            mock_resp.content = [text_block]

        # Call 3 → route_action
        elif idx == 3:
            mock_resp.stop_reason = "tool_use"
            mock_resp.content = [make_tool_block(*supervisor_tool_calls[2], idx)]

        # Call 4 → log_activity
        elif idx == 4:
            mock_resp.stop_reason = "tool_use"
            mock_resp.content = [make_tool_block(*supervisor_tool_calls[3], idx)]

        # Call 5 → final end_turn summary
        else:
            mock_resp.stop_reason = "end_turn"
            text_block = MagicMock()
            text_block.type = "text"
            text_block.text = "Processed 1 bulletin: 1 IMMEDIATE."
            mock_resp.content = [text_block]

        return mock_resp

    shared_client = MagicMock()
    shared_client.messages.create.side_effect = mock_create

    supervisor = SupervisorAgent(model="claude-sonnet-4-5")
    supervisor._client = shared_client

    # Patch anthropic.Anthropic so assess_regulatory_impact (which calls
    # anthropic.Anthropic() when anthropic_client is provided as self._client)
    # uses the same shared_client — no separate patching needed since
    # dispatch_tool passes anthropic_client=self._client directly.
    job = {"client_id": 42, "bulletins": [SAMPLE_BULLETIN]}
    result = supervisor.run(job)

    assert result["status"] == "success", f"Expected success, got: {result}"
    assert result["tool_calls"] == len(supervisor_tool_calls), \
        f"Expected {len(supervisor_tool_calls)} tool calls, got {result['tool_calls']}"
    assert "IMMEDIATE" in result["summary"] or result["summary"], \
        "Expected non-empty summary"

    print(f"         tool_calls={result['tool_calls']} summary={result['summary'][:80]}")


def test_tool_schemas_valid():
    """All 4 tool schemas are present and have required fields."""
    from agents.tools import TOOL_SCHEMAS
    assert len(TOOL_SCHEMAS) == 4, f"Expected 4 tools, got {len(TOOL_SCHEMAS)}"
    required_tool_names = {
        "fetch_client_profile",
        "assess_regulatory_impact",
        "route_action",
        "log_activity",
    }
    actual_names = {t["name"] for t in TOOL_SCHEMAS}
    assert actual_names == required_tool_names, \
        f"Tool name mismatch: {actual_names ^ required_tool_names}"
    for tool in TOOL_SCHEMAS:
        assert "description" in tool, f"Tool {tool['name']} missing description"
        assert "input_schema" in tool, f"Tool {tool['name']} missing input_schema"


# ── Test runner ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\nIris Agent — Phase 2 Integration Tests")
    print("=" * 50)

    # Ensure we can import from the iris-agent directory
    sys.path.insert(0, os.path.dirname(__file__))

    run_test("fetch_client_profile returns mock when portal not configured", test_fetch_client_profile_mock)
    run_test("assess_regulatory_impact filters out-of-jurisdiction bulletins", test_assess_regulatory_impact_jurisdiction_filter)
    run_test("assess_regulatory_impact calls Claude and parses response", test_assess_regulatory_impact_with_mock_claude)
    run_test("route_action handles MONITOR priority", test_route_action_monitor)
    run_test("route_action handles IMMEDIATE without portal", test_route_action_immediate_no_portal)
    run_test("log_activity handles missing portal URL", test_log_activity_no_portal)
    run_test("SupervisorAgent full loop (4 tool calls + summary)", test_supervisor_full_loop_mock)
    run_test("All 4 tool schemas are valid", test_tool_schemas_valid)

    print("\n" + "=" * 50)
    passed = sum(1 for _, ok, _ in results if ok)
    total  = len(results)
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("\n\033[92mALL TESTS PASSED\033[0m")
        sys.exit(0)
    else:
        failed = [(n, e) for n, ok, e in results if not ok]
        print(f"\n\033[91m{len(failed)} TEST(S) FAILED:\033[0m")
        for name, err in failed:
            print(f"  • {name}: {err}")
        sys.exit(1)
