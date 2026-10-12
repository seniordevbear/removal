"""Webbula, LLC — CCPA/CPRA opt-out by e-mail (generated 2026-10-12).

From the data-broker gap list: confirmed by 16 independent sources
(registries and removal-service directories). webbula.com publishes no consumer
opt-out form, so the request goes to its published privacy contact,
which is a role address rather than an individual's inbox.

Opt-out page on file: https://webbula.com/opt-out-request/
"""
from lib.broker_helpers import run_ccpa_email_optout


def webbulacom(dataRow, website_name, in_user_email, run_mode):
    return run_ccpa_email_optout("webbulacom", dataRow,
                                 privacy_email="privacy@webbula.com",
                                 run_mode=run_mode)
