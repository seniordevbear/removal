"""Commercial Real Estate Exchange, Inc. — CCPA/CPRA opt-out by e-mail (generated 2026-10-12).

From the data-broker gap list: confirmed by 10 independent sources
(registries and removal-service directories). crexi.com publishes no consumer
opt-out form, so the request goes to its published privacy contact,
which is a role address rather than an individual's inbox.

Opt-out page on file: https://crexi.bigidprivacy.cloud/consumer/#/o2TCsG9LJ7
"""
from lib.broker_helpers import run_ccpa_email_optout


def crexicom(dataRow, website_name, in_user_email, run_mode):
    return run_ccpa_email_optout("crexicom", dataRow,
                                 privacy_email="privacy@crexi.com",
                                 run_mode=run_mode)
