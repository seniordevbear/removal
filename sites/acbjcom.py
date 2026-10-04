from lib.broker_helpers import run_ccpa_email_optout


def acbjcom(dataRow, website_name, in_user_email, run_mode):
    """2026-10-04: the OneTrust webform this script drove is gone ("The
    requested content is no longer available") and the replacement at
    privacy.acbj.com is a JavaScript privacy center that cannot be captured
    from the web server. ACBJ's privacy policy (acbj.com/privacy, captured
    2026-10-04) says rights requests can be sent to the Privacy Policy
    Coordinator at PrivacyPolicyCoordinator@bizjournals.com, so that is the
    route until the privacy center is scripted.
    """
    return run_ccpa_email_optout("acbjcom", dataRow,
                                 privacy_email="PrivacyPolicyCoordinator@bizjournals.com",
                                 run_mode=run_mode)
