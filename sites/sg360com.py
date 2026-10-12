"""SG360 — CCPA/CPRA opt-out by e-mail (generated 2026-10-12).

From the data-broker gap list: confirmed by 12 independent sources
(registries and removal-service directories). sg360.com publishes no consumer
opt-out form, so the request goes to its published privacy contact,
which is a role address rather than an individual's inbox.

Opt-out page on file: https://sg360.com/do-not-sell-my-info/
"""
from lib.broker_helpers import run_ccpa_email_optout


def sg360com(dataRow, website_name, in_user_email, run_mode):
    return run_ccpa_email_optout("sg360com", dataRow,
                                 privacy_email="dataprivacy@sg360.com",
                                 run_mode=run_mode)
