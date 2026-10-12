"""BH MARKETING GROUP LLC — CCPA/CPRA opt-out by e-mail (generated 2026-10-12).

From the data-broker gap list: confirmed by 17 independent sources
(registries and removal-service directories). usmarketinggrp.com publishes no consumer
opt-out form, so the request goes to its published privacy contact,
which is a role address rather than an individual's inbox.

Opt-out page on file: https://www.usmarketinggrp.com/privacy-policy/#CCPA
"""
from lib.broker_helpers import run_ccpa_email_optout


def usmarketinggrpcom(dataRow, website_name, in_user_email, run_mode):
    return run_ccpa_email_optout("usmarketinggrpcom", dataRow,
                                 privacy_email="privacy@usmarketinggrp.com",
                                 run_mode=run_mode)
