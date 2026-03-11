"""
agents/deployment_agent.py — Joyn Deployment Agent

Takes a passed Visionary Spec and generates a production-ready
marketplace listing HTML page for the AI staff.

The listing page follows the exact same design system as iris-insurance-regulatory.html
and probe-insurance-innovation.html — single self-contained HTML file,
Joyn design system, no external CSS frameworks.

Architecture: Single-pass LLM call generating the full HTML.
Triggered when: Reviewer Agent returns 'pass' verdict.

The generated HTML is:
1. Validated against the design spec (no border-radius, no box-shadow,
   only approved palette colours, correct fonts)
2. Saved to marketplace/{staff-slug}-{vertical-slug}.html
3. Committed to the GitHub repository
4. Listed in data/roster.json

Returns:
  - listing_html: full HTML string
  - filename: e.g. "dispatch-operations.html"
  - listing_url: e.g. "https://tryjoyn.me/marketplace/dispatch-operations.html"
  - design_check: pass/fail with specific issues
"""
from __future__ import annotations
import json
import logging
import os
import re
import sqlite3
from typing import Optional

logger = logging.getLogger(__name__)

try:
    from openai import OpenAI
    _client = OpenAI()
    _MODEL = os.environ.get("DEPLOYMENT_MODEL", "gpt-4.1-mini")
    _LLM_AVAILABLE = True
except ImportError:
    _LLM_AVAILABLE = False
    logger.warning("openai package not available — DeploymentAgent running in template mode")

# Approved palette — any other hex is a design violation
APPROVED_PALETTE = {
    '#fafaf8', '#111110', '#3f3f3e', '#e8e4dc',
    '#d0ccc4', '#f4f1eb', '#b8902a', '#8b6914', '#7a5c10'
}

SYSTEM_PROMPT = """You are the Joyn Deployment Agent. Your job is to generate a production-ready
marketplace listing HTML page for an AI staff that has passed The Bar.

CRITICAL DESIGN RULES — violating any of these is an automatic fail:
1. Single self-contained HTML file — all CSS and JS inline
2. NO border-radius on any element
3. NO box-shadow on any element
4. NO external CSS frameworks (no Bootstrap, Tailwind, etc.)
5. ONLY these approved hex colours (use CSS custom properties):
   --white: #fafaf8
   --ink: #111110
   --ink-secondary: #3f3f3e
   --rule: #e8e4dc
   --rule-mid: #d0ccc4
   --surface: #f4f1eb
   --gold-display: #b8902a
   --gold-text: #8B6914
   --gold-hover: #7a5c10
6. ONLY these three fonts (via Google Fonts CDN):
   - Cormorant Garamond: headings, hero text
   - DM Mono: labels, metadata, tags, UI elements
   - Syne: body text, descriptions
7. NO keyframe animations — transitions max 0.2s ease only
8. NO lorem ipsum — every word is real copy about this specific AI staff
9. NO forbidden terms: agent, bot, activate, subscribe, cancel
   USE instead: staff, hire, letting someone go
10. Transitions: 0.15s–0.2s ease ONLY

The listing page must include:
- Hero section: staff name, role definition (one sentence), mode badge, hire CTA
- What it does: 3 core tasks in plain language
- Named outputs: table with name, format, trigger, frequency
- Hirer experience: timeline showing intervention points and total time
- Moat asset: what makes this staff uniquely valuable over time
- Calibration: how it learns and improves
- Hire section: pricing, hire CTA linking to hire page

The hire CTA should link to: ./[staff-slug]-hire.html

Return ONLY the complete HTML — no markdown, no explanation, just the HTML."""


