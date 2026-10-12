"""Claritas — CCPA/CPRA opt-out by e-mail (generated 2026-10-12).

From the data-broker gap list: confirmed by 17 independent sources
(registries and removal-service directories). claritas.com publishes no consumer
opt-out form, so the request goes to its published privacy contact,
which is a role address rather than an individual's inbox.

Opt-out page on file: https://privacyportal.onetrust.com/webform/68582716-6ce4-4f6e-bf08-78371b5f3292/6c7dc52d-0e2b-481f-9256-0755179e3783.html
"""
from lib.broker_helpers import run_ccpa_email_optout


def claritascom(dataRow, website_name, in_user_email, run_mode):
    return run_ccpa_email_optout("claritascom", dataRow,
                                 privacy_email="privacyinfo@claritas.com",
                                 run_mode=run_mode)
