import json
import os
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

    # For non-Iris staff, send the portal welcome email directly.
    # For Iris, the iris-agent sends the richer onboarding Stage 0 email instead.
    if staff_slug != 'iris':
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

    # ── Notify iris-agent to create client profile + start onboarding ──────
    if staff_slug == 'iris':
        iris_url = current_app.config.get('IRIS_AGENT_URL', '')
        iris_key = current_app.config.get('IRIS_INTERNAL_KEY', '')
        if iris_url and iris_key:
            try:
                import requests as _requests
                _requests.post(
                    f'{iris_url}/api/register',
                    json={
                        'email': email,
                        'name': name,
                        'firm_name': firm_name,
                        'states': [s.strip() for s in states.split(',') if s.strip()],
                        'portal_client_id': client_id,
                    },
                    headers={'X-Internal-Key': iris_key},
                    timeout=10,
                )
                current_app.logger.info(f'iris-agent notified for new client: {email}')
            except Exception as _e:
                current_app.logger.warning(f'iris-agent notify failed (non-fatal): {_e}')

    current_app.logger.info(
        f'New client registered: {email} ({firm_name}) — staff: {staff_slug}'
    )
    return jsonify({'success': True, 'message': 'Account created'}), 201



# ── Stripe checkout session (portal registration flow) ──────────────────────────

# Pricing packages (BVD: defined server-side only)
JOYN_PRICING_PACKAGES = {
    'founder_onetime': {
        'name': "Founder's Rate - Limited Time",
        'amount': 99.00,  # USD one-time
        'description': 'AI staff one-time setup at exclusive founder\'s rate',
        'mode': 'payment',  # one-time payment, not subscription
        'limited_time': True,
    },
    'standard_monthly': {
        'name': 'Standard - Monthly',
        'amount': 149.00,  # USD
        'description': 'AI staff monthly subscription',
        'mode': 'subscription',
        'interval': 'month',
    },
    'standard_annual': {
        'name': 'Standard - Annual',
        'amount': 1490.00,  # USD (save ~17%)
        'description': 'AI staff annual subscription',
        'mode': 'subscription',
        'interval': 'year',
    },
}


@api_bp.route('/checkout/session', methods=['POST'])
@api_login_required
def create_checkout_session():
    """
    Create a Stripe checkout session for subscription.
    
    Expected JSON body:
    {
        "package_id": "founder_monthly" | "founder_annual" | etc,
        "origin_url": "https://app.tryjoyn.me"  (from window.location.origin)
    }
    
    Returns:
    {
        "url": "https://checkout.stripe.com/...",
        "session_id": "cs_..."
    }
    """
    data = request.get_json(silent=True) or {}
    package_id = data.get('package_id', '').strip()
    origin_url = data.get('origin_url', '').strip().rstrip('/')
    
    if not package_id or package_id not in JOYN_PRICING_PACKAGES:
        return jsonify({'error': f'Invalid package: {package_id}'}), 400
    
    if not origin_url:
        return jsonify({'error': 'origin_url required'}), 400
    
    # Get amount from server-side packages only (security)
    package = JOYN_PRICING_PACKAGES[package_id]
    amount = package['amount']
    
    # Get client info
    client = row_to_dict(query_one('SELECT * FROM clients WHERE id=?', (g.client_id,)))
    if not client:
        return jsonify({'error': 'Client not found'}), 404
    
    # Build URLs dynamically
    success_url = f"{origin_url}/settings?payment=success&session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{origin_url}/settings?payment=cancelled"
    
    try:
        # Create or get Stripe customer
        if not client.get('stripe_customer_id'):
            customer = stripe.Customer.create(
                email=client['email'],
                name=client.get('company_name', ''),
                metadata={'joyn_client_id': str(g.client_id)},
            )
            execute_commit(
                'UPDATE clients SET stripe_customer_id=? WHERE id=?',
                (customer.id, g.client_id)
            )
            customer_id = customer.id
        else:
            customer_id = client['stripe_customer_id']
        
        # Determine payment mode and build line item
        is_subscription = package.get('mode') == 'subscription'
        
        price_data = {
            'currency': 'usd',
            'product_data': {
                'name': package['name'],
                'description': package['description'],
            },
            'unit_amount': int(amount * 100),  # Convert to cents
        }
        
        # Add recurring only for subscriptions
        if is_subscription:
            price_data['recurring'] = {
                'interval': package.get('interval', 'month'),
            }
        
        # Create checkout session
        session = stripe.checkout.Session.create(
            customer=customer_id,
            mode='subscription' if is_subscription else 'payment',
            line_items=[{
                'price_data': price_data,
                'quantity': 1,
            }],
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                'joyn_client_id': str(g.client_id),
                'package_id': package_id,
            },
        )
        
        # Record pending transaction
        insert(
            """INSERT INTO payment_transactions 
               (client_id, session_id, amount, currency, package_id, status)
               VALUES (?, ?, ?, 'usd', ?, 'pending')""",
            (g.client_id, session.id, amount, package_id)
        )
        
        return jsonify({
            'url': session.url,
            'session_id': session.id,
        })
        
    except stripe.error.StripeError as exc:
        current_app.logger.error(f'Stripe error: {exc}')
        return jsonify({'error': 'Payment service unavailable'}), 503


