"""Narvar, Inc. — CCPA/CPRA opt-out by e-mail (generated 2026-10-12).

From the data-broker gap list: confirmed by 11 independent sources
(registries and removal-service directories). narvar.com publishes no consumer
opt-out form, so the request goes to its published privacy contact,
which is a role address rather than an individual's inbox.

Opt-out page on file: https://narvar.my.onetrust.com/webform/04b3731f-2a9a-42ce-bd6b-106d4b4ec3bf/a7c944bf-3cec-4f00-9dc5-dea5bf2b6f4f
"""
from lib.broker_helpers import run_ccpa_email_optout


def narvarcom(dataRow, website_name, in_user_email, run_mode):
    return run_ccpa_email_optout("narvarcom", dataRow,
                                 privacy_email="legal@narvar.com",
                                 run_mode=run_mode)
