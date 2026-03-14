"""
iris_integration.py
Integration layer between joyn-portal and iris-agent 2.0

This module handles all communication with the iris-agent backend:
- Client registration when users sign in
- Fetching briefings for the dashboard
- Updating client preferences
- Pause/resume communications
"""

import os
import logging
import requests
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Configuration
IRIS_BASE_URL = os.environ.get('IRIS_BASE_URL', 'https://iris-production-5916.up.railway.app')
IRIS_API_KEY = os.environ.get('IRIS_API_KEY', '')

# Timeout for all iris-agent requests
REQUEST_TIMEOUT = 10


class IrisIntegrationError(Exception):
    """Raised when iris-agent integration fails."""
    pass


def _make_request(
    method: str,
    endpoint: str,
    data: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Make an authenticated request to iris-agent.
    
    Args:
        method: HTTP method (GET, POST, PATCH, DELETE)
        endpoint: API endpoint path (e.g., '/api/register')
        data: JSON payload for POST/PATCH requests
        params: Query parameters for GET requests
    
    Returns:
        Parsed JSON response
    
    Raises:
        IrisIntegrationError: If the request fails
    """
    url = f'{IRIS_BASE_URL}{endpoint}'
    headers = {
        'Content-Type': 'application/json',
        'X-Internal-Key': IRIS_API_KEY,
    }
    
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers, params=params, timeout=REQUEST_TIMEOUT)
        elif method == 'POST':
            response = requests.post(url, headers=headers, json=data, timeout=REQUEST_TIMEOUT)
        elif method == 'PATCH':
            response = requests.patch(url, headers=headers, json=data, timeout=REQUEST_TIMEOUT)
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers, timeout=REQUEST_TIMEOUT)
        else:
            raise ValueError(f'Unsupported HTTP method: {method}')
        
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.Timeout:
        logger.error(f'iris-agent request timeout: {method} {endpoint}')
        raise IrisIntegrationError(f'iris-agent request timeout')
    except requests.exceptions.ConnectionError as e:
        logger.error(f'iris-agent connection error: {method} {endpoint} — {e}')
        raise IrisIntegrationError(f'Cannot reach iris-agent')
    except requests.exceptions.HTTPError as e:
        logger.error(f'iris-agent HTTP error: {method} {endpoint} — {e.response.status_code}')
        raise IrisIntegrationError(f'iris-agent returned {e.response.status_code}')
    except Exception as e:
        logger.error(f'iris-agent request error: {method} {endpoint} — {e}')
        raise IrisIntegrationError(f'iris-agent request failed: {str(e)}')


def register_client(
    email: str,
    name: str,
    portal_client_id: int,
    states: Optional[list] = None,
    lob: str = 'both',
) -> Dict[str, Any]:
    """
    Register a new client with iris-agent.
    
    Called when a user signs in to the portal for the first time.
    
    Args:
        email: Client email address
        name: Client full name
        portal_client_id: Portal user ID (for traceability)
        states: List of state codes to monitor (default: [])
        lob: Line of business ('personal', 'commercial', 'both')
    
    Returns:
        Response from iris-agent with client_id
    
    Raises:
        IrisIntegrationError: If registration fails
    """
    payload = {
        'email': email,
        'name': name,
        'portal_client_id': portal_client_id,
        'states': states or [],
        'lob': lob,
    }
    
    try:
        response = _make_request('POST', '/api/register', data=payload)
        logger.info(f'Registered client with iris-agent: {email}')
        return response
    except IrisIntegrationError:
        # Don't fail portal login if iris-agent is down
        logger.warning(f'Failed to register {email} with iris-agent, continuing anyway')
        return {'client_id': None, 'status': 'offline'}


def get_client_profile(iris_client_id: str) -> Dict[str, Any]:
    """
    Get client profile from iris-agent.
    
    Args:
        iris_client_id: Client ID in iris-agent
    
    Returns:
        Client profile data
    
    Raises:
        IrisIntegrationError: If request fails
    """
    return _make_request('GET', f'/api/client/{iris_client_id}')


def get_client_metrics(iris_client_id: str) -> Dict[str, Any]:
    """
    Get client metrics and briefings from iris-agent.
    
    Used to populate the portal dashboard with briefing data.
    
    Args:
        iris_client_id: Client ID in iris-agent
    
    Returns:
        Metrics including briefings, severity distribution, etc.
    
    Raises:
        IrisIntegrationError: If request fails
    """
    return _make_request('GET', f'/api/client/{iris_client_id}/metrics')


def get_client_calibration(iris_client_id: str) -> Dict[str, Any]:
    """
    Get client calibration history from iris-agent.
    
    Used to show how Iris has learned the client's preferences.
    
    Args:
        iris_client_id: Client ID in iris-agent
    
    Returns:
        Calibration data
    
    Raises:
        IrisIntegrationError: If request fails
    """
    return _make_request('GET', f'/api/client/{iris_client_id}/calibration')


def update_client_profile(
    iris_client_id: str,
    states: Optional[list] = None,
    lob: Optional[str] = None,
    briefing_cadence: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Update client preferences in iris-agent.
    
    Called when user updates settings in the portal.
    
    Args:
        iris_client_id: Client ID in iris-agent
        states: List of state codes to monitor
        lob: Line of business
        briefing_cadence: 'daily' or 'realtime'
    
    Returns:
        Updated client profile
    
    Raises:
        IrisIntegrationError: If request fails
    """
    payload = {}
    if states is not None:
        payload['states_subscribed'] = states
    if lob is not None:
        payload['lob'] = lob
    if briefing_cadence is not None:
        payload['briefing_cadence'] = briefing_cadence
    
    return _make_request('PATCH', f'/api/client/{iris_client_id}/update', data=payload)


def pause_client(iris_client_id: str) -> Dict[str, Any]:
    """
    Pause communications for a client.
    
    Args:
        iris_client_id: Client ID in iris-agent
    
    Returns:
        Updated client status
    
    Raises:
        IrisIntegrationError: If request fails
    """
    return _make_request('POST', f'/api/client/{iris_client_id}/pause')


def resume_client(iris_client_id: str) -> Dict[str, Any]:
    """
    Resume communications for a client.
    
    Args:
        iris_client_id: Client ID in iris-agent
    
    Returns:
        Updated client status
    
    Raises:
        IrisIntegrationError: If request fails
    """
    return _make_request('POST', f'/api/client/{iris_client_id}/resume')


def delete_client(iris_client_id: str) -> Dict[str, Any]:
    """
    Delete client and schedule data deletion.
    
    Implements GDPR Right 05 (clean exit + 30-day deletion).
    
    Args:
        iris_client_id: Client ID in iris-agent
    
    Returns:
        Deletion status
    
    Raises:
        IrisIntegrationError: If request fails
    """
    return _make_request('DELETE', f'/api/client/{iris_client_id}')


def export_client_data(iris_client_id: str) -> Dict[str, Any]:
    """
    Export all client data from iris-agent.
    
    Implements GDPR Right 05 (data export).
    
    Args:
        iris_client_id: Client ID in iris-agent
    
    Returns:
        Full client corpus export
    
    Raises:
        IrisIntegrationError: If request fails
    """
    return _make_request('GET', f'/api/client/{iris_client_id}/export')


def health_check() -> bool:
    """
    Check if iris-agent is healthy.
    
    Returns:
        True if iris-agent is responding, False otherwise
    """
    try:
        response = _make_request('GET', '/api/health')
        return response.get('status') == 'ok'
    except IrisIntegrationError:
        return False
