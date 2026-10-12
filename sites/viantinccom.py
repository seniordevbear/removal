"""Viant US LLC — CCPA/CPRA opt-out by e-mail (generated 2026-10-12).

From the data-broker gap list: confirmed by 15 independent sources
(registries and removal-service directories). viantinc.com publishes no consumer
opt-out form, so the request goes to its published privacy contact,
which is a role address rather than an individual's inbox.

Opt-out page on file: https://privacyportal.onetrust.com/webform/18c06089-a9ec-473c-a6d8-23d20fea46af/43201dea-88d7-44cd-9142-e5b4f485e428
"""
from lib.broker_helpers import run_ccpa_email_optout


def viantinccom(dataRow, website_name, in_user_email, run_mode):
    return run_ccpa_email_optout("viantinccom", dataRow,
                                 privacy_email="privacy@viantinc.com",
                                 run_mode=run_mode)
