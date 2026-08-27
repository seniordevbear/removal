from lib.broker_helpers import run_ccpa_email_optout


def radariscom(dataRow, website_name, in_user_email, run_mode):
    """Rewritten 2026-08-25 — email-based CCPA/GDPR opt-out.

    Radaris turned its web opt-out into a hand-off to onerep.com (a paid
    removal service), which does not actually remove data from Radaris — so
    automating that funnel accomplishes nothing. Radaris's published privacy
    contact (privacy policy, Contact Us section, verified 2026-08-25) is
    customer-service@radaris.com, so we send a formal deletion request there:
    same legal force (CCPA 1798.105/.120 + GDPR Art. 17), reliable, no
    captcha. Their contact form is an alternative but is Cloudflare-Turnstile
    gated and only a generic contact form, so email is preferred.
    """
    return run_ccpa_email_optout("radariscom", dataRow,
                                 privacy_email="customer-service@radaris.com",
                                 run_mode=run_mode)
