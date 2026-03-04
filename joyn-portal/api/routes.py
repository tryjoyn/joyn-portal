import json
import secrets
import string
import stripe
from flask import Blueprint, request, jsonify, current_app, g
from data.db import query_one, query, insert, execute_commit, rows_to_list, row_to_dict
from auth.helpers import api_login_required, portal_secret_required, hash_password

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


# ── Public: register client (called from hire form) ───────────

@api_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'success': False, 'error': 'JSON body required'}), 400

    name      = (data.get('name') or '').strip()
    email     = (data.get('email') or '').strip().lower()
    firm_name = (data.get('firm_name') or '').strip()
    states    = (data.get('states') or '').strip()

    if not all([name, email, firm_name, states]):
        return jsonify({'success': False, 'error': 'All fields are required'}), 400

    existing = query_one('SELECT id FROM clients WHERE email=?', (email,))
    if existing:
        return jsonify({'success': False, 'error': 'An account with this email already exists'}), 409

    # Generate 12-char alphanumeric temp password
    alphabet = string.ascii_letters + string.digits
    temp_password = ''.join(secrets.choice(alphabet) for _ in range(12))

    client_id = insert(
        '''INSERT INTO clients
           (email, password_hash, company_name, primary_contact_name,
            states, first_login, subscription_status)
           VALUES (?,?,?,?,?,1,'active')''',
        (email, hash_password(temp_password), firm_name, name, states)
    )

    # Auto-hire Iris with the selected states in her settings
    state_list = [s.strip() for s in states.split(',') if s.strip()]
    insert(
        '''INSERT INTO hired_staff
           (client_id, staff_name, staff_slug, vertical, mode, settings)
           VALUES (?,?,?,?,?,?)''',
        (client_id, 'Iris', 'iris', 'Insurance', 'autonomous',
         json.dumps({'jurisdictions': state_list}))
    )

    _send_welcome_email(email, name, firm_name, states, temp_password)

    current_app.logger.info(f'New client registered: {email} ({firm_name})')
    return jsonify({'success': True, 'message': 'Account created'}), 201


def _send_welcome_email(to_email: str, name: str, firm_name: str,
                        states: str, temp_password: str):
    api_key = current_app.config.get('SENDGRID_API_KEY', '')
    if not api_key:
        current_app.logger.warning('SendGrid not configured — welcome email not sent')
        return

    state_list = ', '.join(s.strip() for s in states.split(',') if s.strip())

    plain = (
        f"Hi {name},\n\n"
        f"Iris is now monitoring {state_list} for {firm_name}.\n\n"
        f"Log in to your portal to see her activity and manage your account:\n"
        f"https://app.tryjoyn.me/login\n\n"
        f"Your login details:\n"
        f"  Email:              {to_email}\n"
        f"  Temporary password: {temp_password}\n\n"
        f"You will be asked to set a new password the first time you sign in.\n\n"
        f"Questions? Reply to this email or write to hire@tryjoyn.me\n\n"
        f"— Iris · Joyn"
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#fafaf8;font-family:Arial,sans-serif;color:#111110;">
<table width="100%" cellpadding="0" cellspacing="0">
  <tr><td align="center" style="padding:3rem 1rem;">
    <table width="100%" style="max-width:560px;">

      <!-- Header -->
      <tr><td style="border-bottom:1px solid #e8e4dc;padding-bottom:1.5rem;margin-bottom:1.5rem;">
        <span style="font-family:'Courier New',monospace;font-size:0.9rem;font-weight:bold;letter-spacing:0.12em;color:#111110;">JOYN.</span>
      </td></tr>

      <!-- Gold label -->
      <tr><td style="padding-top:1.75rem;">
        <p style="font-family:'Courier New',monospace;font-size:0.65rem;letter-spacing:0.1em;text-transform:uppercase;color:#8B6914;margin:0 0 0.5rem 0;">— Iris · Insurance Regulatory Intelligence</p>
      </td></tr>

      <!-- Greeting -->
      <tr><td>
        <h1 style="font-size:2rem;font-weight:300;margin:0 0 1.25rem 0;color:#111110;line-height:1.2;">Hi {name},</h1>
        <p style="font-size:0.95rem;color:#3f3f3e;line-height:1.8;margin:0 0 1rem 0;">
          Iris is now monitoring <strong style="color:#111110;">{state_list}</strong> for {firm_name}.
          She's tracking regulatory changes and will alert you when something matters.
        </p>
        <p style="font-size:0.95rem;color:#3f3f3e;line-height:1.8;margin:0 0 1.75rem 0;">
          Log in to your portal to review her activity, adjust her settings, and see her latest briefings.
        </p>
      </td></tr>

      <!-- CTA -->
      <tr><td style="padding-bottom:1.75rem;">
        <a href="https://app.tryjoyn.me/login"
           style="display:inline-block;font-family:'Courier New',monospace;font-size:0.75rem;font-weight:bold;
                  letter-spacing:0.1em;text-transform:uppercase;padding:0.875rem 2rem;
                  background:#111110;color:#fafaf8;text-decoration:none;">
          Log in to your portal →
        </a>
      </td></tr>

      <!-- Credentials -->
      <tr><td style="background:#f4f1eb;border:1px solid #e8e4dc;padding:1.25rem 1.5rem;margin-bottom:1.75rem;">
        <p style="font-family:'Courier New',monospace;font-size:0.65rem;letter-spacing:0.1em;text-transform:uppercase;color:#8B6914;margin:0 0 0.75rem 0;">Your login details</p>
        <p style="font-family:'Courier New',monospace;font-size:0.8rem;color:#111110;margin:0 0 0.35rem 0;">
          <span style="color:#3f3f3e;">Email&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</span>{to_email}
        </p>
        <p style="font-family:'Courier New',monospace;font-size:0.8rem;color:#111110;margin:0;">
          <span style="color:#3f3f3e;">Temporary password&nbsp;&nbsp;</span>{temp_password}
        </p>
      </td></tr>

      <!-- Note -->
      <tr><td style="padding-top:1.25rem;">
        <p style="font-size:0.85rem;color:#3f3f3e;line-height:1.7;margin:0 0 0.5rem 0;">
          You will be asked to set a new password when you first sign in.
        </p>
        <p style="font-size:0.85rem;color:#3f3f3e;line-height:1.7;margin:0 0 1.75rem 0;">
          Questions? Reply to this email or write to
          <a href="mailto:hire@tryjoyn.me" style="color:#8B6914;">hire@tryjoyn.me</a>
        </p>
      </td></tr>

      <!-- Footer -->
      <tr><td style="border-top:1px solid #e8e4dc;padding-top:1.25rem;">
        <p style="font-family:'Courier New',monospace;font-size:0.65rem;letter-spacing:0.08em;text-transform:uppercase;color:#3f3f3e;margin:0;">
          Iris · Joyn &nbsp;·&nbsp; tryjoyn.me
        </p>
      </td></tr>

    </table>
  </td></tr>
</table>
</body>
</html>"""

    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail
        msg = Mail(
            from_email=current_app.config.get('ADMIN_EMAIL', 'hire@tryjoyn.me'),
            to_emails=to_email,
            subject='Iris is now monitoring your states — here\'s how to log in',
            html_content=html,
            plain_text_content=plain,
        )
        SendGridAPIClient(api_key).send(msg)
    except Exception as e:
        current_app.logger.error(f'SendGrid welcome email error: {e}')


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
