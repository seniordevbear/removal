"""01Advertising Inc. — CCPA/CPRA opt-out by e-mail (generated 2026-10-12).

From the data-broker gap list: confirmed by 13 independent sources
(registries and removal-service directories). 01advertising.com publishes no consumer
opt-out form, so the request goes to its published privacy contact,
which is a role address rather than an individual's inbox.

Opt-out page on file: https://app.termly.io/notify/d1321341-0e82-4d8c-afaf-c4940d46c171
"""
from lib.broker_helpers import run_ccpa_email_optout


# The broker key starts with a digit, which is not a valid Python function
# name, so the implementation is attached under that name via globals() --
# the same pattern sites/33acrosscom.py uses. __removal.py resolves the
# broker with getattr(module, target_domain), which does not require the
# attribute to be an identifier.
def _ccpa_email_impl(dataRow, website_name, in_user_email, run_mode):
    return run_ccpa_email_optout("01advertisingcom", dataRow,
                                 privacy_email="privacy@01advertising.com",
                                 run_mode=run_mode)


globals()["01advertisingcom"] = _ccpa_email_impl
