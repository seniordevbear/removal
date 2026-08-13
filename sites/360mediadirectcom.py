from lib.broker_helpers import run_ccpa_email_optout


def _ccpa_email_impl(dataRow, website_name, in_user_email, run_mode):
    """Auto-implemented 2026-05-28 -- CCPA email-based opt-out.
    Digit-prefixed broker name attached via globals().
    Defaults to privacy@<derived host>."""
    return run_ccpa_email_optout("360mediadirectcom", dataRow, run_mode=run_mode)


globals()["360mediadirectcom"] = _ccpa_email_impl
