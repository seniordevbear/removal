"""VENTIVEIQ LLC — CCPA/CPRA opt-out by e-mail (generated 2026-10-12).

From the data-broker gap list: confirmed by 14 independent sources
(registries and removal-service directories). ventiveiq.com publishes no consumer
opt-out form, so the request goes to its published privacy contact,
which is a role address rather than an individual's inbox.

Opt-out page on file: https://privacyportal.privacypillar.com/dsar/form?orgid=0c31c814-ea86-461f-8ccb-294f05bc74c3&propid=cc95835d-7719-4336-b0c4-18146e5d000a&formid=4348f332-6917-4566-8c56-6fc9eb57097f&status=publish
"""
from lib.broker_helpers import run_ccpa_email_optout


def ventiveiqcom(dataRow, website_name, in_user_email, run_mode):
    return run_ccpa_email_optout("ventiveiqcom", dataRow,
                                 privacy_email="privacy@ventiveiq.com",
                                 run_mode=run_mode)