def run(visionary_spec: dict, builder: dict) -> dict:
    """
    Generate the marketplace listing HTML page.
    
    Parameters
    ----------
    visionary_spec : dict
        Passed Visionary Spec from the Architect Agent
    builder : dict
        Builder record from the database
    
    Returns
    -------
    dict
        {listing_html, filename, listing_url, design_check}
    """
    if _LLM_AVAILABLE:
        html = _llm_listing(visionary_spec, builder)
    else:
        html = _template_listing(visionary_spec, builder)
    
    # Generate filename
    staff_name = visionary_spec.get('staff_name', 'ai-staff')
    vertical = visionary_spec.get('vertical', 'general')
    slug = _slugify(staff_name)
    vertical_slug = _slugify(vertical)
    filename = f"{slug}-{vertical_slug}.html"
    listing_url = f"https://tryjoyn.me/marketplace/{filename}"
    hire_filename = f"{slug}-hire.html"
    
    # Replace placeholder hire link
    html = html.replace('./[staff-slug]-hire.html', f'./{hire_filename}')
    
    # Design check
    design_check = _check_design(html)
    
    return {
        "listing_html": html,
        "filename": filename,
        "listing_url": listing_url,
        "hire_filename": hire_filename,
        "design_check": design_check,
        "staff_slug": slug,
        "agent": "deployment",
        "model": _MODEL if _LLM_AVAILABLE else "template",
    }


def _llm_listing(visionary_spec: dict, builder: dict) -> str:
    """Use LLM to generate the listing HTML."""
    
    prompt = f"""Generate the marketplace listing page for this AI staff:

{json.dumps(visionary_spec, indent=2)}

Builder: {builder.get('full_name', 'Unknown')} — {builder.get('vertical', 'Unknown')} specialist

The page must follow all design rules exactly. Generate the complete, production-ready HTML."""

    try:
        response = _client.chat.completions.create(
            model=_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=4000,
        )
        html = response.choices[0].message.content.strip()
        # Strip any markdown code fences if present
        if html.startswith('```'):
            html = re.sub(r'^```[a-z]*\n?', '', html)
            html = re.sub(r'\n?```$', '', html)
        return html
    except Exception as e:
        logger.error(f"DeploymentAgent LLM error: {e}")
        return _template_listing(visionary_spec, builder)


