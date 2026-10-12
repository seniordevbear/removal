"""WINR Data B.V. — CCPA/CPRA opt-out by e-mail (generated 2026-10-12).

From the data-broker gap list: confirmed by 13 independent sources
(registries and removal-service directories). winrdata.com publishes no consumer
opt-out form, so the request goes to its published privacy contact,
which is a role address rather than an individual's inbox.

Opt-out page on file: https://privacyportal-au.onetrust.com/webform/ad3cafad-4bf2-4d22-951f-57cc1fd05690/5fa8f2da-0508-42a6-bbc7-9b031898d10c
"""
from lib.broker_helpers import run_ccpa_email_optout


def winrdatacom(dataRow, website_name, in_user_email, run_mode):
    return run_ccpa_email_optout("winrdatacom", dataRow,
                                 privacy_email="privacy@winrdata.com",
                                 run_mode=run_mode)
