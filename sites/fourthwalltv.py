"""FourthWall — CCPA/CPRA opt-out by e-mail (generated 2026-10-12).

From the data-broker gap list: confirmed by 13 independent sources
(registries and removal-service directories). fourthwall.tv publishes no consumer
opt-out form, so the request goes to its published privacy contact,
which is a role address rather than an individual's inbox.

Opt-out page on file: https://www.fourthwall.tv/donotsellorshare-fourthwall
"""
from lib.broker_helpers import run_ccpa_email_optout


def fourthwalltv(dataRow, website_name, in_user_email, run_mode):
    return run_ccpa_email_optout("fourthwalltv", dataRow,
                                 privacy_email="privacypolicy@fourthwall.tv",
                                 run_mode=run_mode)
