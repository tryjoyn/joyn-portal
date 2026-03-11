import os
import logging
from logging.handlers import RotatingFileHandler

import stripe
from flask import Flask, redirect, url_for, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

# ── Observability: initialise tracer before app creation ──────────────────────
# Importing get_tracer() here triggers TracerProvider setup so that spans
# cover the full application lifecycle, not just after blueprints register.
try:
    from observability.tracing import get_tracer as _init_tracer  # noqa: F401
except Exception as _otel_init_err:
    logging.getLogger(__name__).warning(
        'OpenTelemetry tracer init skipped: %s', _otel_init_err
    )


def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')

    # ── Config ────────────────────────────────────────────────
    from config import get_config
    app.config.from_object(get_config())

    # ── Logging ───────────────────────────────────────────────
    os.makedirs('logs', exist_ok=True)
    handler = RotatingFileHandler('logs/portal.log', maxBytes=10 * 1024 * 1024, backupCount=5)
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter(
        '[%(asctime)s] %(levelname)s %(name)s: %(message)s'
    ))
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)

    # ── Database ──────────────────────────────────────────────
    from data.db import init_app as db_init_app, init_db
    db_init_app(app)

    with app.app_context():
        init_db()

    # ── CORS ──────────────────────────────────────────────────
    cors_origins = app.config.get('CORS_ORIGINS', '*')
    if isinstance(cors_origins, str) and ',' in cors_origins:
        cors_origins = [o.strip() for o in cors_origins.split(',')]
    CORS(app, origins=cors_origins)

    # ── Stripe ────────────────────────────────────────────────
    stripe.api_key = app.config.get('STRIPE_SECRET_KEY', '')

    # ── Blueprints ────────────────────────────────────────────
    from auth.routes import auth_bp
    from portal.routes import portal_bp
    from api.routes import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(portal_bp)
    app.register_blueprint(api_bp)

    # ── Observability: instrument Flask HTTP requests ─────────
    try:
        from observability.flask_middleware import register_flask_instrumentation
        register_flask_instrumentation(app)
    except Exception as _otel_err:
        app.logger.warning('OTel Flask instrumentation skipped: %s', _otel_err)

    # ── Root redirect ─────────────────────────────────────────
    @app.route('/')
    def index():
        return redirect(url_for('portal.dashboard'))

    # ── Health check (used by Railway / load balancers) ───────
    @app.route('/health')
    def health():
        return jsonify({'status': 'ok'}), 200

    # ── Error handlers ─────────────────────────────────────────
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({'error': 'Bad request'}), 400

    @app.errorhandler(401)
    def unauthorized(e):
        return jsonify({'error': 'Unauthorized'}), 401

    @app.errorhandler(403)
    def forbidden(e):
        return jsonify({'error': 'Forbidden'}), 403

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'error': 'Not found'}), 404

    @app.errorhandler(500)
    def server_error(e):
        app.logger.error(f'Server error: {e}')
        return jsonify({'error': 'Internal server error'}), 500

    # ── CLI: init-db ──────────────────────────────────────────
    @app.cli.command('init-db')
    def cli_init_db():
        with app.app_context():
            init_db()
        print('Database initialised.')

    # ── CLI: create-client ────────────────────────────────────
    @app.cli.command('create-client')
    def cli_create_client():
        import click
        email = click.prompt('Email')
        password = click.prompt('Password', hide_input=True)
        company = click.prompt('Company name')
        from auth.helpers import hash_password
        from data.db import insert
        with app.app_context():
            cid = insert(
                'INSERT INTO clients (email, password_hash, company_name, subscription_status) VALUES (?,?,?,?)',
                (email.strip().lower(), hash_password(password), company, 'active')
            )
        print(f'Client created — id={cid}')

    return app


app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