@api_bp.route('/checkout/status/<session_id>')
@api_login_required
def get_checkout_status(session_id):
    """
    Get status of a Stripe checkout session.
    
    Returns:
    {
        "status": "complete" | "open" | "expired",
        "payment_status": "paid" | "unpaid",
        "amount_total": 4900,
        "currency": "usd"
    }
    """
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        
        # Verify this session belongs to the authenticated client
        if session.metadata.get('joyn_client_id') != str(g.client_id):
            return jsonify({'error': 'Session not found'}), 404
        
        # Update transaction status if paid
        if session.payment_status == 'paid':
            # Check if already processed
            existing = query_one(
                "SELECT * FROM payment_transactions WHERE session_id=? AND status='completed'",
                (session_id,)
            )
            if not existing:
                execute_commit(
                    """UPDATE payment_transactions 
                       SET status='completed', completed_at=CURRENT_TIMESTAMP
                       WHERE session_id=?""",
                    (session_id,)
                )
                # Update client subscription status
                execute_commit(
                    "UPDATE clients SET subscription_status='active' WHERE id=?",
                    (g.client_id,)
                )
        
        return jsonify({
            'status': session.status,
            'payment_status': session.payment_status,
            'amount_total': session.amount_total,
            'currency': session.currency,
        })
        
    except stripe.error.StripeError as exc:
        current_app.logger.error(f'Stripe error: {exc}')
        return jsonify({'error': 'Payment service unavailable'}), 503



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

# ── Admin: check if a client's staff member is paused ─────────────────────────
@api_bp.route('/admin/staff-status', methods=['GET'])
@portal_secret_required
def admin_staff_status():
    """
    Return the paused/active status of a staff member for a client.
    Used by iris-agent to skip all LLM processing for paused clients.
    Protected by X-Joyn-Secret header.
    Query params: email (str), staff_slug (str, default 'iris')
    """
    email = request.args.get('email', '').strip().lower()
    staff_slug = request.args.get('staff_slug', 'iris').strip().lower()
    if not email:
        return jsonify({'error': 'email query param required'}), 400
    client = query_one('SELECT * FROM clients WHERE LOWER(email)=?', (email,))
    if not client:
        return jsonify({'error': 'client not found', 'paused': False}), 404
    staff = query_one(
        'SELECT * FROM hired_staff WHERE client_id=? AND staff_slug=?',
        (client['id'], staff_slug)
    )
    if not staff:
        return jsonify({'error': 'staff not found', 'paused': False}), 404
    is_paused = (staff['status'] == 'paused')
    return jsonify({
        'status': 'ok',
        'client_id': client['id'],
        'email': email,
        'staff_slug': staff_slug,
        'staff_status': staff['status'],
        'paused': is_paused,
    })

# ── Admin: toggle staff pause status (for testing) ────────────────────────────
@api_bp.route('/admin/toggle-pause', methods=['POST'])
@portal_secret_required
def admin_toggle_pause():
    """Toggle a staff member's paused status. For admin/testing use only."""
    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip().lower()
    staff_slug = (data.get('staff_slug') or 'iris').strip().lower()
    if not email:
        return jsonify({'error': 'email required'}), 400
    client = query_one('SELECT * FROM clients WHERE LOWER(email)=?', (email,))
    if not client:
        return jsonify({'error': 'client not found'}), 404
    staff = query_one(
        'SELECT * FROM hired_staff WHERE client_id=? AND staff_slug=?',
        (client['id'], staff_slug)
    )
    if not staff:
        return jsonify({'error': 'staff not found'}), 404
    new_status = 'paused' if staff['status'] == 'active' else 'active'
    execute_commit(
        'UPDATE hired_staff SET status=? WHERE client_id=? AND staff_slug=?',
        (new_status, client['id'], staff_slug)
    )
    return jsonify({'status': 'ok', 'new_status': new_status, 'paused': new_status == 'paused'})



