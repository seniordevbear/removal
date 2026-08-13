from lib.broker_helpers import run_ccpa_email_optout


def attribitscom(dataRow, website_name, in_user_email, run_mode):
    """Auto-implemented 2026-05-28 -- CCPA email-based opt-out.
    Sends a CCPA Sec.1798.105 + 1798.120 deletion + opt-out request
    to privacy@<derived host>. 45-day statutory compliance window. Reply-To
    set to user's email so any verification challenge reaches them.
    """
    return run_ccpa_email_optout("attribitscom", dataRow,
                                   privacy_email=None,
                                   run_mode=run_mode)
