"""
Claude Autonomous Build Script
Reads VISION.md + current site, builds files, posts results to GitHub issue.
"""

import os
import json
import anthropic
import subprocess
import urllib.request
import urllib.parse

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
BUILD_INSTRUCTION = os.environ.get("BUILD_INSTRUCTION", "")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
REPO = os.environ.get("REPO", "")
ISSUE_NUMBER_RAW = os.environ.get("ISSUE_NUMBER", "")

# Extract numeric issue number
ISSUE_NUMBER = ""
for part in ISSUE_NUMBER_RAW.split("/"):
    if part.isdigit():
        ISSUE_NUMBER = part

def read_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return f"[File not found: {path}]"

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True) if "/" in path else None
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def post_github_comment(body):
    if not GITHUB_TOKEN or not REPO or not ISSUE_NUMBER:
        print("Cannot post comment — missing GitHub env vars")
        return
    url = f"https://api.github.com/repos/{REPO}/issues/{ISSUE_NUMBER}/comments"
    data = json.dumps({"body": body}).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Authorization", f"token {GITHUB_TOKEN}")
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/vnd.github+json")
    try:
        urllib.request.urlopen(req)
    except Exception as e:
        print(f"Failed to post comment: {e}")

def get_site_context():
    """Read current site files for context."""
    files = {}
    to_read = [
        "index.html",
        "marketplace/index.html",
        "marketplace/iris-insurance-regulatory.html",
        "practice/tdd-practice-team.html",
        "VISION.md",
    ]
    for path in to_read:
        content = read_file(path)
        if not content.startswith("[File not found"):
            # Truncate large files
            if len(content) > 8000:
                content = content[:8000] + "\n... [truncated]"
            files[path] = content
    return files

def main():
    print(f"Build instruction: {BUILD_INSTRUCTION}")

    vision = read_file("VISION.md")
    site_files = get_site_context()

    site_context = "\n\n".join([
        f"=== {path} ===\n{content}"
        for path, content in site_files.items()
        if path != "VISION.md"
    ])

    system_prompt = f"""You are Joyn's autonomous build partner. You build and update the Joyn website at tryjoyn.me.

VISION DOCUMENT (read before every build):
{vision}

RULES:
- Every page is a single self-contained HTML file. All CSS and JS inline. No frameworks.
- Fonts: Cormorant Garamond (headings), DM Mono (labels), Syne (body) — from Google Fonts CDN only
- Colours: --paper:#f5f1e8 --ink:#0d0c0a --gold:#b8902a --gold2:#c9a84c --night:#0d0c0a --ntext:#f0ece3
- Forms: Web3Forms API key 5b972adb-feba-4546-a657-02d5e29b6e29, submissions to hire@tryjoyn.me
- Language: hire/staff/role/letting go — never activate/agents/function/unsubscribing
- Brand: Joyn (capital J), tryjoyn.me (never tryjoin)

CURRENT SITE FILES:
{site_context}

RESPONSE FORMAT:
Respond with a JSON object like this:
{{
  "files": {{
    "path/to/file.html": "full file content here",
    "another/file.html": "full file content here"
  }},
  "summary": "Brief description of what was built/changed",
  "decisions": "Any decisions made or things the founder should know"
}}

Only include files that need to be created or modified. Output ONLY the JSON, no other text."""

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    print("Calling Claude API...")
    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=8000,
        messages=[
            {
                "role": "user",
                "content": f"Build request: {BUILD_INSTRUCTION}"
            }
        ],
        system=system_prompt
    )

    response_text = message.content[0].text.strip()
    print(f"Claude response received ({len(response_text)} chars)")

    # Parse JSON response
    try:
        # Strip markdown code fences if present
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        result = json.loads(response_text)
    except json.JSONDecodeError as e:
        print(f"Failed to parse Claude response as JSON: {e}")
        print(f"Response: {response_text[:500]}")
        post_github_comment(f"❌ Build failed — Claude returned invalid JSON.\n\nInstruction: {BUILD_INSTRUCTION}\n\nError: {e}")
        return

    files_changed = result.get("files", {})
    summary = result.get("summary", "Build complete")
    decisions = result.get("decisions", "")

    # Write files
    for path, content in files_changed.items():
        print(f"Writing: {path}")
        write_file(path, content)

    # Post comment to issue
    files_list = "\n".join([f"- `{p}`" for p in files_changed.keys()])
    comment = f"""✅ **Build complete**

**Instruction:** {BUILD_INSTRUCTION}

**Files changed:**
{files_list if files_list else "No files changed"}

**Summary:** {summary}

{f'**Decisions / Notes:** {decisions}' if decisions else ''}

*Deployed to tryjoyn.me — live in ~60 seconds*"""

    post_github_comment(comment)
    print("Build complete.")

if __name__ == "__main__":
    main()