# ── Public: Form submission proxy (removes hardcoded API key from frontend) ────
# This endpoint proxies form submissions to Web3Forms, keeping the API key server-side

@api_bp.route('/forms/submit', methods=['POST', 'OPTIONS'])
@cross_origin(origins=["https://tryjoyn.me", "https://www.tryjoyn.me", "http://localhost:3000"],
              supports_credentials=False,
              allow_headers=["Content-Type"])
def form_submit_proxy():
    """
    Proxy form submissions to Web3Forms API.
    
    This removes the need to expose the Web3Forms API key in public HTML.
    The key is stored in WEB3FORMS_KEY environment variable.
    
    Expected JSON body:
    {
        "form_type": "interest" | "waitlist" | "contact",
        "name": "...",
        "email": "...",
        ...other fields
    }
    """
    if request.method == 'OPTIONS':
        return '', 204
    
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'success': False, 'error': 'JSON body required'}), 400
    
    # Validate required fields
    name = (data.get('name') or '').strip()
    email = (data.get('email') or '').strip()
    
    if not name or not email:
        return jsonify({'success': False, 'error': 'Name and email are required'}), 400
    
    # Get API key from environment (not from client)
    import os
    web3forms_key = os.environ.get('WEB3FORMS_KEY', '')
    if not web3forms_key:
        current_app.logger.warning('WEB3FORMS_KEY not configured')
        # Fallback: send via email instead
        return _send_form_via_email(data)
    
    # Build Web3Forms payload
    form_type = data.get('form_type', 'contact')
    subject_map = {
        'interest': f"Interest — {data.get('interested_in', 'Unknown')} · tryjoyn.me",
        'waitlist': "Waitlist — New AI Staff · tryjoyn.me",
        'contact': "Contact Form · tryjoyn.me",
    }
    
    payload = {
        'access_key': web3forms_key,
        'subject': subject_map.get(form_type, subject_map['contact']),
        'name': name,
        'email': email,
    }
    
    # Add form-specific fields
    optional_fields = ['company', 'interested_in', 'hire_timeline', 'notes', 'looking_for']
    for field in optional_fields:
        if data.get(field):
            payload[field] = data[field]
    
    # Submit to Web3Forms
    try:
        import requests as _requests
        resp = _requests.post(
            'https://api.web3forms.com/submit',
            json=payload,
            timeout=10
        )
        if resp.status_code == 200:
            return jsonify({'success': True, 'message': 'Form submitted successfully'})
        else:
            current_app.logger.error(f'Web3Forms error: {resp.status_code} {resp.text}')
            return jsonify({'success': False, 'error': 'Form submission failed'}), 500
    except Exception as exc:
        current_app.logger.error(f'Web3Forms exception: {exc}')
        return _send_form_via_email(data)


def _send_form_via_email(data: dict):
    """Fallback: Send form data via SendGrid if Web3Forms is unavailable."""
    api_key = current_app.config.get('SENDGRID_API_KEY', '')
    admin_email = current_app.config.get('ADMIN_EMAIL', 'hire@tryjoyn.me')
    
    if not api_key:
        return jsonify({'success': False, 'error': 'Form submission unavailable'}), 503
    
    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail
        
        form_type = data.get('form_type', 'contact')
        subject = f"[Joyn Form] {form_type.title()} - {data.get('name', 'Unknown')}"
        
        # Build HTML content
        content_lines = [f"<p><strong>{k}:</strong> {v}</p>" for k, v in data.items()]
        html_content = f"<h2>Form Submission</h2>{''.join(content_lines)}"
        
        msg = Mail(
            from_email=admin_email,
            to_emails=admin_email,
            subject=subject,
            html_content=html_content,
        )
        SendGridAPIClient(api_key).send(msg)
        return jsonify({'success': True, 'message': 'Form submitted successfully'})
    except Exception as exc:
        current_app.logger.error(f'SendGrid fallback error: {exc}')
        return jsonify({'success': False, 'error': 'Form submission failed'}), 500


# ── Admin: Data retention purge (BVD compliance) ────────────────────────────────

