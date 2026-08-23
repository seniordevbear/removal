from lib.broker_helpers import run_ccpa_email_optout


def bvdinfocom(dataRow, website_name, in_user_email, run_mode):
    """Rewritten 2026-08-23 — email-based CCPA/GDPR opt-out.

    Bureau van Dijk is a Moody's company; bvdinfo.com now redirects to
    moodys.com. Their old browser flow pointed at an Alchemer survey that
    forces a Moody's-product choice which doesn't clearly cover the BvD
    database — automating it risked misrouting requests. Moody's privacy
    policy (verified 2026-08-23) directs privacy requests to
    privacy@moodys.com, so this broker uses the email path: same legal
    force (CCPA 1798.105/.120 + GDPR Art. 17), no fragile survey.
    """
    return run_ccpa_email_optout("bvdinfocom", dataRow,
                                 privacy_email="privacy@moodys.com",
                                 run_mode=run_mode)
