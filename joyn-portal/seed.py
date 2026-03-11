"""
Seed one test client + Iris + 10 activity entries + 3 outputs.
Run with:  python seed.py
"""
import os, sys, json
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from auth.helpers import hash_password
from data.db import query_one, insert, execute_commit

app = create_app()

with app.app_context():
    # ── Client ──────────────────────────────────────────────
    existing = query_one('SELECT id FROM clients WHERE email=?', ('shiva@tryjoyn.me',))
    if existing:
        client_id = existing['id']
        print(f'Client already exists — id={client_id}')
    else:
        client_id = insert(
            '''INSERT INTO clients
               (email, password_hash, company_name, subscription_status, trial_ends_at)
               VALUES (?,?,?,?,?)''',
            (
                'shiva@tryjoyn.me',
                hash_password('JoynIris2026'),
                'Joyn Internal',
                'active',
                (datetime.utcnow() + timedelta(days=30)).isoformat(),
            )
        )
        print(f'Client created — id={client_id}')

    # ── Hired staff: Iris ────────────────────────────────────
    iris_existing = query_one(
        "SELECT id FROM hired_staff WHERE client_id=? AND staff_slug='iris'",
        (client_id,)
    )
    if not iris_existing:
        insert(
            '''INSERT INTO hired_staff
               (client_id, staff_name, staff_slug, status, vertical, mode, settings)
               VALUES (?,?,?,?,?,?,?)''',
            (
                client_id, 'Iris', 'iris', 'active', 'Insurance & Risk', 'autonomous',
                json.dumps({
                    'alert_email': 'shiva@tryjoyn.me',
                    'alert_frequency': 'daily',
                    'jurisdictions': ['Florida', 'Georgia', 'Texas', 'California', 'New York'],
                })
            )
        )
        print('Iris hired.')

    # ── Activity log (10 entries) ────────────────────────────
    existing_activity = query_one(
        "SELECT COUNT(*) as c FROM activity_log WHERE client_id=?", (client_id,)
    )
    if existing_activity['c'] == 0:
        activities = [
            ('briefing',  'Regulatory briefing delivered. Florida OIR Bulletin 2026-03 — rate filing requirements updated for homeowners lines.',                         'complete'),
            ('digest',    'Daily digest sent. 6 regulatory items monitored across 5 jurisdictions. No critical alerts.',                                                   'complete'),
            ('alert',     'Alert raised. Florida OIR Emergency Order 26-01 — mandatory coverage extension for coastal properties. Compliance deadline in 30 days.',        'complete'),
            ('briefing',  'Briefing prepared. Georgia DOI proposed rule on claims handling timelines — public comment period open until 15 Apr 2026.',                     'complete'),
            ('digest',    'Daily digest sent. 4 regulatory updates monitored. 1 high-severity item flagged.',                                                              'complete'),
            ('filing',    'Document filed. Updated policy schedule cross-referenced against current Florida OIR guidance. No discrepancies found.',                        'complete'),
            ('briefing',  'Q1 2026 regulatory summary prepared — 14 pages, 5 jurisdictions, 4 priority action items.',                                                    'complete'),
            ('alert',     'Alert raised. Texas TDI rate bulletin TXB-2026-04 — new actuarial filing requirements effective 1 Jul 2026.',                                   'complete'),
            ('digest',    'Daily digest sent. 8 regulatory updates monitored across 5 jurisdictions. No critical alerts.',                                                 'complete'),
            ('briefing',  'Briefing prepared. California CDI market conduct bulletin — data privacy requirements for insurance carriers updated.',                          'complete'),
        ]
        for i, (action_type, description, status) in enumerate(activities):
            ts = (datetime.utcnow() - timedelta(hours=i * 8)).isoformat()
            execute_commit(
                '''INSERT INTO activity_log
                   (client_id, staff_name, staff_slug, timestamp, action_type, action_description, status)
                   VALUES (?,?,?,?,?,?,?)''',
                (client_id, 'Iris', 'iris', ts, action_type, description, status)
            )
        print('10 activity entries seeded.')

    # ── Outputs (3 entries) ──────────────────────────────────
    existing_outputs = query_one(
        "SELECT COUNT(*) as c FROM outputs WHERE client_id=?", (client_id,)
    )
    if existing_outputs['c'] == 0:
        outputs = [
            ('critical', 'briefing',
             'URGENT: Florida OIR Emergency Order 26-01 — Coastal Homeowners Coverage Mandate',
             'Florida OIR has issued an emergency order requiring mandatory coverage extension for coastal properties. Your current policy schedule may require immediate amendment. Compliance deadline: 30 days from issue date.',
             'Emergency order issued 28 Feb 2026. Affects all homeowners carriers writing in coastal counties. Three action items prepared for your compliance team.'),
            ('high', 'briefing',
             'Texas TDI Rate Bulletin TXB-2026-04 — Actuarial Filing Update',
             'New actuarial filing requirements from Texas TDI effective 1 Jul 2026. Rate support documentation requirements expanded.',
             'Two new exhibits required for all rate filings after 1 Jul 2026. Iris has prepared a compliance checklist for your actuarial team.'),
            ('medium', 'summary',
             'Q1 2026 Regulatory Summary — 5 Jurisdictions',
             'Quarterly regulatory intelligence summary across Florida, Georgia, Texas, California, and New York. 14 regulatory items tracked, 4 priority action items identified.',
             '14-page briefing covering Q1 2026 regulatory activity. Key themes: coastal property coverage, rate adequacy, and market conduct. Delivered 1 Apr 2026.'),
        ]
        for severity, output_type, title, summary, full_content in outputs:
            insert(
                '''INSERT INTO outputs
                   (client_id, staff_name, staff_slug, output_type, title, summary, severity, full_content)
                   VALUES (?,?,?,?,?,?,?,?)''',
                (client_id, 'Iris', 'iris', output_type, title, summary, severity, full_content)
            )
        print('3 output entries seeded.')

    print('\n✓ Seed complete.')
    print(f'  Login: shiva@tryjoyn.me / JoynIris2026')
    print(f'  JOYN_PORTAL_SECRET: {os.environ.get("JOYN_PORTAL_SECRET", "(check .env)")}')