@api_bp.route('/admin/purge-old-data', methods=['POST'])
@portal_secret_required
def admin_purge_old_data():
    """
    Purge data older than retention policy.
    
    Retention policy (per BVD compliance):
    - outputs (bulletins): 90 days
    - activity_log: 90 days
    - llm_usage: 180 days
    
    Protected by X-Joyn-Secret header. For compliance automation.
    """
    retention_days = {
        'outputs': 90,
        'activity_log': 90,
        'llm_usage': 180,
    }
    
    purge_results = {}
    
    for table, days in retention_days.items():
        try:
            # Get count before purge
            count_before = query_one(f"SELECT COUNT(*) as c FROM {table}")['c']
            
            # Determine date column
            date_col = 'delivered_at' if table == 'outputs' else (
                'timestamp' if table == 'activity_log' else 'recorded_at'
            )
            
            # Purge old records
            execute_commit(
                f"DELETE FROM {table} WHERE {date_col} < datetime('now', '-{days} days')"
            )
            
            # Get count after purge
            count_after = query_one(f"SELECT COUNT(*) as c FROM {table}")['c']
            records_purged = count_before - count_after
            
            # Log the purge
            insert(
                """INSERT INTO retention_purge_log 
                   (table_name, records_purged, retention_days, notes)
                   VALUES (?, ?, ?, 'Automated retention purge')""",
                (table, records_purged, days)
            )
            
            purge_results[table] = {
                'retention_days': days,
                'records_before': count_before,
                'records_purged': records_purged,
                'records_after': count_after,
            }
            
        except Exception as exc:
            purge_results[table] = {'error': str(exc)}
    
    return jsonify({
        'status': 'ok',
        'message': 'Retention purge complete',
        'results': purge_results,
    })


# ── Admin: Delete hirer data (BVD compliance - offboarding) ─────────────────────

@api_bp.route('/admin/delete-hirer', methods=['POST'])
@portal_secret_required
def admin_delete_hirer():
    """
    Delete all data for a specific hirer (client) for offboarding.
    
    BVD Compliance: Hirer data deletion on offboarding.
    
    Expected JSON body:
    {
        "client_id": 123,
        "confirm": true
    }
    
    Protected by X-Joyn-Secret header.
    """
    data = request.get_json(silent=True) or {}
    client_id = data.get('client_id')
    confirm = data.get('confirm', False)
    
    if not client_id:
        return jsonify({'error': 'client_id required'}), 400
    
    if not confirm:
        return jsonify({'error': 'Set confirm=true to proceed with deletion'}), 400
    
    # Verify client exists
    client = query_one('SELECT * FROM clients WHERE id=?', (client_id,))
    if not client:
        return jsonify({'error': f'Client {client_id} not found'}), 404
    
    # Delete in order (foreign key constraints)
    tables = [
        ('password_reset_tokens', 'client_id'),
        ('llm_usage', 'client_id'),
        ('activity_log', 'client_id'),
        ('outputs', 'client_id'),
        ('hired_staff', 'client_id'),
        ('clients', 'id'),
    ]
    
    deleted = {}
    for table, col in tables:
        try:
            count = query_one(f"SELECT COUNT(*) as c FROM {table} WHERE {col}=?", (client_id,))['c']
            execute_commit(f"DELETE FROM {table} WHERE {col}=?", (client_id,))
            deleted[table] = count
        except Exception as exc:
            deleted[table] = f"error: {exc}"
    
    current_app.logger.info(f"Deleted hirer data: client_id={client_id} email={client['email']}")
    
    return jsonify({
        'status': 'ok',
        'message': f"Hirer {client['email']} data deleted",
        'deleted': deleted,
    })



# ── Admin: Cost tracking and alerts ─────────────────────────────────────────────

# Weekly cost threshold for alerts (USD)
WEEKLY_COST_ALERT_THRESHOLD = float(os.environ.get('WEEKLY_COST_ALERT_USD', '50.00'))


