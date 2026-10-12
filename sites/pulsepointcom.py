"""PulsePoint, Inc. — CCPA/CPRA opt-out by e-mail (generated 2026-10-12).

From the data-broker gap list: confirmed by 12 independent sources
(registries and removal-service directories). pulsepoint.com publishes no consumer
opt-out form, so the request goes to its published privacy contact,
which is a role address rather than an individual's inbox.

Opt-out page on file: https://mynt-test-privacy.my.onetrust.com/webform/ebe19500-bc8d-487f-9d89-98fde8b270e2/bac5d2a2-fd3e-4830-99b6-bd2a69fec1c9
"""
from lib.broker_helpers import run_ccpa_email_optout


def pulsepointcom(dataRow, website_name, in_user_email, run_mode):
    return run_ccpa_email_optout("pulsepointcom", dataRow,
                                 privacy_email="privacy@pulsepoint.com",
                                 run_mode=run_mode)
