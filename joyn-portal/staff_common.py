"""
staff_common.py
───────────────
Shared staff registry and email helpers.
Imported by both api/routes.py and portal/routes.py.
No Flask blueprint here — pure utility module to avoid circular imports.
"""
import json as _json

# ── Staff registry ─────────────────────────────────────────────
# Single source of truth for slug → metadata.
# Add new staff here; both the public hire API and the in-portal
# add-staff flow read from this dict.

STAFF_REGISTRY = {
    'iris': {
        'name':     'Iris',
        'vertical': 'Insurance',
        'mode':     'autonomous',
        'description': (
            'Monitors insurance regulation continuously across US states. '
            'Alerts you when a filing, bulletin, or rule change affects your lines of business.'
        ),
    },
    'probe': {
        'name':     'Probe',
        'vertical': 'Insurance',
        'mode':     'supervised',
        'description': (
            'Runs structured innovation experiments for insurance organisations. '
            'Takes your hypothesis, builds an Experiment Brief, and delivers a '
            'Landscape Memo and Red Team Memo within 24 hours.'
        ),
    },
    'tdd-practice-team': {
        'name':     'TDD Practice Team',
        'vertical': 'Technology',
        'mode':     'supervised',
        'description': (
            'Eight-agent team that delivers a full technology due diligence report. '
            'Covers architecture, security, scalability, and team capability for any software target.'
        ),
    },
    'creator-application': {
        'name':     'Creator Application',
        'vertical': 'Platform',
        'mode':     'supervised',
        'description': (
            'Apply to build AI staff on the Joyn platform.'
        ),
    },
}

# ── Available staff for the in-portal add-staff page ──────────
# Subset of STAFF_REGISTRY — excludes internal/meta slugs.
AVAILABLE_STAFF_SLUGS = ['iris', 'probe', 'tdd-practice-team']


# ── Email helpers ──────────────────────────────────────────────
# Both functions use current_app from Flask, which is only valid
# inside a request or app context — safe to call from route handlers.

