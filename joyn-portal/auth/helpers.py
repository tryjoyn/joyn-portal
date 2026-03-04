import os
import jwt
import bcrypt
import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import request, redirect, url_for, g, current_app, jsonify


# ── Password ───────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt(rounds=12)).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


# ── JWT ────────────────────────────────────────────────────────

def _jwt_secret():
    return current_app.config['JWT_SECRET_KEY']


def create_access_token(client_id: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        'sub': str(client_id),
        'iat': now,
        'exp': now + timedelta(days=7),
        'type': 'access',
    }
    return jwt.encode(payload, _jwt_secret(), algorithm='HS256')


def decode_token(token: str) -> dict:
    return jwt.decode(token, _jwt_secret(), algorithms=['HS256'])


# ── Decorators ─────────────────────────────────────────────────

def login_required(f):
    """Protects portal HTML routes — redirects to /login if not authed."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get(current_app.config.get('JWT_COOKIE_NAME', 'joyn_session'))
        if not token:
            return redirect(url_for('auth.login'))
        try:
            payload = decode_token(token)
            g.client_id = int(payload['sub'])
        except jwt.ExpiredSignatureError:
            resp = redirect(url_for('auth.login'))
            resp.delete_cookie(current_app.config.get('JWT_COOKIE_NAME', 'joyn_session'))
            return resp
        except jwt.InvalidTokenError:
            resp = redirect(url_for('auth.login'))
            resp.delete_cookie(current_app.config.get('JWT_COOKIE_NAME', 'joyn_session'))
            return resp
        return f(*args, **kwargs)
    return decorated


def api_login_required(f):
    """Protects JSON API routes — returns 401 JSON if not authed."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get(current_app.config.get('JWT_COOKIE_NAME', 'joyn_session'))
        if not token:
            return jsonify({'error': 'Authentication required'}), 401
        try:
            payload = decode_token(token)
            g.client_id = int(payload['sub'])
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Session expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        return f(*args, **kwargs)
    return decorated


def portal_secret_required(f):
    """Protects external logging endpoints — validates X-Joyn-Secret header."""
    @wraps(f)
    def decorated(*args, **kwargs):
        expected = current_app.config.get('JOYN_PORTAL_SECRET', '')
        provided = request.headers.get('X-Joyn-Secret', '')
        # Also accept API key in Authorization: Bearer header (backwards compat)
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            provided_key = auth_header[7:]
            from data.db import query_one
            key_hash = hashlib.sha256(provided_key.encode()).hexdigest()
            key_row = query_one(
                'SELECT id FROM api_keys WHERE key_hash=? AND revoked_at IS NULL',
                (key_hash,)
            )
            if key_row:
                from data.db import execute_commit
                execute_commit('UPDATE api_keys SET last_used=CURRENT_TIMESTAMP WHERE id=?', (key_row['id'],))
                return f(*args, **kwargs)
        if not provided or not expected or provided != expected:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated


# ── Reset tokens ───────────────────────────────────────────────

def generate_reset_token() -> tuple[str, str]:
    """Returns (plain_token, hashed_token)."""
    token = secrets.token_urlsafe(32)
    hashed = hashlib.sha256(token.encode()).hexdigest()
    return token, hashed
