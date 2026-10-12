"""LeadCrunch — CCPA/CPRA opt-out by e-mail (generated 2026-10-12).

From the data-broker gap list: confirmed by 12 independent sources
(registries and removal-service directories). getrev.ai publishes no consumer
opt-out form, so the request goes to its published privacy contact,
which is a role address rather than an individual's inbox.

Opt-out page on file: https://getrev.ai/privacy-policy/#notice-to-residents-of-california
"""
from lib.broker_helpers import run_ccpa_email_optout


def getrevai(dataRow, website_name, in_user_email, run_mode):
    return run_ccpa_email_optout("getrevai", dataRow,
                                 privacy_email="privacy@getrev.ai",
                                 run_mode=run_mode)
