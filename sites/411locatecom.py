from lib.broker_helpers import run_ccpa_email_optout


def _ccpa_email_impl(dataRow, website_name, in_user_email, run_mode):
    """Auto-implemented 2026-05-28 -- CCPA email-based opt-out.

    Chose email over scraper for this broker because the form path
    requires CAPTCHA solving + email-verification round-trip (user
    clicks a verification link in their inbox). Email path is
    legally equivalent under CCPA Sec.1798.105 & 1798.120, requires
    no captcha, and triggers the same 45-day compliance clock.

    Target privacy contact: privacy@411locate.com
    """
    return run_ccpa_email_optout("411locatecom", dataRow,
                                   privacy_email="privacy@411locate.com",
                                   run_mode=run_mode)


globals()["411locatecom"] = _ccpa_email_impl
