import json
import stripe
from flask import Blueprint, request, jsonify, current_app, g
from data.db import query_one, query, insert, execute_commit, rows_to_list, row_to_dict
from auth.helpers import api_login_required, portal_secret_required

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

    # Verify client exists
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
            subject='Payment failed — Joyn',
            html_content=f'<p>Hi {company_name},</p>'
                         f'<p>We were unable to process your latest payment. '
                         f'Please update your billing details at '
                         f'<a href="https://app.tryjoyn.me/settings#billing">your portal settings</a>.</p>'
                         f'<p>— Joyn</p>',
        )
        SendGridAPIClient(api_key).send(msg)
    except Exception as e:
        current_app.logger.error(f'SendGrid error: {e}')
