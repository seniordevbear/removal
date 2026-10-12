"""Sheerid, Inc. — CCPA/CPRA opt-out by e-mail (generated 2026-10-12).

From the data-broker gap list: confirmed by 14 independent sources
(registries and removal-service directories). sheerid.com publishes no consumer
opt-out form, so the request goes to its published privacy contact,
which is a role address rather than an individual's inbox.

Opt-out page on file: https://www.sheerid.com/privacy-notice-for-audience-development-products-services/?_cord_id=6ddcc513-32c1-4799-832f-5c1d99acad88
"""
from lib.broker_helpers import run_ccpa_email_optout


def sheeridcom(dataRow, website_name, in_user_email, run_mode):
    return run_ccpa_email_optout("sheeridcom", dataRow,
                                 privacy_email="privacy@sheerid.com",
                                 run_mode=run_mode)
