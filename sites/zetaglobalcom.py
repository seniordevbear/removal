"""Zeta Global — CCPA/CPRA opt-out by e-mail (generated 2026-10-12).

From the data-broker gap list: confirmed by 15 independent sources
(registries and removal-service directories). zetaglobal.com publishes no consumer
opt-out form, so the request goes to its published privacy contact,
which is a role address rather than an individual's inbox.

Opt-out page on file: https://zetaglobal.com/privacy-choices/
"""
from lib.broker_helpers import run_ccpa_email_optout


def zetaglobalcom(dataRow, website_name, in_user_email, run_mode):
    return run_ccpa_email_optout("zetaglobalcom", dataRow,
                                 privacy_email="privacy@zetaglobal.com",
                                 run_mode=run_mode)
