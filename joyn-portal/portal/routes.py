import json
import secrets
import string
from datetime import datetime
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, g, jsonify, flash, current_app
)
from data.db import query_one, query, insert, execute_commit, row_to_dict, rows_to_list
from auth.helpers import login_required, hash_password, verify_password
from staff_common import STAFF_REGISTRY, AVAILABLE_STAFF_SLUGS, send_staff_added_email

portal_bp = Blueprint('portal', __name__)


def _get_client():
    return row_to_dict(query_one('SELECT * FROM clients WHERE id=?', (g.client_id,)))


def _get_hired_staff(client_id):
    return rows_to_list(query(
        "SELECT * FROM hired_staff WHERE client_id=? AND status != 'let-go' ORDER BY hired_at ASC",
        (client_id,)
    ))


def _get_activity(client_id, staff_slug=None, limit=20):
    if staff_slug:
        rows = query(
            'SELECT * FROM activity_log WHERE client_id=? AND staff_slug=? ORDER BY timestamp DESC LIMIT ?',
            (client_id, staff_slug, limit)
        )
    else:
        rows = query(
            'SELECT * FROM activity_log WHERE client_id=? ORDER BY timestamp DESC LIMIT ?',
            (client_id, limit)
        )
    return rows_to_list(rows)


def _get_outputs(client_id, staff_slug=None, limit=50):
    if staff_slug:
        rows = query(
            'SELECT * FROM outputs WHERE client_id=? AND staff_slug=? ORDER BY delivered_at DESC LIMIT ?',
            (client_id, staff_slug, limit)
        )
    else:
        rows = query(
            'SELECT * FROM outputs WHERE client_id=? ORDER BY delivered_at DESC LIMIT ?',
            (client_id, limit)
        )
    return rows_to_list(rows)


def _stats(client_id):
    hired = query(
        "SELECT COUNT(*) as c FROM hired_staff WHERE client_id=? AND status='active'",
        (client_id,)
    )
    actions = query_one(
        'SELECT COUNT(*) as c FROM activity_log WHERE client_id=?',
        (client_id,)
    )
    alerts = query_one(
        "SELECT COUNT(*) as c FROM outputs WHERE client_id=? AND severity IN ('critical','high')",
        (client_id,)
    )
    return {
        'staff_count':    hired[0]['c'] if hired else 0,
        'total_actions':  actions['c'] if actions else 0,
        'total_alerts':   alerts['c'] if alerts else 0,
    }


# ── GET /dashboard ─────────────────────────────────────────────

@portal_bp.route('/dashboard')
@login_required
def dashboard():
    client = _get_client()
    hired_staff = _get_hired_staff(g.client_id)
    activity = _get_activity(g.client_id, limit=20)
    stats = _stats(g.client_id)
    return render_template(
        'dashboard.html',
        client=client,
        hired_staff=hired_staff,
        activity=activity,
        stats=stats,
        now=datetime.utcnow(),
    )


# ── GET /staff/iris ────────────────────────────────────────────

@portal_bp.route('/staff/iris')
@login_required
def staff_iris():
    client = _get_client()
    iris = row_to_dict(query_one(
        "SELECT * FROM hired_staff WHERE client_id=? AND staff_slug='iris'",
        (g.client_id,)
    ))
    if not iris:
        return redirect(url_for('portal.dashboard'))

    activity = _get_activity(g.client_id, staff_slug='iris', limit=50)
    outputs = _get_outputs(g.client_id, staff_slug='iris')

    # Parse settings JSON
    settings = {}
    if iris.get('settings'):
        try:
            settings = json.loads(iris['settings'])
        except (ValueError, TypeError):
            settings = {}

    # Month stats
    from datetime import timedelta
    month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0)
    actions_month = query_one(
        "SELECT COUNT(*) as c FROM activity_log WHERE client_id=? AND staff_slug='iris' AND timestamp >= ?",
        (g.client_id, month_start.isoformat())
    )
    alerts_month = query_one(
        "SELECT COUNT(*) as c FROM outputs WHERE client_id=? AND staff_slug='iris' AND severity IN ('critical','high') AND delivered_at >= ?",
        (g.client_id, month_start.isoformat())
    )

    iris_stats = {
        'actions_this_month': actions_month['c'] if actions_month else 0,
        'alerts_this_month':  alerts_month['c'] if alerts_month else 0,
        'outputs_count':      len(outputs),
    }

    return render_template(
        'staff_iris.html',
        client=client,
        iris=iris,
        iris_settings=settings,
        activity=activity,
        outputs=outputs,
        iris_stats=iris_stats,
        now=datetime.utcnow(),
    )


