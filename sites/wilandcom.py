"""Wiland, Inc. — CCPA/CPRA opt-out by e-mail (generated 2026-10-12).

From the data-broker gap list: confirmed by 16 independent sources
(registries and removal-service directories). wiland.com publishes no consumer
opt-out form, so the request goes to its published privacy contact,
which is a role address rather than an individual's inbox.

Opt-out page on file: https://privacyportal.onetrust.com/webform/7567ece3-2d27-4ee0-a506-1153cb7a62b7/a5485eb1-f1ee-4a9f-9ed4-2b8ee48b550f
"""
from lib.broker_helpers import run_ccpa_email_optout


def wilandcom(dataRow, website_name, in_user_email, run_mode):
    return run_ccpa_email_optout("wilandcom", dataRow,
                                 privacy_email="privacy@wiland.com",
                                 run_mode=run_mode)