def send_welcome_email(
        app_config, logger,
        to_email, name, firm_name,
        staff_slug, staff_name,
        states, temp_password):
    """Sent when a brand-new account is created. Includes temp password."""
    api_key = app_config.get('SENDGRID_API_KEY', '')
    if not api_key:
        logger.warning('SendGrid not configured — welcome email not sent')
        return

    state_list_str = ', '.join(s.strip() for s in states.split(',') if s.strip()) if states else ''

    STAFF_COPY = {
        'iris': (
            f'Iris is now monitoring {state_list_str} for {firm_name}. '
            'She is tracking regulatory changes and will alert you when something matters.'
        ),
        'probe': (
            f'Probe is ready to begin your innovation experiment for {firm_name}. '
            'Log in to your portal to review your Experiment Brief and track progress.'
        ),
        'tdd-practice-team': (
            f'The TDD Practice Team has received your brief for {firm_name}. '
            'Log in to your portal to track progress and review outputs as they are delivered.'
        ),
        'creator-application': (
            f'Your creator application for {firm_name} has been received. '
            'Log in to your portal to track your application status.'
        ),
    }
    body_copy = STAFF_COPY.get(
        staff_slug,
        f'{staff_name} is now active for {firm_name}. Log in to your portal to get started.'
    )

    plain = (
        f'Hi {name},\n\n'
        f'{body_copy}\n\n'
        f'Log in to your portal:\n'
        f'https://app.tryjoyn.me/login\n\n'
        f'Your login details:\n'
        f'  Email:              {to_email}\n'
        f'  Temporary password: {temp_password}\n\n'
        f'You will be asked to set a new password the first time you sign in.\n\n'
        f'Questions? Reply to this email or write to hire@tryjoyn.me\n\n'
        f'\u2014 {staff_name} \u00b7 Joyn'
    )

    html = (
        '<!DOCTYPE html>'
        '<html lang="en"><head><meta charset="UTF-8"></head>'
        '<body style="margin:0;padding:0;background:#fafaf8;font-family:Arial,sans-serif;color:#111110;">'
        '<table width="100%" cellpadding="0" cellspacing="0">'
        '<tr><td align="center" style="padding:3rem 1rem;">'
        '<table width="100%" style="max-width:560px;">'
        '<tr><td style="border-bottom:1px solid #e8e4dc;padding-bottom:1.5rem;">'
        '<span style="font-family:\'Courier New\',monospace;font-size:0.9rem;font-weight:bold;letter-spacing:0.12em;color:#111110;">JOYN.</span>'
        '</td></tr>'
        '<tr><td style="padding-top:1.75rem;">'
        f'<p style="font-family:\'Courier New\',monospace;font-size:0.65rem;letter-spacing:0.1em;text-transform:uppercase;color:#8B6914;margin:0 0 0.5rem 0;">\u2014 {staff_name}</p>'
        '</td></tr>'
        '<tr><td>'
        f'<h1 style="font-size:2rem;font-weight:300;margin:0 0 1.25rem 0;color:#111110;line-height:1.2;">Hi {name},</h1>'
        f'<p style="font-size:0.95rem;color:#3f3f3e;line-height:1.8;margin:0 0 1.75rem 0;">{body_copy}</p>'
        '</td></tr>'
        '<tr><td style="padding-bottom:1.75rem;">'
        '<a href="https://app.tryjoyn.me/login" '
        'style="display:inline-block;font-family:\'Courier New\',monospace;font-size:0.75rem;font-weight:bold;'
        'letter-spacing:0.1em;text-transform:uppercase;padding:0.875rem 2rem;background:#111110;color:#fafaf8;text-decoration:none;">'
        'Log in to your portal \u2192'
        '</a>'
        '</td></tr>'
        '<tr><td style="background:#f4f1eb;border:1px solid #e8e4dc;padding:1.25rem 1.5rem;">'
        '<p style="font-family:\'Courier New\',monospace;font-size:0.65rem;letter-spacing:0.1em;text-transform:uppercase;color:#8B6914;margin:0 0 0.75rem 0;">Your login details</p>'
        f'<p style="font-family:\'Courier New\',monospace;font-size:0.8rem;color:#111110;margin:0 0 0.35rem 0;"><span style="color:#3f3f3e;">Email&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</span>{to_email}</p>'
        f'<p style="font-family:\'Courier New\',monospace;font-size:0.8rem;color:#111110;margin:0;"><span style="color:#3f3f3e;">Temporary password&nbsp;&nbsp;</span>{temp_password}</p>'
        '</td></tr>'
        '<tr><td style="padding-top:1.25rem;">'
        '<p style="font-size:0.85rem;color:#3f3f3e;line-height:1.7;margin:0 0 0.5rem 0;">You will be asked to set a new password when you first sign in.</p>'
        '<p style="font-size:0.85rem;color:#3f3f3e;line-height:1.7;margin:0 0 1.75rem 0;">Questions? Reply to this email or write to '
        '<a href="mailto:hire@tryjoyn.me" style="color:#8B6914;">hire@tryjoyn.me</a></p>'
        '</td></tr>'
        '<tr><td style="border-top:1px solid #e8e4dc;padding-top:1.25rem;">'
        f'<p style="font-family:\'Courier New\',monospace;font-size:0.65rem;letter-spacing:0.08em;text-transform:uppercase;color:#3f3f3e;margin:0;">{staff_name} \u00b7 Joyn \u00b7 tryjoyn.me</p>'
        '</td></tr>'
        '</table></td></tr></table>'
        '</body></html>'
    )

    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail
        msg = Mail(
            from_email=app_config.get('ADMIN_EMAIL', 'hire@tryjoyn.me'),
            to_emails=to_email,
            subject=f'{staff_name} is ready \u2014 here is how to log in',
            html_content=html,
            plain_text_content=plain,
        )
        SendGridAPIClient(api_key).send(msg)
    except Exception as e:
        logger.error(f'SendGrid welcome email error: {e}')


