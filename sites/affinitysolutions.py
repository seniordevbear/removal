from lib.broker_helpers import run_ccpa_email_optout


def affinitysolutions(dataRow, website_name, in_user_email, run_mode):
    """Auto-implemented 2026-05-28 -- CCPA email-based opt-out.
    Sends a CCPA Sec.1798.105 + 1798.120 deletion + opt-out request
    to privacy@affinitysolutions.com. 45-day statutory compliance window. Reply-To
    set to user's email so any verification challenge reaches them.
    """
    return run_ccpa_email_optout("affinitysolutions", dataRow,
                                   privacy_email="privacy@affinitysolutions.com",
                                   run_mode=run_mode)
