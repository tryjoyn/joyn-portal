import os
import json
import uuid
from datetime import datetime
from flask import Flask, request, jsonify
from db import get_db

# Agent system — graceful degradation if agents unavailable
try:
    from agents import intake as intake_agent, architect as architect_agent
    from agents import reviewer as reviewer_agent, deployment as deployment_agent
    _AGENTS_AVAILABLE = True
except ImportError as _agent_err:
    _AGENTS_AVAILABLE = False
    import logging
    logging.getLogger(__name__).warning(f'Agent system unavailable: {_agent_err}')
from flask_cors import CORS
import stripe
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

app = Flask(__name__)

# CORS — explicit origins, no wildcard with credentials
CORS(app, resources={r"/api/*": {
    "origins": [
        "https://tryjoyn.me",
        "https://www.tryjoyn.me",
        "https://tryjoyn.github.io",
        "http://localhost:8080",
        "http://localhost:3000",
        "http://localhost:5173"
    ],
    "methods": ["GET","POST","PUT","OPTIONS"],
    "allow_headers": ["Content-Type","Authorization"],
    "supports_credentials": False
}})

@app.route("/api/<path:path>", methods=["OPTIONS"])
def options_handler(path):
    return "", 204

# All secrets from environment — never hardcoded
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")
STRIPE_PUBLISHABLE_KEY = os.environ.get("STRIPE_PUBLISHABLE_KEY","")
SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET")
DB_PATH = os.environ.get("DB_PATH","joyn_builders.db")

