"""National Opinion Institute, LLC — CCPA/CPRA opt-out by e-mail (generated 2026-10-12).

From the data-broker gap list: confirmed by 11 independent sources
(registries and removal-service directories). nationalopinioninstitute.com publishes no consumer
opt-out form, so the request goes to its published privacy contact,
which is a role address rather than an individual's inbox.

Opt-out page on file: https://privacyportal.onetrust.com/webform/77dff651-9f08-40cd-99fe-a7c487b2504d/afcce4ab-fd72-4990-a972-58e24d9110a7
"""
from lib.broker_helpers import run_ccpa_email_optout


def nationalopinioninstitutecom(dataRow, website_name, in_user_email, run_mode):
    return run_ccpa_email_optout("nationalopinioninstitutecom", dataRow,
                                 privacy_email="privacy@nationalopinioninstitute.com",
                                 run_mode=run_mode)
