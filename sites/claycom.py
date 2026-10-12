"""CLAY LABS LLC — CCPA/CPRA opt-out by e-mail (generated 2026-10-12).

From the data-broker gap list: confirmed by 14 independent sources
(registries and removal-service directories). clay.com publishes no consumer
opt-out form, so the request goes to its published privacy contact,
which is a role address rather than an individual's inbox.

Opt-out page on file: https://docs.google.com/forms/d/e/1FAIpQLSeAsU1U-AJfhqzDx6-6eVcyQ_kBD1J9cw1y0huQiS-HCkRf0Q/viewform?usp=send_form
"""
from lib.broker_helpers import run_ccpa_email_optout


def claycom(dataRow, website_name, in_user_email, run_mode):
    return run_ccpa_email_optout("claycom", dataRow,
                                 privacy_email="privacy@clay.com",
                                 run_mode=run_mode)
