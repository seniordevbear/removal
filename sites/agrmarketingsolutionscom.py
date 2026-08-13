from lib.broker_helpers import run_ccpa_email_optout


def agrmarketingsolutionscom(dataRow, website_name, in_user_email, run_mode):
    """Auto-implemented 2026-05-28 -- CCPA email-based opt-out.
    Defaults to privacy@<derived host>.
    """
    return run_ccpa_email_optout("agrmarketingsolutionscom", dataRow, run_mode=run_mode)
