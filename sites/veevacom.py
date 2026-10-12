"""Veeva Systems Inc. — CCPA/CPRA opt-out by e-mail (generated 2026-10-12).

From the data-broker gap list: confirmed by 16 independent sources
(registries and removal-service directories). veeva.com publishes no consumer
opt-out form, so the request goes to its published privacy contact,
which is a role address rather than an individual's inbox.

Opt-out page on file: https://privacyportal.onetrust.com/webform/3d676ed2-16b1-4c48-97f8-a911923a3adf/a0df0a98-d990-40ff-9bdb-35b5f9e06620
"""
from lib.broker_helpers import run_ccpa_email_optout


def veevacom(dataRow, website_name, in_user_email, run_mode):
    return run_ccpa_email_optout("veevacom", dataRow,
                                 privacy_email="privacy@veeva.com",
                                 run_mode=run_mode)
