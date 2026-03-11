"""
Generate catalogue extensions to reach TARGET_COUNTS per vertical.
Uses OpenAI to generate realistic, fully-specified roles following seed patterns.
Run once: python generate_extensions.py
Output: extensions.json (list of role dicts ready for DB insertion)
"""
import os, json, time, random, string
from openai import OpenAI

client = OpenAI()

TARGET_COUNTS = {
    "Insurance & Risk": 87,
    "Healthcare Administration": 94,
    "Financial Advisory": 76,
    "Legal & Compliance": 82,
    "Real Estate": 61,
    "Software Engineering": 73,
    "HR & People Ops": 58,
    "Operations & Logistics": 69,
    "Construction & Property": 54,
    "Accounting & Tax": 71,
    "Private Equity & VC": 44,
    "Marketing & Growth": 48,
    "Supply Chain": 62,
    "Life Sciences": 55,
    "Energy & Utilities": 45,
    "Government & Public Sector": 38,
    "Media & Publishing": 36,
    "Architecture & Engineering": 52,
    "Retail & Consumer": 41,
    "Hospitality & Events": 33,
    "Nonprofit & Social": 29,
    "Sports & Entertainment": 28,
    "Education & Training": 31,
}

VERTICAL_PREFIX = {
    "Insurance & Risk": "ins",
    "Healthcare Administration": "hca",
    "Financial Advisory": "fin",
    "Legal & Compliance": "leg",
    "Real Estate": "re",
    "Software Engineering": "swe",
    "HR & People Ops": "hr",
    "Operations & Logistics": "ops",
    "Construction & Property": "con",
    "Accounting & Tax": "acc",
    "Private Equity & VC": "pe",
    "Marketing & Growth": "mkt",
    "Supply Chain": "sc",
    "Life Sciences": "ls",
    "Energy & Utilities": "ene",
    "Government & Public Sector": "gov",
    "Media & Publishing": "med",
    "Architecture & Engineering": "arc",
    "Retail & Consumer": "ret",
    "Hospitality & Events": "hosp",
    "Nonprofit & Social": "npo",
    "Sports & Entertainment": "spo",
    "Education & Training": "edu",
}

SCHEMA_EXAMPLE = {
    "id": "ins-001",
    "name": "Iris",
    "role": "Insurance Regulatory Intelligence Analyst",
    "mode": "autonomous",
    "vertical": "Insurance & Risk",
    "sub_vertical": "Regulatory Compliance",
    "target_hirer": "P&C and L&H carriers, MGAs, and brokers needing continuous state regulatory monitoring",
    "target_pain": "Regulatory bulletins, appetite changes, and compliance deadlines arrive faster than any team can track manually",
    "core_tasks": [
        "Monitor all 50 state DOI feeds and carrier bulletins daily",
        "Classify changes by line of business, urgency, and compliance deadline",
        "Produce structured regulatory briefings with action items"
    ],
    "named_outputs": [
        {"name": "Daily Regulatory Digest", "format": "Structured markdown report", "trigger": "Daily at 7am", "freq": "Daily"},
        {"name": "Compliance Alert", "format": "Priority-flagged JSON + email", "trigger": "Critical bulletin detected", "freq": "As needed"},
        {"name": "Monthly Appetite Map", "format": "Carrier appetite matrix", "trigger": "Month end", "freq": "Monthly"}
    ],
    "success_metrics": [
        "Zero missed compliance deadlines in 90-day period",
        "Bulletin classification accuracy >95% vs human review",
        "Alert-to-action time under 4 hours for critical changes"
    ],
    "moat_asset": "Proprietary regulatory taxonomy covering all 50 states across P&C and L&H lines, built from 12 years of practitioner experience",
    "build_complexity": "complex",
    "estimated_weeks": "6-8",
    "recommended_tools": ["Claude", "Manus"],
    "architecture_pattern": "Supervisor-worker: supervisor classifies and routes, workers handle state-specific deep analysis",
    "calibration_questions": [
        "Was this bulletin relevant to your specific book of business?",
        "Did the action item match what your compliance team would have recommended?",
        "Was the urgency classification correct?"
    ],
    "builder_guidance": {
        "key_data_sources": "State DOI websites, NAIC bulletins, carrier appetite guides, ISO circulars",
        "hardest_part": "Distinguishing material compliance changes from routine administrative updates without false positives",
        "common_bar_failures": "Vague escalation conditions, missing trigger definitions on outputs, no specimen output provided"
    },
    "status": "open",
    "track": "A"
}

def load_seed_roles():
    """Load the existing seed roles from the JS file."""
    import subprocess, tempfile
    js_path = os.path.join(os.path.dirname(__file__), 'joyn-catalogue-seed.js')
    # Write a small node script that reads the file by path
    script = f"""
const fs = require('fs');
const src = fs.readFileSync({json.dumps(js_path)}, 'utf8');
const match = src.match(/const\\s+\\w+\\s*=\\s*(\\[[\\s\\S]*\\]);/);
if (match) {{
    const arr = eval(match[1]);
    console.log(JSON.stringify(arr));
}} else {{
    console.log('[]');
}}
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
        f.write(script)
        script_path = f.name
    result = subprocess.run(['node', script_path], capture_output=True, text=True)
    os.unlink(script_path)
    return json.loads(result.stdout.strip())

def generate_roles_for_vertical(vertical, seed_examples, needed_count, existing_ids):
    """Generate needed_count new roles for a vertical using seed examples as reference."""
    prefix = VERTICAL_PREFIX.get(vertical, vertical[:3].lower())
    
    # Pick 2-3 seed examples for this vertical
    vertical_seeds = [r for r in seed_examples if r.get('vertical') == vertical]
    examples_to_show = vertical_seeds[:3] if vertical_seeds else seed_examples[:2]
    
    prompt = f"""You are generating AI staff role specifications for the Joyn marketplace.
