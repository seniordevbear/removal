"""LionShare — CCPA/CPRA opt-out by e-mail (generated 2026-10-12).

From the data-broker gap list: confirmed by 14 independent sources
(registries and removal-service directories). lionsharemarketing.com publishes no consumer
opt-out form, so the request goes to its published privacy contact,
which is a role address rather than an individual's inbox.

Opt-out page on file: https://www.lionsharemarketing.com/privacy-policy/
"""
from lib.broker_helpers import run_ccpa_email_optout


def lionsharemarketingcom(dataRow, website_name, in_user_email, run_mode):
    return run_ccpa_email_optout("lionsharemarketingcom", dataRow,
                                 privacy_email="webmaster@lionsharemarketing.com",
                                 run_mode=run_mode)