def log_event(builder_id, event_type, data=None):
    try:
        conn = get_db()
        conn.execute(
            "INSERT INTO builder_events (id,builder_id,event_type,event_data,created_at) VALUES (?,?,?,?,?)",
            (str(uuid.uuid4()), builder_id, event_type, json.dumps(data or {}), datetime.utcnow().isoformat())
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[EVENT LOG ERROR] {e}")

def parse_json_fields(role_dict, fields):
    for f in fields:
        try:
            role_dict[f] = json.loads(role_dict.get(f) or '[]')
        except:
            role_dict[f] = []
    return role_dict

# ── HEALTH ──────────────────────────────────────────────────

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status":"ok","service":"joyn-builders","time":datetime.utcnow().isoformat()})

# ── CATALOGUE ───────────────────────────────────────────────

@app.route("/api/catalogue", methods=["GET"])
def get_catalogue():
    vertical = request.args.get("vertical")
    mode = request.args.get("mode")
    status = request.args.get("status")
    track = request.args.get("track")
    complexity = request.args.get("complexity")
    search = request.args.get("q","").strip()
    limit = min(int(request.args.get("limit",50)),100)
    offset = int(request.args.get("offset",0))

    conn = get_db()
    base = "SELECT * FROM catalogue WHERE 1=1"
    params = []

    if vertical and vertical != "all":
        base += " AND vertical=?"; params.append(vertical)
    if mode and mode != "all":
        base += " AND mode=?"; params.append(mode)
    if status and status != "all":
        base += " AND status=?"; params.append(status)
    if track and track != "all":
        base += " AND track=?"; params.append(track)
    if complexity and complexity != "all":
        base += " AND complexity=?"; params.append(complexity)
    if search:
        base += " AND (name LIKE ? OR role LIKE ? OR pain LIKE ? OR sub LIKE ? OR vertical LIKE ?)"
        s = f"%{search}%"
        params.extend([s,s,s,s,s])

    total = conn.execute(f"SELECT COUNT(*) FROM ({base})", params).fetchone()[0]

    ordered = base + " ORDER BY CASE status WHEN 'live' THEN 0 WHEN 'in_build' THEN 1 WHEN 'claimed' THEN 2 ELSE 3 END, name ASC"
    ordered += f" LIMIT {limit} OFFSET {offset}"

    rows = conn.execute(ordered, params).fetchall()
    conn.close()

    roles = []
    for r in rows:
        rd = dict(r)
        rd = parse_json_fields(rd, ['tasks','outputs','metrics','tools','calibration_questions'])
        try: rd['builder_guidance'] = json.loads(rd.get('builder_guidance') or '{}')
        except: rd['builder_guidance'] = {}
        roles.append(rd)

    return jsonify({"roles":roles,"total":total,"offset":offset,"limit":limit})


@app.route("/api/catalogue/verticals", methods=["GET"])
def get_verticals():
    """Return vertical summary counts for filter bar and stats."""
    conn = get_db()
    rows = conn.execute("""
        SELECT vertical,
               COUNT(*) as total,
               SUM(CASE WHEN status='live' THEN 1 ELSE 0 END) as live_count,
               SUM(CASE WHEN status='in_build' THEN 1 ELSE 0 END) as in_build_count,
               SUM(CASE WHEN status='open' THEN 1 ELSE 0 END) as open_count
        FROM catalogue
        GROUP BY vertical
        ORDER BY vertical ASC
    """).fetchall()
    conn.close()
    return jsonify({"verticals": [dict(r) for r in rows]})


@app.route("/api/catalogue/search", methods=["POST"])
def search_catalogue():
    data = request.get_json()
    query = (data.get("q") or data.get("query") or "").lower().strip()
    vertical = data.get("vertical")
    mode = data.get("mode")

    if not query:
        return jsonify({"matches":[],"suggestion":None})

    conn = get_db()
    all_roles = conn.execute("SELECT * FROM catalogue").fetchall()
    conn.close()

    scored = []
    for r in all_roles:
        role = dict(r)
        score = 0
        name_l = role['name'].lower()
        role_l = role['role'].lower()
        pain_l = (role.get('pain') or '').lower()
        tasks_l = (role.get('tasks') or '').lower()
        vert_l = role['vertical'].lower()
        sub_l = (role.get('sub') or '').lower()

        if query == name_l: score += 200
        elif query in name_l: score += 100
        if query in role_l: score += 60
        if query in pain_l: score += 45
        if query in sub_l: score += 35
        if query in vert_l: score += 30
        if query in tasks_l: score += 20

        for word in query.split():
            if len(word) < 3: continue
            if word in name_l: score += 25
            if word in role_l: score += 15
            if word in pain_l: score += 12
            if word in vert_l: score += 10
            if word in sub_l: score += 10

        if vertical and vertical != "all":
            if role['vertical'].lower() == vertical.lower(): score += 30

        if mode and mode != "all":
            if role['mode'] == mode: score += 20

        if score > 0:
            if score >= 100: mt = "exact"
            elif score >= 50: mt = "high"
            elif score >= 25: mt = "partial"
            else: mt = "adjacent"
            role['_score'] = score
            role['_match_type'] = mt
            scored.append(role)

    scored.sort(key=lambda x: x['_score'], reverse=True)
    top = scored[:8]

    for role in top:
        role = parse_json_fields(role, ['tasks','outputs','metrics','tools'])

    return jsonify({"matches":top,"total_scored":len(scored),"suggestion":top[0] if top else None})


@app.route("/api/catalogue/<role_id>", methods=["GET"])
def get_role(role_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM catalogue WHERE id=?", (role_id,)).fetchone()
    conn.close()
    if not row: return jsonify({"error":"Role not found"}), 404
    rd = dict(row)
    rd = parse_json_fields(rd, ['tasks','outputs','metrics','tools','calibration_questions'])
    try: rd['builder_guidance'] = json.loads(rd.get('builder_guidance') or '{}')
    except: rd['builder_guidance'] = {}
    return jsonify(rd)

# ── BUILDER APPLICATION ──────────────────────────────────────

@app.route("/api/builder/apply", methods=["POST"])
def apply():
    data = request.get_json()
    required = ['full_name','email','vertical','staff_concept','track']
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error":f"Missing: {', '.join(missing)}"}), 400

    email = data['email'].lower().strip()
    conn = get_db()

    existing = conn.execute(
        "SELECT id,paid,build_stage FROM builders WHERE email=?", (email,)
    ).fetchone()

    if existing:
        conn.close()
        if existing['paid']:
            return jsonify({
                "error":"active_seat",
                "message":"You already have an active Founding Builder Seat.",
                "dashboard_url":"https://tryjoyn.me/marketplace/builder-dashboard.html"
            }), 409
        return jsonify({
            "success":True,"application_id":existing['id'],
            "returning":True,
            "message":"Application saved — continue to payment to activate your seat."
        })

    # Founding Builder logic — first 100 builders get 75% lifetime revenue share
    builder_count = conn.execute("SELECT COUNT(*) FROM builders").fetchone()[0]
    is_founding = builder_count < 100
    revenue_share = 0.75 if is_founding else 0.70

    builder_id = str(uuid.uuid4())
    conn.execute("""
        INSERT INTO builders
        (id,full_name,email,applicant_role,domain,years_experience,
         vertical,track,staff_concept,manual_task_replaced,
         build_tools,referral_source,catalogue_role_id,claimed_role_name,
         is_founding_builder,revenue_share)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        builder_id, data['full_name'], email,
        data.get('applicant_role',''), data.get('domain',''),
        data.get('years_experience',''), data['vertical'],
        data.get('track','A'), data['staff_concept'],
        data.get('manual_task_replaced',''),
        json.dumps(data.get('build_tools',[])),
        data.get('referral_source',''),
        data.get('catalogue_role_id'), data.get('claimed_role_name'),
        is_founding, revenue_share
    ))

    if data.get('catalogue_role_id'):
        conn.execute(
            "UPDATE catalogue SET builder_count=builder_count+1, status=CASE WHEN status='open' THEN 'claimed' ELSE status END WHERE id=?",
            (data['catalogue_role_id'],)
        )

    conn.commit()
    log_event(builder_id, 'applied', {'vertical':data['vertical'],'track':data.get('track','A')})
    conn.close()

    # Run Intake Agent asynchronously (non-blocking)
    intake_result = {}
    if _AGENTS_AVAILABLE:
        try:
            intake_result = intake_agent(data, DB_PATH)
            # Store intake assessment in builder notes
            conn2 = get_db()
            conn2.execute(
                "UPDATE builders SET notes=? WHERE id=?",
                (json.dumps({'intake': intake_result}), builder_id)
            )
            conn2.commit()
            conn2.close()
        except Exception as _e:
            pass  # Never fail the apply route due to agent error

    return jsonify({
        "success":True,"application_id":builder_id,
        "message":"Application received. Proceed to payment to activate your Founding Builder Seat.",
        "intake_feedback": intake_result.get('feedback',''),
        "track_recommendation": intake_result.get('track_recommendation', data.get('track','A')),
        "is_founding_builder": is_founding,
        "revenue_share": revenue_share,
        "seat_number": builder_count + 1,
    })


@app.route("/api/builder/checkout", methods=["POST"])
def checkout():
    data = request.get_json()
    app_id = data.get('application_id')
    email = (data.get('email') or '').lower().strip()

    if not app_id or not email:
        return jsonify({"error":"Missing application_id or email"}), 400

    conn = get_db()
    builder = conn.execute(
        "SELECT * FROM builders WHERE id=? AND email=?", (app_id, email)
    ).fetchone()
    conn.close()

    if not builder: return jsonify({"error":"Application not found"}), 404
    if builder['paid']:
        return jsonify({"error":"Already paid","dashboard_url":"https://tryjoyn.me/marketplace/builder-dashboard.html"}), 409

    try:
        session = stripe.checkout.Session.create(
            mode="subscription",
            customer_email=email,
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "unit_amount": 9900,
                    "recurring": {"interval":"year"},
                    "product_data": {
                        "name": "Founding Builder Seat — Joyn",
                        "description": "Annual seat on the world's first agentic AI workforce operating system. Build AI staff, earn on every hire. Founding rate locked for life."
                    }
                },
                "quantity": 1
            }],
            success_url="https://tryjoyn.me/marketplace/builder-onboarding.html?success=true&session_id={CHECKOUT_SESSION_ID}",
            cancel_url="https://tryjoyn.me/marketplace/builder-onboarding.html?step=2&cancelled=true",
            metadata={"application_id":app_id,"builder_email":email},
            subscription_data={"metadata":{"application_id":app_id}}
        )
        return jsonify({"checkout_url":session.url})
    except stripe.error.StripeError as e:
        return jsonify({"error":str(e)}), 500


@app.route("/api/stripe/webhook", methods=["POST"])
def webhook():
    payload = request.get_data()
    sig = request.headers.get("Stripe-Signature")
    try:
        event = stripe.Webhook.construct_event(payload, sig, STRIPE_WEBHOOK_SECRET)
    except Exception as e:
        return jsonify({"error":str(e)}), 400

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        app_id = session.get('metadata',{}).get('application_id')
        if app_id:
            conn = get_db()
            conn.execute("""
                UPDATE builders SET
                    paid=TRUE, stripe_customer_id=?, stripe_subscription_id=?,
                    stripe_session_id=?, paid_at=?, build_stage='paid'
                WHERE id=?
            """, (
                session.get('customer'), session.get('subscription'),
                session.get('id'), datetime.utcnow().isoformat(), app_id
            ))
            conn.commit()
            builder = conn.execute("SELECT * FROM builders WHERE id=?", (app_id,)).fetchone()
            conn.close()
            if builder:
                log_event(app_id, 'paid', {'stripe_session':session.get('id')})
                _send_welcome_email(dict(builder))

    elif event['type'] == 'customer.subscription.deleted':
        sub_id = event['data']['object']['id']
        conn = get_db()
        conn.execute("UPDATE builders SET status='inactive' WHERE stripe_subscription_id=?", (sub_id,))
        conn.commit()
        conn.close()

    return jsonify({"status":"ok"})


def _send_welcome_email(builder):
    """Never fails the webhook — all errors swallowed."""
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        claimed = builder.get('claimed_role_name') or builder.get('staff_concept','your AI staff')
        vertical = builder.get('vertical','your vertical')
        track = builder.get('track','A')
        track_label = "Build from Brief" if track == 'A' else "Franchise Your Build"

        html = f"""
        <div style="font-family:'Georgia',serif;max-width:600px;margin:0 auto;color:#111110;background:#fafaf8;padding:40px;">
        <p style="font-family:'Courier New',monospace;font-size:11px;letter-spacing:0.1em;text-transform:uppercase;color:#8B6914;margin-bottom:32px;">JOYN · FOUNDING BUILDER SEAT · CONFIRMED</p>
        <h1 style="font-size:28px;font-weight:300;margin-bottom:16px;">{builder['full_name']},</h1>
        <p style="font-size:16px;line-height:1.8;margin-bottom:24px;">Your Founding Builder Seat is confirmed. Welcome to the cohort.</p>
        <div style="border:1px solid #e8e4dc;padding:24px;margin-bottom:32px;background:#f4f1eb;">
            <p style="font-family:'Courier New',monospace;font-size:10px;text-transform:uppercase;letter-spacing:0.1em;color:#8B6914;margin-bottom:12px;">YOUR SEAT</p>
            <p style="margin:6px 0;font-size:14px;">Vertical: <strong>{vertical}</strong></p>
            <p style="margin:6px 0;font-size:14px;">Staff: <strong>{claimed}</strong></p>
            <p style="margin:6px 0;font-size:14px;">Track: <strong>{track_label}</strong></p>
            <p style="margin:6px 0;font-size:14px;">Rate: <strong>$99/year · Founding rate locked at renewal</strong></p>
        </div>
        <p style="font-family:'Courier New',monospace;font-size:10px;text-transform:uppercase;letter-spacing:0.1em;color:#8B6914;margin-bottom:16px;">YOUR NEXT STEP</p>
        <p style="font-size:15px;line-height:1.8;margin-bottom:24px;">Go to your builder dashboard. It shows exactly where you are and what to do next.</p>
        <a href="https://tryjoyn.me/marketplace/builder-dashboard.html" style="display:inline-block;font-family:'Courier New',monospace;font-size:12px;letter-spacing:0.1em;text-transform:uppercase;text-decoration:none;padding:14px 28px;background:#111110;color:#fafaf8;border:1px solid #111110;">Go to Your Dashboard →</a>
        <div style="border-top:1px solid #e8e4dc;margin-top:48px;padding-top:24px;">
            <p style="font-family:'Courier New',monospace;font-size:10px;letter-spacing:0.08em;color:#888;">Joyn · tryjoyn.me · hire@tryjoyn.me</p>
            <p style="font-family:'Courier New',monospace;font-size:10px;letter-spacing:0.08em;color:#888;">Reply to this email with any questions.</p>
        </div>
        </div>
        """

        msg = Mail(
            from_email=("hire@tryjoyn.me","Joyn · Builder Program"),
            to_emails=builder['email'],
            subject="Your Founding Builder Seat is confirmed — here's what's next",
            html_content=html
        )
        sg.send(msg)
    except Exception as e:
        print(f"[EMAIL ERROR] {builder.get('email')}: {e}")

# ── BUILDER STATUS & DASHBOARD ───────────────────────────────

@app.route("/api/builder/confirm", methods=["GET"])
def builder_confirm():
    """Look up builder by Stripe session_id after successful checkout."""
    session_id = request.args.get('session_id', '')
    if not session_id:
        return jsonify({"error": "session_id required"}), 400
    conn = get_db()
    builder = conn.execute(
        """SELECT id,full_name,email,vertical,track,staff_concept,
                  claimed_role_name,catalogue_role_id,paid,build_stage,
                  live_listing_url,hire_count,applied_at,paid_at,
                  is_founding_builder,revenue_share
           FROM builders WHERE stripe_session_id=?""",
        (session_id,)
    ).fetchone()
    conn.close()
    if not builder:
        return jsonify({"error": "Builder not found"}), 404
    b = dict(builder)
    b['status'] = b.get('build_stage', 'applied')
    b['is_founding_builder'] = bool(b.get('is_founding_builder', False))
    return jsonify(b)

@app.route("/api/builder/status", methods=["GET"])
def builder_status_query():
    """Look up builder by email or id via query params — used by dashboard."""
    email = request.args.get('email','')
    builder_id = request.args.get('id','')
    if not email and not builder_id:
        return jsonify({"error":"email or id required"}), 400
    conn = get_db()
    if builder_id:
        builder = conn.execute(
            """SELECT id,full_name,email,vertical,track,staff_concept,
                      claimed_role_name,catalogue_role_id,paid,build_stage,
                      live_listing_url,hire_count,applied_at,paid_at,
                      is_founding_builder,revenue_share,visionary_spec,reviewer_verdict
               FROM builders WHERE id=?""",
            (builder_id,)
        ).fetchone()
    else:
        builder = conn.execute(
            """SELECT id,full_name,email,vertical,track,staff_concept,
                      claimed_role_name,catalogue_role_id,paid,build_stage,
                      live_listing_url,hire_count,applied_at,paid_at,
                      is_founding_builder,revenue_share,visionary_spec,reviewer_verdict
               FROM builders WHERE email=?""",
            (email.lower().strip(),)
        ).fetchone()
    if not builder:
        conn.close()
        return jsonify({"error":"Builder not found"}), 404
    b = dict(builder)
    b['status'] = b.get('build_stage','applied')
    b['active_hirers'] = b.get('hire_count', 0)
    b['is_founding_builder'] = bool(b.get('is_founding_builder', False))
    if b.get('visionary_spec'):
        try: b['visionary_spec'] = json.loads(b['visionary_spec'])
        except: pass
    if b.get('reviewer_verdict'):
        try: b['review_result'] = json.loads(b['reviewer_verdict'])
        except: pass
    conn.close()
    return jsonify(b)

@app.route("/api/builder/status/<email>", methods=["GET"])
def builder_status(email):
    conn = get_db()
    builder = conn.execute(
        """SELECT id,full_name,email,vertical,track,staff_concept,
                  claimed_role_name,catalogue_role_id,paid,build_stage,
                  live_listing_url,hire_count,applied_at,paid_at
           FROM builders WHERE email=? AND status='active'""",
        (email.lower().strip(),)
    ).fetchone()

    if not builder:
        conn.close()
        return jsonify({"error":"Builder not found"}), 404

    b = dict(builder)

    # If has a catalogue role, include it
    if b.get('catalogue_role_id'):
        role_row = conn.execute(
            "SELECT id,name,role,mode,vertical,sub,complexity,weeks,tools,pattern,builder_guidance,calibration_questions FROM catalogue WHERE id=?",
            (b['catalogue_role_id'],)
        ).fetchone()
        if role_row:
            rd = dict(role_row)
            rd = parse_json_fields(rd, ['tools','calibration_questions'])
            try: rd['builder_guidance'] = json.loads(rd.get('builder_guidance') or '{}')
            except: rd['builder_guidance'] = {}
            b['catalogue_role'] = rd

    conn.close()

    stages = ['applied','paid','briefing','brief_approved','building',
              'submitted','under_review','conditional_pass','revising','deployed','earning']
    current_idx = stages.index(b['build_stage']) if b['build_stage'] in stages else 0

    b['stage_index'] = current_idx
    b['stages'] = stages
    b['next_action'] = _next_action(b['build_stage'])
    b['next_action_url'] = _next_action_url(b['build_stage'])
    b['resources'] = _stage_resources(b['build_stage'], b)

    return jsonify(b)

def _next_action(stage):
    return {
        'applied': 'Complete payment to activate your Founding Builder Seat',
        'paid': 'Complete your Creator Brief to lock your staff spec',
        'briefing': 'Continue your Creator Brief — your progress is saved',
        'brief_approved': 'Start building using your approved Visionary Spec',
        'building': 'Build your AI staff and return when ready to submit',
        'submitted': 'Your submission is under review — verdict within 48 hours',
        'under_review': 'The Reviewer Agent is evaluating your submission gate by gate',
        'conditional_pass': 'Review your verdict and resolve the flagged gates',
        'revising': 'Revise your submission and resubmit the failed gates',
        'deployed': 'Your staff is live — monitor hire requests and calibration feedback',
        'earning': 'Your staff is earning — use calibration feedback to improve it'
    }.get(stage, 'Continue your build')

def _next_action_url(stage):
    return {
        'applied': 'builder-onboarding.html?step=2',
        'paid': 'builder-onboarding.html?step=brief',
        'briefing': 'builder-onboarding.html?step=brief',
        'brief_approved': 'builder-dashboard.html#resources',
        'building': 'builder-dashboard.html#resources',
        'submitted': 'builder-dashboard.html#submission',
        'under_review': 'builder-dashboard.html#submission',
        'conditional_pass': 'builder-dashboard.html#verdict',
        'revising': 'builder-dashboard.html#verdict',
        'deployed': 'builder-dashboard.html#performance',
        'earning': 'builder-dashboard.html#performance'
    }.get(stage, 'builder-dashboard.html')

def _stage_resources(stage, builder):
    """Returns resources relevant to current build stage only."""
    track = builder.get('track','A')
    vertical = builder.get('vertical','')
    role = builder.get('catalogue_role',{})
    tools = role.get('tools',[]) if role else []
    tools_str = ', '.join(tools) if tools else 'Manus, Emergent'

    base = {
        'paid': [
            {"title":"Creator Brief Template","description":"Complete this before building anything","url":"https://tryjoyn.me/marketplace/creator-studio.html#brief","type":"action"},
            {"title":"The Bar — Deployment Standard","description":"Five gates your staff must pass","url":"https://tryjoyn.me/docs/the-bar-v1.docx","type":"doc"},
            {"title":"Design Specification","description":"All listing pages must follow this exactly","url":"https://tryjoyn.me/marketplace/creator-studio.html#design","type":"doc"}
        ],
        'brief_approved': [
            {"title":f"Build Prompt for {builder.get('claimed_role_name','your role')}","description":f"Pre-populated prompt for {tools_str}","url":"builder-dashboard.html#build-prompt","type":"tool"},
            {"title":"Design Specification","description":"All listing pages must follow this exactly","url":"https://tryjoyn.me/marketplace/creator-studio.html#design","type":"doc"},
            {"title":"Example Live Listing","description":"See Iris — the reference implementation","url":"https://tryjoyn.me/marketplace/iris-insurance-regulatory.html","type":"example"}
        ],
        'building': [
            {"title":f"Build Prompt for {builder.get('claimed_role_name','your role')}","description":f"Pre-populated prompt for {tools_str}","url":"builder-dashboard.html#build-prompt","type":"tool"},
            {"title":"Pre-Flight Check","description":"Run this before submitting to The Bar","url":"builder-dashboard.html#preflight","type":"action"},
            {"title":"The Bar — What Pass Looks Like","description":"Gate-by-gate examples of passing submissions","url":"https://tryjoyn.me/docs/the-bar-v1.docx","type":"doc"}
        ],
        'conditional_pass': [
            {"title":"Your Reviewer Verdict","description":"Gate-by-gate feedback with specific fixes","url":"builder-dashboard.html#verdict","type":"action"},
            {"title":"Resubmit Guide","description":"How to resubmit only the failed gates","url":"https://tryjoyn.me/docs/the-bar-v1.docx#resubmit","type":"doc"}
        ],
        'deployed': [
            {"title":"Your Live Listing","description":builder.get('live_listing_url',''),"url":builder.get('live_listing_url','#'),"type":"live"},
            {"title":"Calibration Feedback","description":"Review hirer feedback to improve your staff","url":"builder-dashboard.html#calibration","type":"data"}
        ]
    }
    return base.get(stage, base.get('paid',[]))


# ── BRIEF ────────────────────────────────────────────────────

@app.route("/api/builder/brief", methods=["POST"])
def save_brief():
    data = request.get_json()
    builder_id = data.get('builder_id')
    answers = data.get('answers',{})
    completed = data.get('completed', False)

    if not builder_id:
        return jsonify({"error":"Missing builder_id"}), 400

    conn = get_db()
    existing = conn.execute(
        "SELECT id FROM brief_sessions WHERE builder_id=?", (builder_id,)
    ).fetchone()

    now = datetime.utcnow().isoformat()
    if existing:
        conn.execute(
            "UPDATE brief_sessions SET answers=?, completed=?, last_saved=? WHERE builder_id=?",
            (json.dumps(answers), completed, now, builder_id)
        )
    else:
        conn.execute(
            "INSERT INTO brief_sessions (id,builder_id,answers,completed,last_saved) VALUES (?,?,?,?,?)",
            (str(uuid.uuid4()), builder_id, json.dumps(answers), completed, now)
        )

    if completed:
        conn.execute(
            "UPDATE builders SET build_stage='brief_approved', brief_data=? WHERE id=?",
            (json.dumps(answers), builder_id)
        )
        log_event(builder_id, 'brief_approved', {})
        conn.commit()
        conn.close()

        # Run Architect Agent to generate Visionary Spec
        visionary_spec = {}
        if _AGENTS_AVAILABLE:
            try:
                conn3 = get_db()
                builder_row = conn3.execute("SELECT * FROM builders WHERE id=?", (builder_id,)).fetchone()
                conn3.close()
                if builder_row:
                    visionary_spec = architect_agent(answers, dict(builder_row))
                    conn4 = get_db()
                    conn4.execute(
                        "UPDATE builders SET visionary_spec=?, build_stage='building' WHERE id=?",
                        (json.dumps(visionary_spec), builder_id)
                    )
                    conn4.commit()
                    conn4.close()
                    log_event(builder_id, 'visionary_spec_generated', {'model': visionary_spec.get('_meta',{}).get('model','')})
            except Exception as _e:
                pass  # Never fail the brief route due to agent error

        return jsonify({"saved":True,"completed":True,"visionary_spec_generated": bool(visionary_spec), "visionary_spec": visionary_spec})

    conn.commit()
    conn.close()
    return jsonify({"saved":True,"completed":completed})


@app.route("/api/builder/brief/<builder_id>", methods=["GET"])
def get_brief(builder_id):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM brief_sessions WHERE builder_id=?", (builder_id,)
    ).fetchone()
    conn.close()
    if not row: return jsonify({"answers":{},"completed":False})
    r = dict(row)
    r['answers'] = json.loads(r.get('answers') or '{}')
    return jsonify(r)


# ── PRE-FLIGHT CHECK ─────────────────────────────────────────

@app.route("/api/builder/preflight", methods=["POST"])
def preflight():
    """
    Automated pre-flight check before Bar submission.
    Checks against The Bar's five gates without requiring Reviewer Agent.
    Returns gate-by-gate pass/fail/warning with specific fixes.
    """
    data = request.get_json()
    builder_id = data.get('builder_id')
    submission = data.get('submission',{})

    if not builder_id:
        return jsonify({"error":"Missing builder_id"}), 400

    results = []
    overall = 'pass'

    # Gate 01 — Role Clarity
    role_def = submission.get('role_definition','')
    word_count = len(role_def.split())
    if not role_def:
        results.append({"gate":"01","check":"Role definition present","status":"fail","detail":"Role definition is required. Complete your Creator Brief first."})
        overall = 'fail'
    elif word_count > 30:
        results.append({"gate":"01","check":"Role definition single sentence","status":"warning","detail":f"Your role definition is {word_count} words. It should be expressible in one sentence (under 20 words). If you need more words, the role is not specific enough."})
        if overall == 'pass': overall = 'warning'
    else:
        results.append({"gate":"01","check":"Role definition single sentence","status":"pass","detail":""})

    # Gate 02 — Output Standard
    outputs = submission.get('named_outputs',[])
    if not outputs:
        results.append({"gate":"02","check":"Named outputs present","status":"fail","detail":"At least two named outputs are required. Each must have a name, format, and trigger condition."})
        overall = 'fail'
    else:
        unnamed = [o for o in outputs if not o.get('name') or not o.get('format')]
        if unnamed:
            results.append({"gate":"02","check":"All outputs named and formatted","status":"fail","detail":f"{len(unnamed)} output(s) are missing a name or format. Every output must be fully specified."})
            overall = 'fail'
        else:
            results.append({"gate":"02","check":"Named outputs complete","status":"pass","detail":""})

        no_trigger = [o for o in outputs if not o.get('trigger')]
        if no_trigger:
            results.append({"gate":"02","check":"Output triggers defined","status":"warning","detail":f"{len(no_trigger)} output(s) have no trigger condition defined. Specify what causes each output to be produced."})
            if overall == 'pass': overall = 'warning'
        else:
            results.append({"gate":"02","check":"Output triggers defined","status":"pass","detail":""})

    # Gate 03 — Hirer Experience
    escalation_def = submission.get('escalation_definition','')
    intervention_points = submission.get('intervention_points',[])
    mode = submission.get('mode','autonomous')

    if mode == 'supervised' and not intervention_points:
        results.append({"gate":"03","check":"Supervised intervention points defined","status":"fail","detail":"Supervised staff must define explicit intervention points. List each point where the practitioner must review or approve before the staff proceeds."})
        overall = 'fail'
    elif mode == 'autonomous' and not escalation_def:
        results.append({"gate":"03","check":"Escalation conditions defined","status":"warning","detail":"Autonomous staff should define when it escalates to the hirer. What conditions trigger escalation? What single question does it ask?"})
        if overall == 'pass': overall = 'warning'
    else:
        results.append({"gate":"03","check":"Hirer interaction model defined","status":"pass","detail":""})

    # Gate 04 — Failure Handling
    failure_paths = submission.get('failure_paths',[])
    if not failure_paths:
        results.append({"gate":"04","check":"Failure paths defined","status":"fail","detail":"Failure handling is required. Define at least three failure scenarios: (1) declined/missing data, (2) ambiguous input, (3) out-of-scope request. Show how the staff handles each without hallucinating."})
        overall = 'fail'
    elif len(failure_paths) < 3:
        results.append({"gate":"04","check":"Three failure scenarios covered","status":"warning","detail":f"You have {len(failure_paths)} failure scenario(s). The Bar requires at least three: declined data, ambiguous input, and scope change."})
        if overall == 'pass': overall = 'warning'
    else:
        results.append({"gate":"04","check":"Failure paths defined","status":"pass","detail":""})

    # Gate 05 — Calibration Architecture
    calibration_questions = submission.get('calibration_questions',[])
    if not calibration_questions:
        results.append({"gate":"05","check":"Calibration questions present","status":"fail","detail":"A calibration mechanism is required. Define at least three closing questions asked after each engagement. Show how responses are stored and carried forward."})
        overall = 'fail'
    elif len(calibration_questions) < 3:
        results.append({"gate":"05","check":"Minimum three calibration questions","status":"warning","detail":f"You have {len(calibration_questions)} calibration question(s). The Bar requires at least three."})
        if overall == 'pass': overall = 'warning'
    else:
        results.append({"gate":"05","check":"Calibration architecture complete","status":"pass","detail":""})

    # Output specimen check
    specimen = submission.get('output_specimen')
    if not specimen:
        results.append({"gate":"02","check":"Output specimen provided","status":"fail","detail":"At least one real output specimen is required — a completed artifact from a test run, not a template."})
        overall = 'fail'

    # Design spec check (if listing HTML provided)
    listing_html = submission.get('listing_html','')
    if listing_html:
        design_fails = []
        if 'border-radius' in listing_html: design_fails.append("border-radius found — must be removed")
        if 'box-shadow' in listing_html: design_fails.append("box-shadow found — must be removed")
        import re
        hex_pattern = re.compile(r'(?<!var\()#[0-9a-fA-F]{3,6}(?!\))')
        hex_matches = hex_pattern.findall(listing_html)
        valid_hex = ['#fafaf8','#111110','#3f3f3e','#e8e4dc','#d0ccc4','#f4f1eb','#b8902a','#8B6914','#7a5c10']
        invalid_hex = [h for h in set(hex_matches) if h.lower() not in [v.lower() for v in valid_hex]]
        if invalid_hex: design_fails.append(f"Hardcoded hex colours found: {', '.join(invalid_hex[:5])} — use CSS custom properties only")
        for term in ['agent','bot','activate','subscribe','cancel']:
            if term in listing_html.lower(): design_fails.append(f"Forbidden term '{term}' found in listing HTML")

        if design_fails:
            results.append({"gate":"design","check":"Listing page design compliance","status":"fail","detail":"Design spec violations: " + "; ".join(design_fails)})
            overall = 'fail'
        else:
            results.append({"gate":"design","check":"Listing page design compliance","status":"pass","detail":""})

    # Save results
    conn = get_db()
    check_id = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO preflight_checks (id,builder_id,check_date,results,overall_status) VALUES (?,?,?,?,?)",
        (check_id, builder_id, datetime.utcnow().isoformat(), json.dumps(results), overall)
    )
    conn.execute(
        "UPDATE builders SET preflight_results=? WHERE id=?",
        (json.dumps({"results":results,"overall":overall,"check_id":check_id}), builder_id)
    )
    if overall == 'pass':
        conn.execute(
            "UPDATE builders SET build_stage='submitted' WHERE id=? AND build_stage='building'",
            (builder_id,)
        )
        log_event(builder_id, 'submitted', {"preflight":overall})
    conn.commit()
    conn.close()

    pass_count = len([r for r in results if r['status']=='pass'])
    fail_count = len([r for r in results if r['status']=='fail'])
    warn_count = len([r for r in results if r['status']=='warning'])

    return jsonify({
        "overall_status": overall,
        "results": results,
        "summary": {"pass":pass_count,"fail":fail_count,"warning":warn_count},
        "can_submit": overall in ('pass','warning'),
        "message": {
            "pass": "All gates cleared. Your submission is ready for The Bar.",
            "warning": f"{warn_count} warning(s) found. You can submit now, but addressing these warnings will improve your chances of passing The Bar.",
            "fail": f"{fail_count} gate(s) failed. Fix these before submitting — The Bar will reject submissions with these issues."
        }.get(overall)
    })


# ── BUILD PROMPT ────────────────────────────────────────────

@app.route("/api/builder/build-prompt", methods=["GET"])
def get_build_prompt():
    builder_id = request.args.get('id')
    if not builder_id:
        return jsonify({"error": "builder_id required"}), 400
    conn = get_db()
    row = conn.execute(
        "SELECT b.*, c.name as role_name, c.role as role_title, c.vertical as role_vertical, "
        "c.mode as role_mode, c.pain as target_pain, c.tasks as core_tasks, "
        "c.outputs as named_outputs, c.calibration_questions, "
        "c.builder_guidance, c.weeks as estimated_weeks "
        "FROM builders b LEFT JOIN catalogue c ON b.catalogue_role_id = c.id "
        "WHERE b.id = ?",
        (builder_id,)
    ).fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "Builder not found"}), 404

    b = dict(row)
    role_name = b.get('role_name') or b.get('claimed_role_name') or 'your AI staff'
    role_title = b.get('role_title') or ''
    vertical = b.get('role_vertical') or b.get('vertical') or ''
    mode = b.get('role_mode') or 'autonomous'
    pain = b.get('target_pain') or ''

    try: tasks = json.loads(b.get('tasks') or '[]')
    except: tasks = []
    try: outputs = json.loads(b.get('outputs') or '[]')
    except: outputs = []
    try: calibration = json.loads(b.get('calibration_questions') or '[]')
    except: calibration = []
    try: guidance = json.loads(b.get('builder_guidance') or '{}')
    except: guidance = {}

    tasks_str = '\n'.join([f'  - {t}' for t in tasks]) if tasks else '  - (complete the Creator Brief to see specific tasks)'
    outputs_str = '\n'.join([
        f'  - {o.get("name",o) if isinstance(o,dict) else o}: {o.get("format","") if isinstance(o,dict) else ""} (trigger: {o.get("trigger","") if isinstance(o,dict) else ""})'
        for o in outputs
    ]) if outputs else '  - (complete the Creator Brief to define named outputs)'
    calibration_str = '\n'.join([f'  {i+1}. {q}' for i,q in enumerate(calibration)]) if calibration else '  (complete the Creator Brief to see calibration questions)'
    hardest = guidance.get('hardest_part', 'Defining the exact named outputs and their trigger conditions.')
    data_sources = guidance.get('key_data_sources', 'Domain-specific data sources relevant to your vertical.')
    weeks = b.get('estimated_weeks', '2-4')

    prompt = f"""You are building {role_name} \u2014 {role_title}.
This is an AI staff for the Joyn marketplace. It will be hired by businesses in the {vertical} vertical.

CONTEXT
- Mode: {mode.upper()} (the staff {'acts without human approval' if mode == 'autonomous' else 'presents recommendations for human sign-off'})
- The problem it solves: {pain}
- Estimated build time: {weeks} weeks
- Vertical: {vertical}

CORE TASKS
{tasks_str}

NAMED OUTPUTS (what the staff must produce)
{outputs_str}

CALIBRATION QUESTIONS (the hirer answers these at onboarding)
{calibration_str}

BUILD REQUIREMENTS
1. The staff must produce NAMED, SCHEDULED outputs \u2014 not just answers to questions
2. Onboarding must take under 30 minutes for the hirer
3. Every failure scenario must have a defined response (at least 3 scenarios)
4. The staff must improve over time through hirer feedback
5. The hirer experience must be consistent and professional

DESIGN STANDARD
- Follow the Joyn design spec (JOYN-DESIGN-SPEC.md in the repository)
- Study Iris (iris-insurance-regulatory.html) as the reference implementation
- Tools are open. Standards are closed.
- Terminology: never use 'agent', 'bot', 'activate', 'subscribe', 'cancel'

KEY DATA SOURCES
{data_sources}

HARDEST PART OF THIS BUILD
{hardest}

START HERE
Define the three most important named outputs for {role_name}. For each output, specify:
1. Name (what the hirer calls it)
2. Format (email, PDF, Slack message, dashboard, etc.)
3. Trigger (what causes it to be produced)
4. Schedule (daily, weekly, on-demand, etc.)
5. Who receives it

Once you have defined the named outputs, build the workflow that produces them."""

    return jsonify({"prompt": prompt, "role_name": role_name, "vertical": vertical})


# ── STAGE UPDATES ────────────────────────────────────────────

@app.route("/api/builder/stage", methods=["POST"])
def update_stage():
    data = request.get_json()
    builder_id = data.get('builder_id')
    new_stage = data.get('stage')

    valid_stages = ['applied','paid','briefing','brief_approved','building',
                    'submitted','under_review','conditional_pass','revising','deployed','earning']

    if not builder_id or new_stage not in valid_stages:
        return jsonify({"error":"Invalid builder_id or stage"}), 400

    conn = get_db()
    conn.execute("UPDATE builders SET build_stage=? WHERE id=?", (new_stage, builder_id))
    if new_stage == 'deployed':
        listing_url = data.get('listing_url','')
        if listing_url:
            conn.execute("UPDATE builders SET live_listing_url=? WHERE id=?", (listing_url, builder_id))
            conn.execute(
                "UPDATE catalogue SET status='live', live_count=live_count+1 WHERE id=(SELECT catalogue_role_id FROM builders WHERE id=?)",
                (builder_id,)
            )
    conn.commit()
    conn.close()
    log_event(builder_id, f'stage_{new_stage}', data)
    return jsonify({"success":True,"stage":new_stage})


# ── ADMIN: LOAD CATALOGUE EXTENSIONS ────────────────────────────────────────
# Protected by ADMIN_SECRET env var — never expose without auth
@app.route("/api/admin/load-extensions", methods=["POST"])
def load_extensions():
    """Load additional catalogue roles from extensions.json or a posted JSON array.
    Called after generate_extensions.py completes to expand the catalogue without redeployment.
    Requires ADMIN_SECRET header for protection.
    """
    admin_secret = os.environ.get('ADMIN_SECRET', '')
    if admin_secret:
        provided = request.headers.get('X-Admin-Secret', '')
        if provided != admin_secret:
            return jsonify({'error': 'Unauthorized'}), 401

    # Accept roles from request body OR from extensions.json file
    data = request.get_json(silent=True) or {}
    roles = data.get('roles')

    if not roles:
        # Try loading from extensions.json in the same directory
        ext_path = os.path.join(os.path.dirname(__file__), 'extensions.json')
        if not os.path.exists(ext_path):
            return jsonify({'error': 'No roles provided and extensions.json not found'}), 400
        with open(ext_path) as f:
            roles = json.load(f)

    if not isinstance(roles, list):
        return jsonify({'error': 'roles must be a JSON array'}), 400

    conn = get_db()
    inserted = 0
    skipped = 0
    errors = []

    for role in roles:
        try:
            role_id = role.get('id')
            if not role_id:
                skipped += 1
                continue

            # Check if already exists
            existing = conn.execute('SELECT id FROM catalogue WHERE id=?', (role_id,)).fetchone()
            if existing:
                skipped += 1
                continue

            # Normalise JSON fields
            def jdump(v):
                if isinstance(v, (list, dict)): return json.dumps(v)
                return v or ''

            status = role.get('status', 'open')
            if status not in ('open', 'claimed', 'live'): status = 'open'
            track = role.get('track', 'A')
            if track not in ('A', 'B'): track = 'A'
            complexity = role.get('build_complexity') or role.get('complexity', 'moderate')
            if complexity not in ('simple', 'moderate', 'complex'): complexity = 'moderate'

            conn.execute("""
                INSERT INTO catalogue
                (id, name, role, mode, vertical, sub, hirer, pain, tasks, outputs, metrics,
                 complexity, weeks, tools, pattern, moat, calibration_questions, builder_guidance,
                 status, track, live_count)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,0)
            """, (
                role_id,
                role.get('name', ''),
                role.get('role', ''),
                role.get('mode', 'autonomous'),
                role.get('vertical', ''),
                role.get('sub_vertical') or role.get('sub', ''),
                role.get('target_hirer') or role.get('hirer', ''),
                role.get('target_pain') or role.get('pain', ''),
                jdump(role.get('core_tasks') or role.get('tasks', [])),
                jdump(role.get('named_outputs') or role.get('outputs', [])),
                jdump(role.get('success_metrics') or role.get('metrics', [])),
                complexity,
                role.get('estimated_weeks') or role.get('weeks', '2-4'),
                jdump(role.get('recommended_tools') or role.get('tools', [])),
                role.get('architecture_pattern') or role.get('pattern', ''),
                role.get('moat_asset') or role.get('moat', ''),
                jdump(role.get('calibration_questions', [])),
                jdump(role.get('builder_guidance', {})),
                status,
                track,
            ))
            inserted += 1
        except Exception as e:
            errors.append({'id': role.get('id', '?'), 'error': str(e)})

    conn.commit()
    total = conn.execute('SELECT COUNT(*) FROM catalogue').fetchone()[0]
    conn.close()

    return jsonify({
        'success': True,
        'inserted': inserted,
        'skipped': skipped,
        'errors': errors[:10],  # Cap error list
        'total_catalogue': total
    })


def init_db():
    conn = get_db()
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
        CREATE TABLE IF NOT EXISTS builders (
            id TEXT PRIMARY KEY,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            applicant_role TEXT,
            domain TEXT,
            years_experience TEXT,
            vertical TEXT,
            track TEXT DEFAULT 'A' CHECK(track IN ('A','B')),
            staff_concept TEXT,
            manual_task_replaced TEXT,
            build_tools TEXT,
            referral_source TEXT,
            catalogue_role_id TEXT,
            claimed_role_name TEXT,
            paid BOOLEAN DEFAULT FALSE,
            stripe_customer_id TEXT,
            stripe_subscription_id TEXT,
            stripe_session_id TEXT,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            paid_at TIMESTAMP,
            build_stage TEXT DEFAULT 'applied' CHECK(build_stage IN (
                'applied','paid','briefing','brief_approved',
                'building','submitted','under_review',
                'conditional_pass','revising','deployed','earning'
            )),
            brief_data TEXT,
            visionary_spec TEXT,
            submission_data TEXT,
            reviewer_verdict TEXT,
            preflight_results TEXT,
            live_listing_url TEXT,
            hire_count INTEGER DEFAULT 0,
            notes TEXT,
            is_founding_builder BOOLEAN DEFAULT FALSE,
            revenue_share REAL DEFAULT 0.70,
            status TEXT DEFAULT 'active' CHECK(status IN ('active','inactive','suspended'))
        );
        CREATE TABLE IF NOT EXISTS builder_events (
            id TEXT PRIMARY KEY,
            builder_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            event_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (builder_id) REFERENCES builders(id)
        );
        CREATE TABLE IF NOT EXISTS brief_sessions (
            id TEXT PRIMARY KEY,
            builder_id TEXT NOT NULL,
            answers TEXT,
            completed BOOLEAN DEFAULT FALSE,
            last_saved TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (builder_id) REFERENCES builders(id)
        );
        CREATE TABLE IF NOT EXISTS preflight_checks (
            id TEXT PRIMARY KEY,
            builder_id TEXT NOT NULL,
            check_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            results TEXT NOT NULL,
            overall_status TEXT CHECK(overall_status IN ('pass','fail','warning')),
            FOREIGN KEY (builder_id) REFERENCES builders(id)
        );
        CREATE INDEX IF NOT EXISTS idx_builders_email ON builders(email);
        CREATE INDEX IF NOT EXISTS idx_builders_stage ON builders(build_stage);
        CREATE INDEX IF NOT EXISTS idx_catalogue_vertical ON catalogue(vertical);
        CREATE INDEX IF NOT EXISTS idx_catalogue_status ON catalogue(status);
        CREATE INDEX IF NOT EXISTS idx_events_builder ON builder_events(builder_id);
    """)
    conn.commit()
    conn.close()

with app.app_context():
    init_db()

# Run migrate + seed in a background thread so gunicorn can accept
# the Railway healthcheck immediately without timing out.
def _startup_tasks():
    import time, subprocess, sys
    time.sleep(2)  # brief pause to let gunicorn bind the port
    _dir = os.path.dirname(os.path.abspath(__file__)) or '.'
    try:
        subprocess.run([sys.executable, 'migrate.py'], check=True, capture_output=True, cwd=_dir)
        print('[STARTUP] migrate complete')
    except Exception as _e:
        print(f'[STARTUP WARNING] migrate: {_e}')
    try:
        subprocess.run([sys.executable, 'seed_catalogue.py'], check=True, capture_output=True, cwd=_dir)
        print('[STARTUP] seed complete')
    except Exception as _e:
        print(f'[STARTUP WARNING] seed: {_e}')

import threading as _threading
_threading.Thread(target=_startup_tasks, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=False)
