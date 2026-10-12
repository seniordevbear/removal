"""Round Sky, Inc. — CCPA/CPRA opt-out by e-mail (generated 2026-10-12).

From the data-broker gap list: confirmed by 10 independent sources
(registries and removal-service directories). roundsky.com publishes no consumer
opt-out form, so the request goes to its published privacy contact,
which is a role address rather than an individual's inbox.

Opt-out page on file: https://www.roundsky.com/supplemental-privacy-notice/contact.php
"""
from lib.broker_helpers import run_ccpa_email_optout


def roundskycom(dataRow, website_name, in_user_email, run_mode):
    return run_ccpa_email_optout("roundskycom", dataRow,
                                 privacy_email="legal@roundsky.com",
                                 run_mode=run_mode)