Joyn is a platform where domain experts encode their expertise into AI staff that businesses can hire.

Generate exactly {needed_count} new, distinct role specifications for the vertical: "{vertical}"

Rules:
- Each role must be a specific professional function a business would hire for
- Mode must be either "autonomous" or "supervised"
- Names are single evocative words (like Iris, Atlas, Sage, Nova, Clio, etc.) — never generic
- Each role must be genuinely distinct — no duplicates or near-duplicates
- All fields must be fully populated — no nulls except track_b_note
- build_complexity: "simple" (1-2 weeks), "moderate" (2-4 weeks), or "complex" (4-8 weeks)
- estimated_weeks: string like "1-2", "2-4", "4-6", "6-8"
- recommended_tools: subset of ["Claude", "Manus", "Emergent", "make.com"]
- track: always "A" for these roles
- status: always "open"

Here are example roles from this or similar verticals to guide the format and depth:
{json.dumps(examples_to_show, indent=2)}

Return ONLY a valid JSON array of {needed_count} role objects. Each object must have ALL of these fields:
id, name, role, mode, vertical, sub_vertical, target_hirer, target_pain, core_tasks (array of 3),
named_outputs (array of 2-3 objects with name/format/trigger/freq), success_metrics (array of 3),
moat_asset, build_complexity, estimated_weeks, recommended_tools (array), architecture_pattern,
calibration_questions (array of 3), builder_guidance (object with key_data_sources/hardest_part/common_bar_failures),
status, track

For IDs, use the prefix "{prefix}" followed by a 3-digit number starting from {len(existing_ids) + 1:03d}.
Example: "{prefix}-{len(existing_ids) + 1:03d}"

Return ONLY the JSON array, no other text."""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8,
        max_tokens=8000,
    )
    
    content = response.choices[0].message.content.strip()
    # Extract JSON array
    if content.startswith('```'):
        content = content.split('```')[1]
        if content.startswith('json'):
            content = content[4:]
    content = content.strip()
    
    roles = json.loads(content)
    return roles

def main():
    print("Loading seed roles...")
    seed_roles = load_seed_roles()
    print(f"Loaded {len(seed_roles)} seed roles")
    
    # Count existing per vertical
    existing_by_vertical = {}
    for r in seed_roles:
        v = r.get('vertical', 'unknown')
        existing_by_vertical[v] = existing_by_vertical.get(v, 0) + 1
    
    all_extensions = []
    
    for vertical, target in TARGET_COUNTS.items():
        existing = existing_by_vertical.get(vertical, 0)
        needed = target - existing
        
        if needed <= 0:
            print(f"  {vertical}: already at {existing}/{target}, skipping")
            continue
        
        print(f"  {vertical}: generating {needed} roles (have {existing}, need {target})...")
        
        # Get existing IDs for this vertical
        prefix = VERTICAL_PREFIX.get(vertical, vertical[:3].lower())
        existing_ids = [r['id'] for r in seed_roles if r.get('vertical') == vertical]
        
        # Generate in batches of 5 to stay within token limits and avoid JSON truncation
        batch_size = 5
        generated = []
        batch_num = 0
        
        while len(generated) < needed:
            batch_needed = min(batch_size, needed - len(generated))
            batch_num += 1
            
            try:
                batch = generate_roles_for_vertical(
                    vertical, 
                    seed_roles + generated,  # include already generated as examples
                    batch_needed,
                    existing_ids + [r['id'] for r in generated]
                )
                generated.extend(batch)
                print(f"    Batch {batch_num}: generated {len(batch)} roles (total: {len(generated)}/{needed})")
                time.sleep(0.5)  # Rate limit courtesy
            except Exception as e:
                print(f"    Batch {batch_num} error: {e}")
                if batch_needed > 3:
                    # Try with smaller batch
                    batch_size = max(2, batch_size - 2)
                    print(f"    Reducing batch size to {batch_size}")
                time.sleep(2)
                continue
        
        all_extensions.extend(generated[:needed])
        print(f"  {vertical}: done. Generated {len(generated[:needed])} roles.")
    
    # Save to file
    output_path = os.path.join(os.path.dirname(__file__), 'extensions.json')
    with open(output_path, 'w') as f:
        json.dump(all_extensions, f, indent=2)
    
    total = len(seed_roles) + len(all_extensions)
    print(f"\nDone. Generated {len(all_extensions)} extension roles.")
    print(f"Total catalogue size: {total} roles")
    print(f"Saved to: {output_path}")

if __name__ == '__main__':
    main()
