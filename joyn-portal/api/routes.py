import json
import secrets
import string
import stripe
from flask import Blueprint, request, jsonify, current_app, g
from flask_cors import cross_origin
from data.db import query_one, query, insert, execute_commit, rows_to_list, row_to_dict
from auth.helpers import api_login_required, portal_secret_required, hash_password
from staff_common import STAFF_REGISTRY, send_welcome_email, send_staff_added_email

api_bp = Blueprint('api', __name__, url_prefix='/api')


# ── Client: staff ──────────────────────────────────────────────

@api_bp.route('/client/staff')
@api_login_required
def client_staff():
    rows = query(
        "SELECT * FROM hired_staff WHERE client_id=? AND status != 'let-go' ORDER BY hired_at ASC",
        (g.client_id,)
    )
    return jsonify(rows_to_list(rows))


# ── Client: activity ───────────────────────────────────────────

@api_bp.route('/client/activity')
@api_login_required
def client_activity():
    limit = min(int(request.args.get('limit', 20)), 100)
    page  = max(int(request.args.get('page', 1)), 1)
    offset = (page - 1) * limit
    rows = query(
        'SELECT * FROM activity_log WHERE client_id=? ORDER BY timestamp DESC LIMIT ? OFFSET ?',
        (g.client_id, limit, offset)
    )
    return jsonify(rows_to_list(rows))


# ── Client: outputs ────────────────────────────────────────────

@api_bp.route('/client/outputs')
@api_login_required
def client_outputs():
    limit = min(int(request.args.get('limit', 20)), 100)
    page  = max(int(request.args.get('page', 1)), 1)
    offset = (page - 1) * limit
    rows = query(
        'SELECT * FROM outputs WHERE client_id=? ORDER BY delivered_at DESC LIMIT ? OFFSET ?',
        (g.client_id, limit, offset)
    )
    return jsonify(rows_to_list(rows))


# ── Staff Iris: activity ───────────────────────────────────────

@api_bp.route('/staff/iris/activity')
@api_login_required
def iris_activity():
    limit = min(int(request.args.get('limit', 50)), 100)
    rows = query(
        "SELECT * FROM activity_log WHERE client_id=? AND staff_slug='iris' ORDER BY timestamp DESC LIMIT ?",
        (g.client_id, limit)
    )
    return jsonify(rows_to_list(rows))


# ── Staff Iris: outputs ────────────────────────────────────────

@api_bp.route('/staff/iris/outputs')
@api_login_required
def iris_outputs():
    rows = query(
        "SELECT * FROM outputs WHERE client_id=? AND staff_slug='iris' ORDER BY delivered_at DESC",
        (g.client_id,)
    )
    return jsonify(rows_to_list(rows))


# ── Staff Iris: update settings ────────────────────────────────

@api_bp.route('/staff/iris/settings', methods=['POST'])
@api_login_required
def iris_settings():
    data = request.get_json(silent=True) or {}
    staff = query_one(
        "SELECT * FROM hired_staff WHERE client_id=? AND staff_slug='iris'",
        (g.client_id,)
    )
    if not staff:
        return jsonify({'error': 'Iris not found'}), 404

    current_settings = {}
    if staff['settings']:
        try:
            current_settings = json.loads(staff['settings'])
        except (ValueError, TypeError):
            pass

    allowed = ['alert_email', 'alert_frequency', 'status', 'jurisdictions']
    for key in allowed:
        if key in data:
            current_settings[key] = data[key]

    execute_commit(
        "UPDATE hired_staff SET settings=? WHERE client_id=? AND staff_slug='iris'",
        (json.dumps(current_settings), g.client_id)
    )
    return jsonify({'ok': True, 'settings': current_settings})


# ── External: log activity (called by Iris on Railway) ─────────

