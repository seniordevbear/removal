"""CUSTOMER ASSET CONSULTING GROUP Inc — CCPA/CPRA opt-out by e-mail (generated 2026-10-12).

From the data-broker gap list: confirmed by 14 independent sources
(registries and removal-service directories). datadelivers.com publishes no consumer
opt-out form, so the request goes to its published privacy contact,
which is a role address rather than an individual's inbox.

Opt-out page on file: https://datadelivers.com/do-not-sell-or-share-my-personal-information/
"""
from lib.broker_helpers import run_ccpa_email_optout


def datadeliverscom(dataRow, website_name, in_user_email, run_mode):
    return run_ccpa_email_optout("datadeliverscom", dataRow,
                                 privacy_email="privacy@datadelivers.com",
                                 run_mode=run_mode)
