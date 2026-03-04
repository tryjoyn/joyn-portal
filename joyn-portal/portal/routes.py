import json
from datetime import datetime
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, g, jsonify, flash
)
from data.db import query_one, query, execute_commit, row_to_dict, rows_to_list
from auth.helpers import login_required, hash_password, verify_password

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
