from lib.broker_helpers import run_ccpa_email_optout


def bytwocom(dataRow, website_name, in_user_email, run_mode):
    """2026-10-04: the OneTrust webform this script drove now redirects to
    anteriad.com/privacy-center, which carries no request form (captured
    round 2 and round 5). Anteriad's privacy policy states: "You may contact
    us to have your personal information removed from our database ... email
    us at privacy@anteriad.com". That is the route now.
    """
    return run_ccpa_email_optout("bytwocom", dataRow,
                                 privacy_email="privacy@anteriad.com",
                                 run_mode=run_mode)
