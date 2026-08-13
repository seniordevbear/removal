from lib.broker_helpers import run_ccpa_email_optout


def affinityanswerscom(dataRow, website_name, in_user_email, run_mode):
    """Auto-implemented 2026-05-28 -- CCPA email-based opt-out.
    Sends a CCPA Sec.1798.105+120 request to privacy@<derived>.
    Broker has 45 days to comply per statute.
    """
    return run_ccpa_email_optout("affinityanswerscom", dataRow,
                                   privacy_email=None,
                                   run_mode=run_mode)