def _template_listing(visionary_spec: dict, builder: dict) -> str:
    """Generate a template listing page from the Visionary Spec."""
    
    staff_name = visionary_spec.get('staff_name', 'AI Staff')
    role_def = visionary_spec.get('role_definition', 'Performs specialised professional tasks.')
    mode = visionary_spec.get('mode', 'autonomous').capitalize()
    vertical = visionary_spec.get('vertical', 'Operations')
    target_hirer = visionary_spec.get('target_hirer', 'Businesses')
    core_pain = visionary_spec.get('core_pain', 'Manual professional tasks consuming expert time')
    moat = visionary_spec.get('moat_asset', 'Domain-specific pattern intelligence')
    
    # Agent roster
    roster = visionary_spec.get('agent_roster', [])
    roster_rows = ""
    for agent in roster:
        roster_rows += f"""
        <tr>
          <td style="padding:1rem 1.5rem;border-bottom:1px solid var(--rule);font-family:'Cormorant Garamond',serif;font-size:1.05rem;">{agent.get('name','')}</td>
          <td style="padding:1rem 1.5rem;border-bottom:1px solid var(--rule);font-size:0.9rem;color:var(--ink-secondary);">{agent.get('function','')}</td>
          <td style="padding:1rem 1.5rem;border-bottom:1px solid var(--rule);font-size:0.9rem;color:var(--ink-secondary);">{agent.get('produces','')}</td>
        </tr>"""
    
    # Named outputs
    outputs = visionary_spec.get('named_outputs', [])
    output_rows = ""
    for out in outputs:
        output_rows += f"""
        <tr>
          <td style="padding:1rem 1.5rem;border-bottom:1px solid var(--rule);font-family:'Cormorant Garamond',serif;font-size:1.05rem;">{out.get('name','')}</td>
          <td style="padding:1rem 1.5rem;border-bottom:1px solid var(--rule);font-family:'DM Mono',monospace;font-size:0.8rem;">{out.get('format','')}</td>
          <td style="padding:1rem 1.5rem;border-bottom:1px solid var(--rule);font-size:0.9rem;color:var(--ink-secondary);">{out.get('trigger','')}</td>
          <td style="padding:1rem 1.5rem;border-bottom:1px solid var(--rule);font-family:'DM Mono',monospace;font-size:0.8rem;">{out.get('frequency','')}</td>
        </tr>"""
    
    # Calibration questions
    calib = visionary_spec.get('calibration_architecture', {})
    calib_questions = calib.get('calibration_questions', [])
    calib_list = "".join([f"<li style='margin-bottom:0.5rem;color:var(--ink-secondary);'>{q}</li>" for q in calib_questions])
    
    # Hirer experience
    hirer_exp = visionary_spec.get('hirer_experience', {})
    total_time = hirer_exp.get('total_time_minutes', 30)
    intervention_points = hirer_exp.get('intervention_points', [])
    intervention_html = ""
    for i, point in enumerate(intervention_points):
        intervention_html += f"""
        <div style="display:flex;gap:1.5rem;align-items:flex-start;padding:1.25rem 0;border-bottom:1px solid var(--rule);">
          <div style="font-family:'DM Mono',monospace;font-size:0.7rem;letter-spacing:0.1em;text-transform:uppercase;color:var(--gold-text);min-width:3rem;padding-top:0.15rem;">0{i+1}</div>
          <div>
            <div style="font-family:'Cormorant Garamond',serif;font-size:1.1rem;margin-bottom:0.25rem;">{point.get('point','')}</div>
            <div style="font-size:0.9rem;color:var(--ink-secondary);">{point.get('action_required','')} · {point.get('time_minutes',0)} min</div>
          </div>
        </div>"""
    
    slug = _slugify(staff_name)
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{staff_name} · Joyn AI Staff Marketplace</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;0,600;1,300;1,400;1,500&family=DM+Mono:wght@300;400;500&family=Syne:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
  :root {{
    --white: #fafaf8; --ink: #111110; --ink-secondary: #3f3f3e;
    --rule: #e8e4dc; --rule-mid: #d0ccc4; --surface: #f4f1eb;
    --gold-display: #b8902a; --gold-text: #8B6914; --gold-hover: #7a5c10;
  }}
  *, *::before, *::after {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ background: var(--white); color: var(--ink); font-family: 'Syne', sans-serif; font-size: 1rem; line-height: 1.8; -webkit-font-smoothing: antialiased; }}
  h1, h2, h3, h4 {{ font-family: 'Cormorant Garamond', serif; font-weight: 400; color: var(--ink); }}
  p {{ color: var(--ink-secondary); }}
  a {{ color: var(--gold-text); text-decoration: none; transition: color 0.2s ease; }}
  a:hover {{ color: var(--gold-hover); }}
  .nav {{ display: flex; justify-content: space-between; align-items: center; padding: 1.25rem clamp(1.5rem,5vw,4rem); border-bottom: 1px solid var(--rule); background: var(--white); }}
  .nav-logo {{ font-family: 'DM Mono', monospace; font-size: 0.85rem; letter-spacing: 0.12em; text-transform: uppercase; color: var(--ink); text-decoration: none; }}
  .nav-links {{ display: flex; gap: 2rem; align-items: center; }}
  .nav-links a {{ font-family: 'DM Mono', monospace; font-size: 0.7rem; letter-spacing: 0.08em; text-transform: uppercase; color: var(--ink-secondary); }}
  .btn {{ display: inline-flex; padding: 0.875rem 2rem; font-family: 'DM Mono', monospace; font-size: 0.75rem; letter-spacing: 0.1em; text-transform: uppercase; align-items: center; justify-content: center; text-decoration: none; border: none; cursor: pointer; transition: background 0.2s ease, color 0.2s ease; }}
  .btn-primary {{ background: var(--ink); color: var(--white); }}
  .btn-primary:hover {{ background: #2a2a29; color: var(--white); }}
  .btn-gold {{ background: var(--gold-text); color: var(--white); }}
  .btn-gold:hover {{ background: var(--gold-hover); color: var(--white); }}
  .label {{ font-family: 'DM Mono', monospace; font-size: 0.65rem; letter-spacing: 0.12em; text-transform: uppercase; color: var(--gold-text); }}
  .mode-badge {{ display: inline-block; font-family: 'DM Mono', monospace; font-size: 0.65rem; letter-spacing: 0.1em; text-transform: uppercase; padding: 0.3rem 0.75rem; border: 1px solid var(--rule-mid); color: var(--ink-secondary); background: var(--surface); }}
  .section {{ padding: clamp(3rem,6vw,5rem) clamp(1.5rem,5vw,4rem); border-bottom: 1px solid var(--rule); }}
  .section-label {{ font-family: 'DM Mono', monospace; font-size: 0.65rem; letter-spacing: 0.12em; text-transform: uppercase; color: var(--gold-text); margin-bottom: 1.25rem; }}
  .section h2 {{ font-size: clamp(1.75rem,3vw,2.5rem); margin-bottom: 1rem; }}
  table {{ width: 100%; border-collapse: collapse; }}
  th {{ font-family: 'DM Mono', monospace; font-size: 0.65rem; letter-spacing: 0.1em; text-transform: uppercase; color: var(--ink-secondary); padding: 0.75rem 1.5rem; text-align: left; background: var(--surface); border-bottom: 1px solid var(--rule-mid); }}
</style>
</head>
<body>

<nav class="nav">
  <a href="/" class="nav-logo">Joyn</a>
  <div class="nav-links">
    <a href="/marketplace/">Marketplace</a>
    <a href="/marketplace/creator-studio.html">Build</a>
    <a href="./{slug}-hire.html" class="btn btn-primary">Hire {staff_name}</a>
  </div>
</nav>

<!-- HERO -->
<section style="padding:clamp(4rem,8vw,7rem) clamp(1.5rem,5vw,4rem);border-bottom:1px solid var(--rule);background:var(--surface);">
  <div style="max-width:900px;">
    <div style="display:flex;gap:1rem;align-items:center;margin-bottom:1.5rem;">
      <span class="mode-badge">{mode}</span>
      <span class="label">{vertical}</span>
    </div>
    <h1 style="font-size:clamp(2.5rem,5vw,4rem);font-weight:300;line-height:1.1;margin-bottom:1.25rem;">{staff_name}</h1>
    <p style="font-size:1.2rem;max-width:60ch;margin-bottom:2rem;color:var(--ink-secondary);">{role_def}</p>
    <div style="display:flex;gap:1rem;flex-wrap:wrap;">
      <a href="./{slug}-hire.html" class="btn btn-gold">Hire {staff_name} →</a>
      <a href="/marketplace/" class="btn" style="border:1.5px solid var(--ink);color:var(--ink);">Browse All Staff</a>
    </div>
  </div>
</section>

<!-- THE PROBLEM -->
<section class="section">
  <div class="section-label">The Problem</div>
  <h2>What {staff_name} solves</h2>
  <p style="max-width:65ch;font-size:1.05rem;">{core_pain}</p>
  <p style="margin-top:1rem;max-width:65ch;">Hired by {target_hirer}.</p>
</section>

<!-- AGENT ROSTER -->
<section class="section" style="background:var(--surface);">
  <div class="section-label">How It Works</div>
  <h2>The {staff_name} team</h2>
  <p style="max-width:65ch;margin-bottom:2rem;">{len(roster)} specialised {'worker' if len(roster) == 1 else 'workers'}, each with a defined function and handoff protocol.</p>
  <table>
    <thead>
      <tr>
        <th>Worker</th>
        <th>Function</th>
        <th>Produces</th>
      </tr>
    </thead>
    <tbody>
      {roster_rows}
    </tbody>
  </table>
</section>

<!-- NAMED OUTPUTS -->
<section class="section">
  <div class="section-label">What You Receive</div>
  <h2>Named outputs</h2>
  <p style="max-width:65ch;margin-bottom:2rem;">Every output is named, formatted, triggered, and delivered on a defined schedule.</p>
  <table>
    <thead>
      <tr>
        <th>Output</th>
        <th>Format</th>
        <th>Trigger</th>
        <th>Frequency</th>
      </tr>
    </thead>
    <tbody>
      {output_rows}
    </tbody>
  </table>
</section>

<!-- HIRER EXPERIENCE -->
<section class="section" style="background:var(--surface);">
  <div class="section-label">Your Time Commitment</div>
  <h2>What hiring {staff_name} looks like</h2>
  <p style="max-width:65ch;margin-bottom:2rem;">Total time required: <strong>{total_time} minutes</strong> across the full engagement lifecycle.</p>
  {intervention_html}
</section>

<!-- PLATFORM INTELLIGENCE / MOAT -->
<section class="section" style="border-left:3px solid var(--gold-display);padding-left:calc(clamp(1.5rem,5vw,4rem) - 3px);">
  <div class="section-label">Platform Intelligence</div>
  <h2>What {staff_name} builds over time</h2>
  <p style="max-width:65ch;font-size:1.05rem;">{moat}</p>
</section>

<!-- CALIBRATION -->
<section class="section" style="background:var(--surface);">
  <div class="section-label">Calibration</div>
  <h2>How {staff_name} improves</h2>
  <p style="max-width:65ch;margin-bottom:1.5rem;">{calib.get('feedback_mechanism', 'Feedback collected after each engagement and carried forward.')}</p>
  <p style="font-family:'DM Mono',monospace;font-size:0.7rem;letter-spacing:0.08em;text-transform:uppercase;color:var(--ink-secondary);margin-bottom:0.75rem;">Calibration questions after each engagement:</p>
  <ul style="list-style:none;padding:0;">
    {calib_list}
  </ul>
</section>

<!-- HIRE CTA -->
<section class="section" style="text-align:center;padding:clamp(4rem,8vw,7rem) clamp(1.5rem,5vw,4rem);">
  <div class="section-label" style="text-align:center;">Ready to hire</div>
  <h2 style="font-size:clamp(2rem,4vw,3rem);margin-bottom:1rem;">Hire {staff_name}</h2>
  <p style="max-width:50ch;margin:0 auto 2rem;font-size:1.05rem;">{role_def}</p>
  <a href="./{slug}-hire.html" class="btn btn-gold" style="font-size:0.8rem;padding:1rem 2.5rem;">Hire {staff_name} →</a>
</section>

<footer style="padding:2rem clamp(1.5rem,5vw,4rem);border-top:1px solid var(--rule);display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:1rem;">
  <span style="font-family:'DM Mono',monospace;font-size:0.65rem;letter-spacing:0.08em;text-transform:uppercase;color:var(--ink-secondary);">Joyn · tryjoyn.me</span>
  <div style="display:flex;gap:2rem;">
    <a href="/marketplace/" style="font-family:'DM Mono',monospace;font-size:0.65rem;letter-spacing:0.08em;text-transform:uppercase;color:var(--ink-secondary);">Marketplace</a>
    <a href="mailto:hire@tryjoyn.me" style="font-family:'DM Mono',monospace;font-size:0.65rem;letter-spacing:0.08em;text-transform:uppercase;color:var(--ink-secondary);">hire@tryjoyn.me</a>
  </div>
</footer>

</body>
</html>"""


def _check_design(html: str) -> dict:
    """Validate the generated HTML against the design spec."""
    issues = []
    
    if 'border-radius' in html:
        issues.append("border-radius found — must be removed")
    if 'box-shadow' in html:
        issues.append("box-shadow found — must be removed")
    
    # Check for hardcoded hex colours not in approved palette
    hex_pattern = re.compile(r'(?<!var\()#[0-9a-fA-F]{3,6}(?![0-9a-fA-F])')
    hex_matches = set(hex_pattern.findall(html))
    invalid_hex = [h for h in hex_matches if h.lower() not in APPROVED_PALETTE]
    if invalid_hex:
        issues.append(f"Unapproved hex colours: {', '.join(invalid_hex[:5])}")
    
    # Check for forbidden terms
    for term in ['agent', 'bot', 'activate', 'subscribe', 'cancel']:
        # Allow 'agent' in HTML comments or meta tags but not in user-facing copy
        if f'>{term}' in html.lower() or f' {term} ' in html.lower():
            issues.append(f"Forbidden term '{term}' found in user-facing copy")
    
    return {
        "status": "pass" if not issues else "fail",
        "issues": issues
    }


def _slugify(text: str) -> str:
    """Convert text to URL-safe slug."""
    slug = text.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'\s+', '-', slug.strip())
    slug = re.sub(r'-+', '-', slug)
    return slug[:50]