@api_bp.route('/log/activity', methods=['POST'])
@portal_secret_required
def log_activity():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'JSON body required'}), 400

    required = ['client_id', 'staff_name', 'action_description']
    missing = [k for k in required if not data.get(k)]
    if missing:
        return jsonify({'error': f'Missing fields: {", ".join(missing)}'}), 400

    client = query_one('SELECT id FROM clients WHERE id=?', (data['client_id'],))
    if not client:
        return jsonify({'error': 'Client not found'}), 404

    slug = data.get('staff_slug') or data['staff_name'].lower().replace(' ', '-')

    row_id = insert(
        '''INSERT INTO activity_log
           (client_id, staff_name, staff_slug, action_type, action_description, status)
           VALUES (?,?,?,?,?,?)''',
        (
            data['client_id'],
            data['staff_name'],
            slug,
            data.get('action_type', 'action'),
            data['action_description'],
            data.get('status', 'complete'),
        )
    )
    return jsonify({'ok': True, 'id': row_id}), 201


# ── External: log output (called by Iris on Railway) ───────────

@api_bp.route('/log/output', methods=['POST'])
@portal_secret_required
def log_output():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'JSON body required'}), 400

    required = ['client_id', 'staff_name', 'title']
    missing = [k for k in required if not data.get(k)]
    if missing:
        return jsonify({'error': f'Missing fields: {", ".join(missing)}'}), 400

    client = query_one('SELECT id FROM clients WHERE id=?', (data['client_id'],))
    if not client:
        return jsonify({'error': 'Client not found'}), 404

    slug = data.get('staff_slug') or data['staff_name'].lower().replace(' ', '-')

    row_id = insert(
        '''INSERT INTO outputs
           (client_id, staff_name, staff_slug, output_type, title, summary, severity, full_content)
           VALUES (?,?,?,?,?,?,?,?)''',
        (
            data['client_id'],
            data['staff_name'],
            slug,
            data.get('output_type', 'briefing'),
            data['title'],
            data.get('summary'),
            data.get('severity', 'info'),
            data.get('full_content'),
        )
    )
    return jsonify({'ok': True, 'id': row_id}), 201


# ── Public: register client (called from any hire form) ───────────

@api_bp.route('/register', methods=['POST', 'OPTIONS'])
@cross_origin(origins=["https://tryjoyn.me", "https://www.tryjoyn.me"],
              supports_credentials=True,
              allow_headers=["Content-Type"])
