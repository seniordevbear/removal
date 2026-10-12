"""Wiza — CCPA/CPRA opt-out by e-mail (generated 2026-10-12).

From the data-broker gap list: confirmed by 12 independent sources
(registries and removal-service directories). wiza.co publishes no consumer
opt-out form, so the request goes to its published privacy contact,
which is a role address rather than an individual's inbox.

Opt-out page on file: https://wiza.co/optout-directory
"""
from lib.broker_helpers import run_ccpa_email_optout


def wizaco(dataRow, website_name, in_user_email, run_mode):
    return run_ccpa_email_optout("wizaco", dataRow,
                                 privacy_email="hello@wiza.co",
                                 run_mode=run_mode)
