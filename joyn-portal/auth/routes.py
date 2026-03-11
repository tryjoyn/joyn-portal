from flask import (
    Blueprint, render_template, request, redirect,
    url_for, make_response, current_app, g
)
from data.db import query_one, execute_commit
from auth.helpers import (
    verify_password, hash_password, create_access_token,
    login_required, generate_reset_token
)

auth_bp = Blueprint('auth', __name__)

COOKIE_NAME = 'joyn_session'


def _cookie_name():
    return current_app.config.get('JWT_COOKIE_NAME', COOKIE_NAME)


# ── GET /login ─────────────────────────────────────────────────

@auth_bp.route('/login', methods=['GET'])
def login():
    # Already logged in → go to dashboard
    token = request.cookies.get(_cookie_name())
    if token:
        try:
            from auth.helpers import decode_token
            decode_token(token)
            return redirect(url_for('portal.dashboard'))
        except Exception:
            pass
    return render_template('login.html', error=None)


# ── POST /login ────────────────────────────────────────────────

@auth_bp.route('/login', methods=['POST'])
def login_post():
    email = (request.form.get('email') or '').strip().lower()
    password = request.form.get('password') or ''

    if not email or not password:
        return render_template('login.html', error='Email and password are required.'), 400

    client = query_one('SELECT * FROM clients WHERE email=?', (email,))

    if not client or not verify_password(password, client['password_hash']):
        return render_template('login.html', error='Incorrect email or password.'), 401

    # Update last login
    execute_commit('UPDATE clients SET last_login=CURRENT_TIMESTAMP WHERE id=?', (client['id'],))

    token = create_access_token(client['id'])

    # first_login=1 → force password change before dashboard
    first_login = dict(client).get('first_login', 0)
    dest = url_for('auth.set_password') if first_login else url_for('portal.dashboard')

    resp = make_response(redirect(dest))
    resp.set_cookie(
        _cookie_name(),
        token,
        httponly=True,
        samesite='Lax',
        secure=current_app.config.get('SESSION_COOKIE_SECURE', False),
        max_age=7 * 24 * 60 * 60,  # 7 days
    )
    return resp


# ── GET /logout ────────────────────────────────────────────────

@auth_bp.route('/logout')
def logout():
    resp = make_response(redirect(url_for('auth.login')))
    resp.delete_cookie(_cookie_name())
    return resp


# ── GET /forgot-password ───────────────────────────────────────

@auth_bp.route('/forgot-password', methods=['GET'])
def forgot_password():
    return render_template('login.html', error=None, forgot=True)


# ── GET /set-password ──────────────────────────────────────────

@auth_bp.route('/set-password', methods=['GET'])
@login_required
def set_password():
    return render_template('set_password.html', error=None)


# ── POST /set-password ──────────────────────────────────────────

@auth_bp.route('/set-password', methods=['POST'])
@login_required
def set_password_post():
    new_pw      = request.form.get('new_password', '')
    confirm_pw  = request.form.get('confirm_password', '')

    if len(new_pw) < 12:
        return render_template('set_password.html',
                               error='Password must be at least 12 characters.'), 400
    if new_pw != confirm_pw:
        return render_template('set_password.html',
                               error='Passwords do not match.'), 400

    execute_commit(
        'UPDATE clients SET password_hash=?, first_login=0 WHERE id=?',
        (hash_password(new_pw), g.client_id)
    )
    return redirect(url_for('portal.dashboard'))


# ── POST /forgot-password ──────────────────────────────────────

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password_post():
    email = (request.form.get('email') or '').strip().lower()
    # Always respond the same way to prevent enumeration
    if email:
        client = query_one('SELECT id FROM clients WHERE email=?', (email,))
        if client:
            plain_token, hashed_token = generate_reset_token()
            from datetime import datetime, timedelta
            expires = datetime.utcnow() + timedelta(hours=2)
            from data.db import insert
            insert(
                'INSERT INTO password_reset_tokens (client_id, token_hash, expires_at) VALUES (?,?,?)',
                (client['id'], hashed_token, expires.isoformat())
            )
            # TODO: send email via SendGrid
    return render_template('login.html',
                           error=None,
                           info='If that email is registered, a reset link has been sent.')