def register():
    if request.method == 'OPTIONS':
        return '', 204
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'success': False, 'error': 'JSON body required'}), 400

    name      = (data.get('name') or '').strip()
    email     = (data.get('email') or '').strip().lower()
    firm_name = (data.get('firm_name') or '').strip()

    # staff_slug defaults to 'iris' for backward compatibility
    staff_slug = (data.get('staff_slug') or 'iris').strip().lower()

    # For Iris, states is still required; for other staff it is optional
    states = (data.get('states') or '').strip()

    if not all([name, email, firm_name]):
        return jsonify({'success': False, 'error': 'name, email, and firm_name are required'}), 400

    if staff_slug == 'iris' and not states:
        return jsonify({'success': False, 'error': 'states is required for Iris'}), 400

    staff_meta = STAFF_REGISTRY.get(staff_slug)
    if not staff_meta:
        return jsonify({'success': False, 'error': f'Unknown staff_slug: {staff_slug}'}), 400

    existing = query_one('SELECT id FROM clients WHERE email=?', (email,))

    # ── EXISTING ACCOUNT: add staff, never create a duplicate ──────────────
    if existing:
        client_id = existing['id']

        already_hired = query_one(
            "SELECT id FROM hired_staff WHERE client_id=? AND staff_slug=?",
            (client_id, staff_slug)
        )
        if already_hired:
            return jsonify({
                'success': False,
                'error': f'{staff_meta["name"]} is already active on this account'
            }), 409

        reserved = {'name', 'email', 'firm_name', 'staff_slug', 'states'}
        extra_settings = {k: v for k, v in data.items() if k not in reserved}
        if staff_slug == 'iris':
            state_list = [s.strip() for s in states.split(',') if s.strip()]
            extra_settings['jurisdictions'] = state_list

        insert(
            '''INSERT INTO hired_staff
               (client_id, staff_name, staff_slug, vertical, mode, settings)
               VALUES (?,?,?,?,?,?)''',
            (
                client_id,
                staff_meta['name'],
                staff_slug,
                staff_meta['vertical'],
                staff_meta['mode'],
                json.dumps(extra_settings),
            )
        )

        send_staff_added_email(
            app_config=current_app.config,
            logger=current_app.logger,
            to_email=email,
            name=name,
            firm_name=firm_name,
            staff_slug=staff_slug,
            staff_name=staff_meta['name'],
            states=states,
        )

        current_app.logger.info(
            f'Staff added to existing account: {email} ({firm_name}) — staff: {staff_slug}'
        )
        return jsonify({'success': True, 'message': 'Staff added to existing account'}), 200

    # ── NEW ACCOUNT ────────────────────────────────────────────────────────
    alphabet = string.ascii_letters + string.digits
    temp_password = ''.join(secrets.choice(alphabet) for _ in range(12))

    client_id = insert(
        '''INSERT INTO clients
           (email, password_hash, company_name, primary_contact_name,
            states, first_login, subscription_status)
           VALUES (?,?,?,?,?,1,'trial')''',
        (email, hash_password(temp_password), firm_name, name, states or None)
    )

    reserved = {'name', 'email', 'firm_name', 'staff_slug', 'states'}
    extra_settings = {k: v for k, v in data.items() if k not in reserved}

    if staff_slug == 'iris':
        state_list = [s.strip() for s in states.split(',') if s.strip()]
        extra_settings['jurisdictions'] = state_list

    insert(
        '''INSERT INTO hired_staff
           (client_id, staff_name, staff_slug, vertical, mode, settings)
           VALUES (?,?,?,?,?,?)''',
        (
            client_id,
            staff_meta['name'],
            staff_slug,
            staff_meta['vertical'],
            staff_meta['mode'],
            json.dumps(extra_settings),
        )
    )

    send_welcome_email(
        app_config=current_app.config,
        logger=current_app.logger,
        to_email=email,
        name=name,
        firm_name=firm_name,
        staff_slug=staff_slug,
        staff_name=staff_meta['name'],
        states=states,
        temp_password=temp_password,
    )

    current_app.logger.info(
        f'New client registered: {email} ({firm_name}) — staff: {staff_slug}'
    )
    return jsonify({'success': True, 'message': 'Account created'}), 201


# ── Stripe webhook ─────────────────────────────────────────────

@api_bp.route('/stripe/webhook', methods=['POST'])
def stripe_webhook():
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')
    webhook_secret = current_app.config.get('STRIPE_WEBHOOK_SECRET', '')

    if not webhook_secret or webhook_secret == 'WHSEC_PLACEHOLDER':
        return jsonify({'error': 'Webhook secret not configured'}), 500

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except ValueError:
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError:
        return jsonify({'error': 'Invalid signature'}), 400

    etype = event['type']
    obj = event['data']['object']

    if etype == 'customer.subscription.created':
        customer_id = obj.get('customer')
        execute_commit(
            "UPDATE clients SET subscription_status='active', stripe_subscription_id=? WHERE stripe_customer_id=?",
            (obj.get('id'), customer_id)
        )

    elif etype == 'customer.subscription.deleted':
        customer_id = obj.get('customer')
        execute_commit(
            "UPDATE clients SET subscription_status='cancelled' WHERE stripe_customer_id=?",
            (customer_id,)
        )

    elif etype == 'invoice.payment_failed':
        customer_id = obj.get('customer')
        client = query_one('SELECT * FROM clients WHERE stripe_customer_id=?', (customer_id,))
        if client:
            _send_payment_failed_email(client['email'], client['company_name'])

    return jsonify({'received': True})