# ── GET/POST /settings ──────────────────────────────────────────

@portal_bp.route('/settings')
@login_required
def settings():
    client = _get_client()
    hired_staff = _get_hired_staff(g.client_id)
    return render_template('settings.html', client=client, hired_staff=hired_staff)


@portal_bp.route('/settings/company', methods=['POST'])
@login_required
def settings_company():
    execute_commit('''
        UPDATE clients SET
            company_name=?, business_reg_no=?, industry=?,
            address=?, website=?, team_size=?
        WHERE id=?
    ''', (
        request.form.get('company_name', ''),
        request.form.get('business_reg_no', ''),
        request.form.get('industry', ''),
        request.form.get('address', ''),
        request.form.get('website', ''),
        request.form.get('team_size', ''),
        g.client_id,
    ))
    return redirect(url_for('portal.settings') + '#company')


@portal_bp.route('/settings/contacts', methods=['POST'])
@login_required
def settings_contacts():
    execute_commit('''
        UPDATE clients SET
            primary_contact_name=?, primary_contact_phone=?,
            email=?, briefing_emails=?
        WHERE id=?
    ''', (
        request.form.get('primary_contact_name', ''),
        request.form.get('primary_contact_phone', ''),
        request.form.get('email', ''),
        request.form.get('briefing_emails', ''),
        g.client_id,
    ))
    return redirect(url_for('portal.settings') + '#contacts')


@portal_bp.route('/settings/password', methods=['POST'])
@login_required
def settings_password():
    client = _get_client()
    current_pw = request.form.get('current_password', '')
    new_pw = request.form.get('new_password', '')
    confirm_pw = request.form.get('confirm_password', '')

    if not verify_password(current_pw, client['password_hash']):
        hired_staff = _get_hired_staff(g.client_id)
        return render_template('settings.html', client=client, hired_staff=hired_staff,
                               pw_error='Current password is incorrect.'), 400

    if len(new_pw) < 12:
        hired_staff = _get_hired_staff(g.client_id)
        return render_template('settings.html', client=client, hired_staff=hired_staff,
                               pw_error='New password must be at least 12 characters.'), 400

    if new_pw != confirm_pw:
        hired_staff = _get_hired_staff(g.client_id)
        return render_template('settings.html', client=client, hired_staff=hired_staff,
                               pw_error='Passwords do not match.'), 400

    execute_commit('UPDATE clients SET password_hash=? WHERE id=?',
                   (hash_password(new_pw), g.client_id))
    return redirect(url_for('portal.settings') + '#security')


@portal_bp.route('/settings/staff/<slug>/pause', methods=['POST'])
@login_required
def settings_staff_pause(slug):
    staff = query_one(
        "SELECT * FROM hired_staff WHERE client_id=? AND staff_slug=?",
        (g.client_id, slug)
    )
    if not staff:
        return redirect(url_for('portal.settings'))
    new_status = 'paused' if staff['status'] == 'active' else 'active'
    execute_commit(
        'UPDATE hired_staff SET status=? WHERE client_id=? AND staff_slug=?',
        (new_status, g.client_id, slug)
    )
    return redirect(url_for('portal.settings') + '#staff')


@portal_bp.route('/settings/staff/<slug>/let-go', methods=['POST'])
@login_required
def settings_staff_let_go(slug):
    execute_commit(
        "UPDATE hired_staff SET status='let-go' WHERE client_id=? AND staff_slug=?",
        (g.client_id, slug)
    )
    return redirect(url_for('portal.dashboard'))


# ── GET /add-staff ─────────────────────────────────────────────
# Renders the in-portal staff marketplace. Passes the list of
# available staff and the slugs the hirer already has so the
# template can grey-out already-hired cards.

# Build the available-staff list for the template from staff_common
AVAILABLE_STAFF = [
    {
        'slug':        slug,
        'name':        STAFF_REGISTRY[slug]['name'],
        'role':        STAFF_REGISTRY[slug].get('vertical', ''),
        'mode':        STAFF_REGISTRY[slug]['mode'],
        'description': STAFF_REGISTRY[slug].get('description', ''),
    }
    for slug in AVAILABLE_STAFF_SLUGS
]