def send_staff_added_email(
        app_config, logger,
        to_email, name, firm_name,
        staff_slug, staff_name, states):
    """Sent when a second (or further) staff member is added to an existing account.
    No password — the hirer already has credentials."""
    api_key = app_config.get('SENDGRID_API_KEY', '')
    if not api_key:
        logger.warning('SendGrid not configured — staff-added email not sent')
        return

    state_list_str = ', '.join(s.strip() for s in states.split(',') if s.strip()) if states else ''

    STAFF_COPY = {
        'iris': (
            f'Iris is now monitoring {state_list_str} for {firm_name}. '
            'She has been added to your portal and is already tracking regulatory changes.'
        ),
        'probe': (
            f'Probe has been added to your portal for {firm_name}. '
            'Log in to review your Experiment Brief and track progress.'
        ),
        'tdd-practice-team': (
            f'The TDD Practice Team has been added to your portal for {firm_name}. '
            'Log in to track progress and review outputs as they are delivered.'
        ),
        'creator-application': (
            f'Your creator application for {firm_name} has been received and added to your portal. '
            'Log in to track your application status.'
        ),
    }
    body_copy = STAFF_COPY.get(
        staff_slug,
        f'{staff_name} has been added to your portal for {firm_name}. Log in to get started.'
    )

    plain = (
        f'Hi {name},\n\n'
        f'{body_copy}\n\n'
        f'Log in to your portal:\n'
        f'https://app.tryjoyn.me/login\n\n'
        f'Your email address is your login. Use the password you set when you first signed in.\n\n'
        f'Questions? Reply to this email or write to hire@tryjoyn.me\n\n'
        f'\u2014 {staff_name} \u00b7 Joyn'
    )

    html = (
        '<!DOCTYPE html>'
        '<html lang="en"><head><meta charset="UTF-8"></head>'
        '<body style="margin:0;padding:0;background:#fafaf8;font-family:Arial,sans-serif;color:#111110;">'
        '<table width="100%" cellpadding="0" cellspacing="0">'
        '<tr><td align="center" style="padding:3rem 1rem;">'
        '<table width="100%" style="max-width:560px;">'
        '<tr><td style="border-bottom:1px solid #e8e4dc;padding-bottom:1.5rem;">'
        '<span style="font-family:\'Courier New\',monospace;font-size:0.9rem;font-weight:bold;letter-spacing:0.12em;color:#111110;">JOYN.</span>'
        '</td></tr>'
        '<tr><td style="padding-top:1.75rem;">'
        f'<p style="font-family:\'Courier New\',monospace;font-size:0.65rem;letter-spacing:0.1em;text-transform:uppercase;color:#8B6914;margin:0 0 0.5rem 0;">\u2014 {staff_name} added to your portal</p>'
        '</td></tr>'
        '<tr><td>'
        f'<h1 style="font-size:2rem;font-weight:300;margin:0 0 1.25rem 0;color:#111110;line-height:1.2;">Hi {name},</h1>'
        f'<p style="font-size:0.95rem;color:#3f3f3e;line-height:1.8;margin:0 0 1.75rem 0;">{body_copy}</p>'
        '</td></tr>'
        '<tr><td style="padding-bottom:1.75rem;">'
        '<a href="https://app.tryjoyn.me/login" '
        'style="display:inline-block;font-family:\'Courier New\',monospace;font-size:0.75rem;font-weight:bold;'
        'letter-spacing:0.1em;text-transform:uppercase;padding:0.875rem 2rem;background:#111110;color:#fafaf8;text-decoration:none;">'
        'Log in to your portal \u2192'
        '</a>'
        '</td></tr>'
        '<tr><td style="padding-top:1.25rem;">'
        '<p style="font-size:0.85rem;color:#3f3f3e;line-height:1.7;margin:0 0 0.5rem 0;">Your email address is your login. Use the password you set when you first signed in.</p>'
        '<p style="font-size:0.85rem;color:#3f3f3e;line-height:1.7;margin:0 0 1.75rem 0;">Questions? Reply to this email or write to '
        '<a href="mailto:hire@tryjoyn.me" style="color:#8B6914;">hire@tryjoyn.me</a></p>'
        '</td></tr>'
        '<tr><td style="border-top:1px solid #e8e4dc;padding-top:1.25rem;">'
        f'<p style="font-family:\'Courier New\',monospace;font-size:0.65rem;letter-spacing:0.08em;text-transform:uppercase;color:#3f3f3e;margin:0;">{staff_name} \u00b7 Joyn \u00b7 tryjoyn.me</p>'
        '</td></tr>'
        '</table></td></tr></table>'
        '</body></html>'
    )

    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail
        msg = Mail(
            from_email=app_config.get('ADMIN_EMAIL', 'hire@tryjoyn.me'),
            to_emails=to_email,
            subject=f'{staff_name} has been added to your Joyn portal',
            html_content=html,
            plain_text_content=plain,
        )
        SendGridAPIClient(api_key).send(msg)
    except Exception as e:
        logger.error(f'SendGrid staff-added email error: {e}')