def _send_payment_failed_email(to_email: str, company_name: str):
    api_key = current_app.config.get('SENDGRID_API_KEY', '')
    if not api_key:
        return
    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail
        msg = Mail(
            from_email=current_app.config.get('ADMIN_EMAIL', 'hire@tryjoyn.me'),
            to_emails=to_email,
            subject='Payment failed \u2014 Joyn',
            html_content=(
                f'<p>Hi {company_name},</p>'
                f'<p>We were unable to process your latest payment. '
                f'Please update your billing details at '
                f'<a href="https://app.tryjoyn.me/settings#billing">your portal settings</a>.</p>'
                f'<p>\u2014 Joyn</p>'
            ),
        )
        SendGridAPIClient(api_key).send(msg)
    except Exception as e:
        current_app.logger.error(f'SendGrid error: {e}')


# ── Observability: LLM cost reporting (staff-facing portal) ────────────────────

@api_bp.route('/client/usage/cost')
@api_login_required
def client_cost_summary():
    """
    Return a rolling cost summary for the authenticated client.

    Query params:
      days  — lookback window in days (default 30, max 90)

    Response:
      {
        "period_days": 30,
        "total_cost_usd": 1.2345,
        "total_input_tokens": 45000,
        "total_output_tokens": 12000,
        "by_workflow": [
          { "workflow": "bulletin_analysis", "calls": 12, "cost_usd": 0.80 },
          ...
        ],
        "daily": [
          { "date": "2026-03-01", "cost_usd": 0.04 },
          ...
        ]
      }
    """
    days = min(int(request.args.get('days', 30)), 90)

    totals = query_one(
        """SELECT
               COALESCE(SUM(cost_usd), 0)       AS total_cost_usd,
               COALESCE(SUM(input_tokens), 0)   AS total_input_tokens,
               COALESCE(SUM(output_tokens), 0)  AS total_output_tokens,
               COUNT(*)                          AS total_calls
           FROM llm_usage
           WHERE client_id = ?
             AND recorded_at >= datetime('now', ? || ' days')""",
        (g.client_id, f'-{days}'),
    )

    by_workflow = query(
        """SELECT
               COALESCE(workflow, 'unknown') AS workflow,
               COUNT(*)                      AS calls,
               COALESCE(SUM(cost_usd), 0)   AS cost_usd
           FROM llm_usage
           WHERE client_id = ?
             AND recorded_at >= datetime('now', ? || ' days')
           GROUP BY workflow
           ORDER BY cost_usd DESC""",
        (g.client_id, f'-{days}'),
    )

    daily = query(
        """SELECT
               DATE(recorded_at)            AS date,
               COALESCE(SUM(cost_usd), 0)  AS cost_usd
           FROM llm_usage
           WHERE client_id = ?
             AND recorded_at >= datetime('now', ? || ' days')
           GROUP BY DATE(recorded_at)
           ORDER BY date ASC""",
        (g.client_id, f'-{days}'),
    )

    return jsonify({
        'period_days':        days,
        'total_cost_usd':     round(float(totals['total_cost_usd']), 6) if totals else 0,
        'total_input_tokens': int(totals['total_input_tokens']) if totals else 0,
        'total_output_tokens':int(totals['total_output_tokens']) if totals else 0,
        'total_calls':        int(totals['total_calls']) if totals else 0,
        'by_workflow':        rows_to_list(by_workflow),
        'daily':              rows_to_list(daily),
    })


