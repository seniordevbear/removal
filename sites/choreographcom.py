"""Choreograph LLC — CCPA/CPRA opt-out by e-mail (generated 2026-10-12).

From the data-broker gap list: confirmed by 15 independent sources
(registries and removal-service directories). choreograph.com publishes no consumer
opt-out form, so the request goes to its published privacy contact,
which is a role address rather than an individual's inbox.

Opt-out page on file: https://amer-cpp.choreograph.com/manage-your-data/do-not-sell
"""
from lib.broker_helpers import run_ccpa_email_optout


def choreographcom(dataRow, website_name, in_user_email, run_mode):
    return run_ccpa_email_optout("choreographcom", dataRow,
                                 privacy_email="privacy@choreograph.com",
                                 run_mode=run_mode)
