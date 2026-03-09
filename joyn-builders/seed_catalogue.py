"""
seed_catalogue.py — Joyn Builder Catalogue Seeder
Run once after deploy on Railway: python seed_catalogue.py
Converts joyn-catalogue-seed.js data to SQLite rows.
"""
import os
import json
import uuid
import sqlite3
import subprocess
import tempfile

DB_PATH = os.environ.get("DB_PATH", "joyn_builders.db")

# ── Convert JS catalogue to Python ────────────────────────────────────────────
# We use Node.js to parse the JS file and output JSON
JS_SEED_PATH = os.path.join(os.path.dirname(__file__), "joyn-catalogue-seed.js")

def load_catalogue_from_js(js_path):
    """Parse the JS catalogue file using Node.js and return a list of dicts."""
    wrapper = f"""
const fs = require('fs');
const src = fs.readFileSync('{js_path}', 'utf8');
// Strip JS comments and extract the array
const cleaned = src
  .replace(/\\/\\/[^\\n]*/g, '')
  .replace(/\\/\\*[\\s\\S]*?\\*\\//g, '');
// Find the array content between first [ and last ]
const start = cleaned.indexOf('[');
const end = cleaned.lastIndexOf(']');
const arrStr = cleaned.slice(start, end + 1);
// Evaluate safely
let catalogue;
try {{
  catalogue = eval('(' + arrStr + ')');
}} catch(e) {{
  // Try wrapping keys
  const fixed = arrStr.replace(/([{{,\\s])([a-zA-Z_][a-zA-Z0-9_]*)\\s*:/g, '$1"$2":');
  catalogue = JSON.parse(fixed);
}}
console.log(JSON.stringify(catalogue));
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
        f.write(wrapper)
        tmp_path = f.name
    
    try:
        result = subprocess.run(['node', tmp_path], capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            print(f"Node error: {result.stderr}")
            return []
        return json.loads(result.stdout)
    except Exception as e:
        print(f"Error loading catalogue: {e}")
        return []
    finally:
        os.unlink(tmp_path)


JSON_SEED_PATH = os.path.join(os.path.dirname(__file__), "catalogue_seed.json")


def seed():
    print("Loading catalogue seed data...")
    catalogue = []

    # Try loading from pre-converted JSON file first (no Node.js needed)
    if os.path.exists(JSON_SEED_PATH):
        try:
            with open(JSON_SEED_PATH) as f:
                catalogue = json.load(f)
            print(f"Loaded {len(catalogue)} roles from JSON seed file")
        except Exception as e:
            print(f"JSON load error: {e}")
            catalogue = []

    # Fall back to JS file parsing if JSON not available
    if not catalogue and os.path.exists(JS_SEED_PATH):
        catalogue = load_catalogue_from_js(JS_SEED_PATH)
        print(f"Loaded {len(catalogue)} roles from JS seed file")

    # Final fallback: embedded sample data
    if not catalogue:
        catalogue = get_embedded_sample()
        print(f"Using {len(catalogue)} embedded sample roles")
    
    conn = get_db()
    
    # Create tables if not exist (mirrors app.py init_db)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS catalogue (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            role TEXT NOT NULL,
            mode TEXT CHECK(mode IN ('autonomous','supervised')),
            vertical TEXT NOT NULL,
            sub TEXT,
            hirer TEXT,
            pain TEXT,
            tasks TEXT,
            outputs TEXT,
            metrics TEXT,
            complexity TEXT CHECK(complexity IN ('simple','moderate','complex')),
            weeks TEXT,
            tools TEXT,
            pattern TEXT,
            moat TEXT,
            calibration_questions TEXT,
            builder_guidance TEXT,
            status TEXT DEFAULT 'open' CHECK(status IN ('open','claimed','live')),
            track TEXT DEFAULT 'A' CHECK(track IN ('A','B')),
            live_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_catalogue_vertical ON catalogue(vertical);
        CREATE INDEX IF NOT EXISTS idx_catalogue_status ON catalogue(status);
        CREATE INDEX IF NOT EXISTS idx_catalogue_track ON catalogue(track);
    """)
    
    inserted = 0
    skipped = 0
    
    for role in catalogue:
        role_id = role.get('id') or str(uuid.uuid4())
        
        # Check if already exists
        existing = conn.execute("SELECT id FROM catalogue WHERE id=?", (role_id,)).fetchone()
        if existing:
            skipped += 1
            continue
        
        try:
            conn.execute("""
                INSERT INTO catalogue (
                    id, name, role, mode, vertical, sub, hirer, pain,
                    tasks, outputs, metrics, complexity, weeks, tools,
                    pattern, moat, calibration_questions, builder_guidance,
                    status, track
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                role_id,
                str(role.get('name', '')),
                str(role.get('role', '')),
                str(role.get('mode', 'autonomous')),
                str(role.get('vertical', '')),
                str(role.get('sub', '') or ''),
                str(role.get('hirer', '') or ''),
                str(role.get('pain', '') or ''),
                json.dumps(role.get('tasks', []) or []),
                json.dumps(role.get('outputs', []) or []),
                json.dumps(role.get('metrics', []) or []),
                str(role.get('complexity', 'moderate')),
                str(role.get('weeks', '2-4') or '2-4'),
                json.dumps(role.get('tools', []) or []),
                str(role.get('pattern', '') or ''),
                str(role.get('moat', '') or ''),
                json.dumps(role.get('calibration_questions', []) or []),
                json.dumps(role.get('builder_guidance', {}) or {}),
                str(role.get('status', 'open')) if role.get('status') in ('open','claimed','live') else 'open',
                str(role.get('track', 'A')),
            ))
            inserted += 1
        except Exception as e:
            print(f"  Error inserting {role_id}: {e}")
            skipped += 1
    
    conn.commit()
    
    total = conn.execute("SELECT COUNT(*) FROM catalogue").fetchone()[0]
    verticals = conn.execute("SELECT COUNT(DISTINCT vertical) FROM catalogue").fetchone()[0]
    conn.close()
    
    print(f"\nSeed complete:")
    print(f"  Inserted: {inserted}")
    print(f"  Skipped (already exist): {skipped}")
    print(f"  Total in catalogue: {total}")
    print(f"  Verticals: {verticals}")


def get_embedded_sample():
    """Minimal embedded sample — used only if JS seed file unavailable."""
    return [
        {
            "id": "ins-001", "name": "Iris", "role": "Insurance Regulatory Intelligence",
            "mode": "autonomous", "vertical": "Insurance & Risk", "sub": "Regulatory Monitoring",
            "hirer": "Insurance carriers and MGAs", "pain": "Material regulatory changes missed until they create exposure",
            "tasks": ["Monitor state insurance department bulletins", "Score by client impact", "Route alerts"],
            "outputs": [{"name": "Regulatory Alert", "format": "Email", "trigger": "Material change detected", "freq": "As triggered"}],
            "metrics": ["Alert delivery before client discovery", "Coverage completeness"],
            "complexity": "moderate", "weeks": "2-4", "tools": ["Manus", "Claude Code"],
            "pattern": "Monitor→Score→Alert", "moat": "Regulatory impact patterns by jurisdiction and line of business",
            "calibration_questions": ["Were impact scores accurate?", "Did alerts arrive before clients raised the issue?", "Which jurisdictions need better coverage?"],
            "builder_guidance": {"key_data_sources": ["State OIR websites", "NAIC"], "hardest_part": "Impact scoring by line of business", "common_bar_failures": ["Alerts too broad"]},
            "status": "open", "track": "A"
        },
        {
            "id": "ops-001", "name": "Dispatch", "role": "Field Services Dispatcher",
            "mode": "autonomous", "vertical": "Operations & Logistics", "sub": "Field Operations",
            "hirer": "Field service businesses", "pain": "Missed calls and slow dispatch losing jobs",
            "tasks": ["Answer inbound calls", "Book jobs", "Send confirmations"],
            "outputs": [{"name": "Booking Confirmation", "format": "SMS/Email", "trigger": "Job booked", "freq": "Per booking"}],
            "metrics": ["Call answer rate", "Booking conversion rate"],
            "complexity": "moderate", "weeks": "2-4", "tools": ["Manus", "Emergent"],
            "pattern": "Receive→Qualify→Book→Confirm", "moat": "Dispatch patterns by service type and geography",
            "calibration_questions": ["Were bookings accurate?", "Any missed calls?", "Confirmation timing appropriate?"],
            "builder_guidance": {"key_data_sources": ["Calendar API", "CRM"], "hardest_part": "Real-time scheduling logic", "common_bar_failures": ["Double bookings"]},
            "status": "open", "track": "A"
        },
    ]


if __name__ == "__main__":
    seed()