@api_bp.route('/admin/usage/cost')
@portal_secret_required
def admin_cost_summary():
    """
    System-wide cost summary across all clients.
    Protected by JOYN_PORTAL_SECRET — for internal use only.

    Query params:
      days  — lookback window in days (default 7, max 90)
    """
    days = min(int(request.args.get('days', 7)), 90)

    totals = query_one(
        """SELECT
               COALESCE(SUM(cost_usd), 0)       AS total_cost_usd,
               COALESCE(SUM(input_tokens), 0)   AS total_input_tokens,
               COALESCE(SUM(output_tokens), 0)  AS total_output_tokens,
               COUNT(*)                          AS total_calls,
               COUNT(DISTINCT client_id)         AS active_clients
           FROM llm_usage
           WHERE recorded_at >= datetime('now', ? || ' days')""",
        (f'-{days}',),
    )

    by_client = query(
        """SELECT
               client_id,
               COUNT(*)                      AS calls,
               COALESCE(SUM(cost_usd), 0)   AS cost_usd
           FROM llm_usage
           WHERE recorded_at >= datetime('now', ? || ' days')
           GROUP BY client_id
           ORDER BY cost_usd DESC
           LIMIT 20""",
        (f'-{days}',),
    )

    return jsonify({
        'period_days':        days,
        'total_cost_usd':     round(float(totals['total_cost_usd']), 6) if totals else 0,
        'total_input_tokens': int(totals['total_input_tokens']) if totals else 0,
        'total_output_tokens':int(totals['total_output_tokens']) if totals else 0,
        'total_calls':        int(totals['total_calls']) if totals else 0,
        'active_clients':     int(totals['active_clients']) if totals else 0,
        'top_clients':        rows_to_list(by_client),
    })


# ── Admin: reset all client data (one-time use, protected by portal secret) ──

@api_bp.route('/admin/reset-clients', methods=['POST'])
@portal_secret_required
def admin_reset_clients():
    """
    Wipe all client accounts and related data from the portal database.
    Protected by X-Joyn-Secret header. For testing/onboarding resets only.
    """
    tables = [
        'password_reset_tokens',
        'api_keys',
        'activity_log',
        'outputs',
        'hired_staff',
        'clients',
    ]
    counts = {}
    for table in tables:
        try:
            row = query_one(f"SELECT COUNT(*) AS n FROM {table}")
            n = row['n'] if row else 0
            execute_commit(f"DELETE FROM {table}")
            counts[table] = n
        except Exception as exc:
            counts[table] = f"error: {exc}"

    return jsonify({
        'status': 'ok',
        'message': 'All client data cleared',
        'deleted': counts,
    })


# ── Admin: look up client by email ────────────────────────────────────────────
@api_bp.route('/admin/lookup-client', methods=['GET'])
@portal_secret_required
def admin_lookup_client():
    """
    Look up a client's integer ID by email address.
    Protected by X-Joyn-Secret header.
    Query param: email
    """
    email = request.args.get('email', '').strip().lower()
    if not email:
        return jsonify({'error': 'email query param required'}), 400
    client = query_one('SELECT id, email, company_name FROM clients WHERE email=?', (email,))
    if not client:
        return jsonify({'error': f'No client found with email {email}'}), 404
    return jsonify({
        'status': 'ok',
        'client_id': client['id'],
        'email': client['email'],
        'company_name': client['company_name'],
    })

# ── Admin: view activity log for a client ─────────────────────────────────────
@api_bp.route('/admin/activity-log', methods=['GET'])
@portal_secret_required
def admin_activity_log():
    """
    View recent activity log entries for a client.
    Protected by X-Joyn-Secret header.
    Query params: client_id (int), limit (int, default 20)
    """
    client_id = request.args.get('client_id', type=int)
    limit = min(request.args.get('limit', 20, type=int), 100)
    if not client_id:
        return jsonify({'error': 'client_id query param required'}), 400
    rows = query(
        'SELECT * FROM activity_log WHERE client_id=? ORDER BY timestamp DESC LIMIT ?',
        (client_id, limit)
    )
    return jsonify({
        'status': 'ok',
        'client_id': client_id,
        'count': len(rows_to_list(rows)),
        'entries': rows_to_list(rows),
    })
