"""
portal/routes_iris_updated.py
Updated portal routes with iris-agent briefing integration.

This file adds iris-agent briefing display to the dashboard.
Merge with existing portal/routes.py after review.
"""

import json
import logging
from datetime import datetime
from flask import Blueprint, render_template, g, jsonify, request, current_app
from data.db import query_one, query, row_to_dict, rows_to_list
from auth.helpers import login_required
from iris_integration import (
    get_client_metrics, get_client_profile, update_client_profile,
    pause_client, resume_client, IrisIntegrationError
)

logger = logging.getLogger(__name__)

portal_bp = Blueprint('portal', __name__)


def _get_client():
    """Get current logged-in client."""
    return row_to_dict(query_one('SELECT * FROM clients WHERE id=?', (g.client_id,)))


def _get_iris_briefings(iris_client_id):
    """
    Fetch briefings from iris-agent for the dashboard.
    
    Returns empty list if iris-agent is unavailable.
    """
    if not iris_client_id:
        return []
    
    try:
        metrics = get_client_metrics(iris_client_id)
        briefings = metrics.get('briefings', [])
        
        # Format briefings for display
        formatted = []
        for b in briefings[:10]:  # Show top 10
            formatted.append({
                'id': b.get('id'),
                'state': b.get('state'),
                'title': b.get('title'),
                'severity': b.get('severity_label', 'Low'),
                'severity_score': b.get('severity_score', 1),
                'reasoning': b.get('reasoning'),
                'citation': b.get('citation'),
                'deadline': b.get('compliance_deadline'),
                'source_url': b.get('source_url'),
                'created_at': b.get('created_at'),
            })
        
        return formatted
    
    except IrisIntegrationError as e:
        logger.warning(f'Failed to fetch iris briefings for {iris_client_id}: {e}')
        return []
    except Exception as e:
        logger.error(f'Unexpected error fetching iris briefings: {e}')
        return []


def _get_iris_stats(iris_client_id):
    """
    Get iris-agent statistics for the dashboard sidebar.
    
    Returns empty dict if iris-agent is unavailable.
    """
    if not iris_client_id:
        return {}
    
    try:
        metrics = get_client_metrics(iris_client_id)
        
        briefings = metrics.get('briefings', [])
        severity_dist = metrics.get('severity_distribution', {})
        
        return {
            'total_briefings': len(briefings),
            'critical_count': severity_dist.get('Critical', 0),
            'high_count': severity_dist.get('High', 0),
            'medium_count': severity_dist.get('Medium', 0),
            'low_count': severity_dist.get('Low', 0),
            'last_crawl': metrics.get('last_crawl_at'),
            'next_crawl': metrics.get('next_crawl_at'),
        }
    
    except IrisIntegrationError as e:
        logger.warning(f'Failed to fetch iris stats for {iris_client_id}: {e}')
        return {}
    except Exception as e:
        logger.error(f'Unexpected error fetching iris stats: {e}')
        return {}


# ── GET /dashboard ─────────────────────────────────────────────

@portal_bp.route('/dashboard')
@login_required
def dashboard():
    """
    Portal dashboard with iris-agent briefings.
    """
    client = _get_client()
    iris_client_id = client.get('iris_client_id')
    
    # Fetch iris briefings
    iris_briefings = _get_iris_briefings(iris_client_id)
    iris_stats = _get_iris_stats(iris_client_id)
    
    return render_template(
        'dashboard.html',
        client=client,
        iris_briefings=iris_briefings,
        iris_stats=iris_stats,
        iris_connected=bool(iris_client_id),
        now=datetime.utcnow(),
    )


# ── GET /staff/iris ────────────────────────────────────────────

