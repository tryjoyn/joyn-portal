"""
auth/routes_updated.py
Updated authentication routes with iris-agent integration.

This file should replace auth/routes.py after review.
"""

import os
import logging
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
logger = logging.getLogger(__name__)


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

    # Register with iris-agent if not already registered
    client_dict = dict(client)
    iris_client_id = client_dict.get('iris_client_id')
    
    if not iris_client_id:
        try:
            from iris_integration import register_client
            iris_response = register_client(
                email=email,
                name=client_dict.get('primary_contact_name', 'User'),
                portal_client_id=client_dict['id'],
                states=client_dict.get('states', '').split(',') if client_dict.get('states') else [],
                lob='both'
            )
            iris_client_id = iris_response.get('client_id')
            if iris_client_id:
                execute_commit(
                    'UPDATE clients SET iris_client_id=?, iris_registered_at=CURRENT_TIMESTAMP WHERE id=?',
                    (iris_client_id, client_dict['id'])
                )
                logger.info(f'Registered {email} with iris-agent: {iris_client_id}')
        except Exception as e:
            logger.warning(f'Failed to register {email} with iris-agent: {e}')
            # Don't fail login if iris-agent is down

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
    """User sets password on first login."""
    password = request.form.get('password') or ''
    password_confirm = request.form.get('password_confirm') or ''

    if not password or not password_confirm:
        return render_template('set_password.html', error='Both fields are required.'), 400

    if password != password_confirm:
        return render_template('set_password.html', error='Passwords do not match.'), 400

    if len(password) < 8:
        return render_template('set_password.html', error='Password must be at least 8 characters.'), 400

    # Update password and clear first_login flag
    password_hash = hash_password(password)
    execute_commit(
        'UPDATE clients SET password_hash=?, first_login=0 WHERE id=?',
        (password_hash, g.client_id)
    )

    return redirect(url_for('portal.dashboard'))


# ── POST /forgot-password ──────────────────────────────────────

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password_post():
    """Send password reset email."""
    email = (request.form.get('email') or '').strip().lower()

    if not email:
        return render_template('login.html', error='Email is required.', forgot=True), 400

    client = query_one('SELECT * FROM clients WHERE email=?', (email,))

    if not client:
        # Don't reveal if email exists
        return render_template('login.html', error='If that email is registered, you will receive a reset link.', forgot=True), 200

    # Generate reset token
    reset_token = generate_reset_token(client['id'])

    # Send email (implement SendGrid integration here)
    # TODO: send_password_reset_email(email, reset_token)

    return render_template('login.html', error='Password reset link sent to your email.', forgot=True), 200
