"""Mobile Technology Corporation — CCPA/CPRA opt-out by e-mail (generated 2026-10-12).

From the data-broker gap list: confirmed by 11 independent sources
(registries and removal-service directories). onspotdata.com publishes no consumer
opt-out form, so the request goes to its published privacy contact,
which is a role address rather than an individual's inbox.

Opt-out page on file: https://www.onspotdata.com/privacy-policy/
"""
from lib.broker_helpers import run_ccpa_email_optout


def onspotdatacom(dataRow, website_name, in_user_email, run_mode):
    return run_ccpa_email_optout("onspotdatacom", dataRow,
                                 privacy_email="optout@onspotdata.com",
                                 run_mode=run_mode)
