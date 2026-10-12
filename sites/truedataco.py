"""Truedata Solutions, Inc. — CCPA/CPRA opt-out by e-mail (generated 2026-10-12).

From the data-broker gap list: confirmed by 14 independent sources
(registries and removal-service directories). truedata.co publishes no consumer
opt-out form, so the request goes to its published privacy contact,
which is a role address rather than an individual's inbox.

Opt-out page on file: https://www.truedata.co/wp-content/uploads/2026/01/TD-Privacy-Policy-effective-16-Jan-2026.pdf
"""
from lib.broker_helpers import run_ccpa_email_optout


def truedataco(dataRow, website_name, in_user_email, run_mode):
    return run_ccpa_email_optout("truedataco", dataRow,
                                 privacy_email="privacy@truedata.co",
                                 run_mode=run_mode)