@api_bp.route('/admin/cost-report', methods=['GET'])
@portal_secret_required
def admin_cost_report():
    """
    Get cost report for Iris Claude API usage.
    
    Query params:
    - period: 'day' | 'week' | 'month' (default: 'week')
    
    Returns:
    {
        "period": "week",
        "total_cost_usd": 12.34,
        "total_calls": 156,
        "total_input_tokens": 234567,
        "total_output_tokens": 45678,
        "by_client": [...],
        "by_workflow": [...],
        "alert": true/false (if over threshold)
    }
    """
    period = request.args.get('period', 'week')
    
    period_days = {
        'day': 1,
        'week': 7,
        'month': 30,
    }
    days = period_days.get(period, 7)
    
    try:
        # Get totals
        totals = query_one(f"""
            SELECT 
                COUNT(*) as total_calls,
                COALESCE(SUM(cost_usd), 0) as total_cost_usd,
                COALESCE(SUM(input_tokens), 0) as total_input_tokens,
                COALESCE(SUM(output_tokens), 0) as total_output_tokens
            FROM llm_usage
            WHERE recorded_at > datetime('now', '-{days} days')
        """)
        
        # Get breakdown by client
        by_client = query(f"""
            SELECT 
                client_id,
                COUNT(*) as calls,
                COALESCE(SUM(cost_usd), 0) as cost_usd
            FROM llm_usage
            WHERE recorded_at > datetime('now', '-{days} days')
            GROUP BY client_id
            ORDER BY cost_usd DESC
            LIMIT 10
        """)
        
        # Get breakdown by workflow
        by_workflow = query(f"""
            SELECT 
                workflow,
                COUNT(*) as calls,
                COALESCE(SUM(cost_usd), 0) as cost_usd
            FROM llm_usage
            WHERE recorded_at > datetime('now', '-{days} days')
            GROUP BY workflow
            ORDER BY cost_usd DESC
        """)
        
        total_cost = totals['total_cost_usd'] if totals else 0
        alert = total_cost > WEEKLY_COST_ALERT_THRESHOLD if period == 'week' else False
        
        return jsonify({
            'period': period,
            'days': days,
            'total_cost_usd': round(total_cost, 4),
            'total_calls': totals['total_calls'] if totals else 0,
            'total_input_tokens': totals['total_input_tokens'] if totals else 0,
            'total_output_tokens': totals['total_output_tokens'] if totals else 0,
            'by_client': [row_to_dict(r) for r in by_client] if by_client else [],
            'by_workflow': [row_to_dict(r) for r in by_workflow] if by_workflow else [],
            'alert': alert,
            'alert_threshold_usd': WEEKLY_COST_ALERT_THRESHOLD,
        })
        
    except Exception as exc:
        current_app.logger.error(f'Cost report error: {exc}')
        return jsonify({'error': 'Failed to generate cost report'}), 500


@api_bp.route('/admin/pipeline-metrics', methods=['GET'])
@portal_secret_required
def admin_pipeline_metrics():
    """
    Get pipeline performance metrics for Iris.
    
    Returns latency percentiles and error rates.
    """
    period = request.args.get('period', 'week')
    days = {'day': 1, 'week': 7, 'month': 30}.get(period, 7)
    
    try:
        metrics = query_one(f"""
            SELECT 
                COUNT(*) as total_calls,
                COUNT(CASE WHEN status = 'success' THEN 1 END) as successful_calls,
                COUNT(CASE WHEN status = 'error' THEN 1 END) as failed_calls,
                AVG(latency_ms) as avg_latency_ms,
                MAX(latency_ms) as max_latency_ms,
                MIN(latency_ms) as min_latency_ms
            FROM llm_usage
            WHERE recorded_at > datetime('now', '-{days} days')
        """)
        
        # Get error breakdown
        errors = query(f"""
            SELECT 
                error_message,
                COUNT(*) as count
            FROM llm_usage
            WHERE recorded_at > datetime('now', '-{days} days')
              AND status = 'error'
            GROUP BY error_message
            ORDER BY count DESC
            LIMIT 5
        """)
        
        total = metrics['total_calls'] if metrics else 0
        successful = metrics['successful_calls'] if metrics else 0
        
        return jsonify({
            'period': period,
            'total_calls': total,
            'successful_calls': successful,
            'failed_calls': metrics['failed_calls'] if metrics else 0,
            'success_rate': round(successful / total * 100, 2) if total > 0 else 0,
            'avg_latency_ms': round(metrics['avg_latency_ms'] or 0, 0),
            'max_latency_ms': metrics['max_latency_ms'] or 0,
            'min_latency_ms': metrics['min_latency_ms'] or 0,
            'top_errors': [row_to_dict(r) for r in errors] if errors else [],
        })
        
    except Exception as exc:
        current_app.logger.error(f'Pipeline metrics error: {exc}')
        return jsonify({'error': 'Failed to generate metrics'}), 500