@portal_bp.route('/staff/iris')
@login_required
def staff_iris():
    """
    Iris staff detail page with briefings and settings.
    """
    client = _get_client()
    iris_client_id = client.get('iris_client_id')
    
    if not iris_client_id:
        # Redirect to dashboard if iris not registered
        return redirect(url_for('portal.dashboard'))
    
    # Fetch iris profile and briefings
    try:
        iris_profile = get_client_profile(iris_client_id)
        iris_briefings = _get_iris_briefings(iris_client_id)
        iris_stats = _get_iris_stats(iris_client_id)
    except IrisIntegrationError as e:
        logger.warning(f'Failed to fetch iris profile: {e}')
        iris_profile = {}
        iris_briefings = []
        iris_stats = {}
    
    # Parse settings
    settings = iris_profile.get('settings', {})
    if isinstance(settings, str):
        try:
            settings = json.loads(settings)
        except (ValueError, TypeError):
            settings = {}
    
    return render_template(
        'staff_iris.html',
        client=client,
        iris_profile=iris_profile,
        iris_briefings=iris_briefings,
        iris_stats=iris_stats,
        settings=settings,
        now=datetime.utcnow(),
    )


# ── API: GET /api/iris/briefings ───────────────────────────────

@portal_bp.route('/api/iris/briefings', methods=['GET'])
@login_required
def api_iris_briefings():
    """
    JSON API to fetch iris briefings.
    Used by frontend to refresh briefings without page reload.
    """
    client = _get_client()
    iris_client_id = client.get('iris_client_id')
    
    if not iris_client_id:
        return jsonify({'error': 'iris not registered'}), 400
    
    try:
        briefings = _get_iris_briefings(iris_client_id)
        return jsonify({'briefings': briefings}), 200
    except Exception as e:
        logger.error(f'Failed to fetch iris briefings: {e}')
        return jsonify({'error': 'failed to fetch briefings'}), 500


# ── API: PATCH /api/iris/settings ─────────────────────────────

@portal_bp.route('/api/iris/settings', methods=['PATCH'])
@login_required
def api_iris_settings():
    """
    Update iris-agent settings.
    
    Expects JSON:
    {
        "states": ["FL", "NY", ...],
        "lob": "personal|commercial|both",
        "briefing_cadence": "daily|realtime"
    }
    """
    client = _get_client()
    iris_client_id = client.get('iris_client_id')
    
    if not iris_client_id:
        return jsonify({'error': 'iris not registered'}), 400
    
    data = request.get_json(force=True, silent=True) or {}
    
    try:
        # Update iris-agent profile
        iris_response = update_client_profile(
            iris_client_id=iris_client_id,
            states=data.get('states'),
            lob=data.get('lob'),
            briefing_cadence=data.get('briefing_cadence'),
        )
        
        logger.info(f'Updated iris settings for client {g.client_id}')
        return jsonify({'status': 'ok', 'profile': iris_response}), 200
    
    except IrisIntegrationError as e:
        logger.error(f'Failed to update iris settings: {e}')
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        logger.error(f'Unexpected error updating iris settings: {e}')
        return jsonify({'error': 'unexpected error'}), 500


# ── API: POST /api/iris/pause ──────────────────────────────────

@portal_bp.route('/api/iris/pause', methods=['POST'])
@login_required
def api_iris_pause():
    """
    Pause iris communications.
    """
    client = _get_client()
    iris_client_id = client.get('iris_client_id')
    
    if not iris_client_id:
        return jsonify({'error': 'iris not registered'}), 400
    
    try:
        iris_response = pause_client(iris_client_id)
        logger.info(f'Paused iris for client {g.client_id}')
        return jsonify({'status': 'paused'}), 200
    except IrisIntegrationError as e:
        logger.error(f'Failed to pause iris: {e}')
        return jsonify({'error': str(e)}), 500


# ── API: POST /api/iris/resume ─────────────────────────────────

@portal_bp.route('/api/iris/resume', methods=['POST'])
@login_required
def api_iris_resume():
    """
    Resume iris communications.
    """
    client = _get_client()
    iris_client_id = client.get('iris_client_id')
    
    if not iris_client_id:
        return jsonify({'error': 'iris not registered'}), 400
    
    try:
        iris_response = resume_client(iris_client_id)
        logger.info(f'Resumed iris for client {g.client_id}')
        return jsonify({'status': 'resumed'}), 200
    except IrisIntegrationError as e:
        logger.error(f'Failed to resume iris: {e}')
        return jsonify({'error': str(e)}), 500
