"""Realeflow LLC — CCPA/CPRA opt-out by e-mail (generated 2026-10-12).

From the data-broker gap list: confirmed by 13 independent sources
(registries and removal-service directories). realeflow.com publishes no consumer
opt-out form, so the request goes to its published privacy contact,
which is a role address rather than an individual's inbox.

Opt-out page on file: https://forms.gle/cgg2e2jLT7CL7efM7
"""
from lib.broker_helpers import run_ccpa_email_optout


def realeflowcom(dataRow, website_name, in_user_email, run_mode):
    return run_ccpa_email_optout("realeflowcom", dataRow,
                                 privacy_email="privacy@realeflow.com",
                                 run_mode=run_mode)
