"""DealerSocket — CCPA/CPRA opt-out by e-mail (generated 2026-10-12).

From the data-broker gap list: confirmed by 10 independent sources
(registries and removal-service directories). dealersocket.com publishes no consumer
opt-out form, so the request goes to its published privacy contact,
which is a role address rather than an individual's inbox.

Opt-out page on file: https://globaldsar.solera.com/webform/20bbc57b-6134-4535-8062-a1745b771851/1eafe8e0-f69b-4d39-af7c-6dbf764046fa
"""
from lib.broker_helpers import run_ccpa_email_optout


def dealersocketcom(dataRow, website_name, in_user_email, run_mode):
    return run_ccpa_email_optout("dealersocketcom", dataRow,
                                 privacy_email="privacy@solera.com",
                                 run_mode=run_mode)