STAFF_INTAKE_MESSAGES = {
    'iris':              '{name} is now monitoring {states} for {firm}. '
                         'She will alert you when a regulatory change affects your business.',
    'probe':             'Probe has been added to your portal for {firm}. '
                         'Your Experiment Brief will be ready within 24 hours.',
    'tdd-practice-team': 'The TDD Practice Team has received your brief for {firm}. '
                         'Outputs will appear in your portal as they are delivered.',
}


@portal_bp.route('/add-staff', methods=['GET'])
@login_required
def add_staff():
    client = _get_client()
    hired = _get_hired_staff(g.client_id)
    already_hired_slugs = {s['staff_slug'] for s in hired}
    return render_template(
        'add_staff.html',
        client=client,
        available_staff=AVAILABLE_STAFF,
        already_hired_slugs=already_hired_slugs,
    )


# ── POST /add-staff ────────────────────────────────────────────
# Receives JSON from the in-portal hire form. Uses the session
# identity (no re-entry of name/email/firm). Calls the same
# /api/register logic directly rather than going over HTTP.

@portal_bp.route('/add-staff', methods=['POST'])
@login_required
def add_staff_post():
    data = request.get_json(silent=True) or {}
    staff_slug = (data.get('staff_slug') or '').strip().lower()

    if not staff_slug:
        return jsonify({'success': False, 'error': 'staff_slug is required'}), 400

    staff_meta = STAFF_REGISTRY.get(staff_slug)
    if not staff_meta:
        return jsonify({'success': False, 'error': f'Unknown staff: {staff_slug}'}), 400

    # Check not already hired
    already = query_one(
        "SELECT id FROM hired_staff WHERE client_id=? AND staff_slug=?",
        (g.client_id, staff_slug)
    )
    if already:
        return jsonify({'success': False,
                        'error': f'{staff_meta["name"]} is already on your team'}), 409

    # Validate staff-specific required fields
    if staff_slug == 'iris':
        states = (data.get('states') or '').strip()
        if not states:
            return jsonify({'success': False, 'error': 'Please enter at least one state for Iris to monitor.'}), 400
    else:
        states = ''

    if staff_slug == 'probe':
        if not data.get('org_type'):
            return jsonify({'success': False, 'error': 'Organisation type is required.'}), 400
        if not (data.get('hypothesis') or '').strip():
            return jsonify({'success': False, 'error': 'Innovation hypothesis is required.'}), 400

    if staff_slug == 'tdd-practice-team':
        if not (data.get('target_company') or '').strip():
            return jsonify({'success': False, 'error': 'Target company is required.'}), 400
        if not data.get('engagement_type'):
            return jsonify({'success': False, 'error': 'Engagement type is required.'}), 400
        if not (data.get('brief') or '').strip():
            return jsonify({'success': False, 'error': 'Brief is required.'}), 400

    # Build settings payload
    reserved = {'staff_slug'}
    extra_settings = {k: v for k, v in data.items() if k not in reserved}
    if staff_slug == 'iris':
        extra_settings['jurisdictions'] = [s.strip() for s in states.split(',') if s.strip()]

    insert(
        '''INSERT INTO hired_staff
           (client_id, staff_name, staff_slug, vertical, mode, settings)
           VALUES (?,?,?,?,?,?)''',
        (
            g.client_id,
            staff_meta['name'],
            staff_slug,
            staff_meta['vertical'],
            staff_meta['mode'],
            json.dumps(extra_settings),
        )
    )

    # Fetch client details for the confirmation email
    client = _get_client()
    send_staff_added_email(
        app_config=current_app.config,
        logger=current_app.logger,
        to_email=client['email'],
        name=client['primary_contact_name'],
        firm_name=client['company_name'],
        staff_slug=staff_slug,
        staff_name=staff_meta['name'],
        states=states,
    )

    current_app.logger.info(
        f'Staff added via portal: client_id={g.client_id} staff={staff_slug}'
    )

    # Build a human-readable confirmation message
    tmpl = STAFF_INTAKE_MESSAGES.get(
        staff_slug,
        '{name} has been added to your portal for {firm}.'
    )
    msg = tmpl.format(
        name=staff_meta['name'],
        firm=client['company_name'],
        states=states,
    )

    return jsonify({'success': True, 'message': msg}), 200
