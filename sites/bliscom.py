"""Blis Global Ltd — CCPA/CPRA opt-out by e-mail (generated 2026-10-12).

From the data-broker gap list: confirmed by 13 independent sources
(registries and removal-service directories). blis.com publishes no consumer
opt-out form, so the request goes to its published privacy contact,
which is a role address rather than an individual's inbox.

Opt-out page on file: https://blis.com/privacy-centre/
"""
from lib.broker_helpers import run_ccpa_email_optout


def bliscom(dataRow, website_name, in_user_email, run_mode):
    return run_ccpa_email_optout("bliscom", dataRow,
                                 privacy_email="privacy@blis.com",
                                 run_mode=run_mode)
