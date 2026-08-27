from lib.broker_helpers import run_ccpa_email_optout


def spydialercom(dataRow, website_name, in_user_email, run_mode):
    """Rewritten 2026-08-27 — email-based CCPA/GDPR opt-out.

    Spydialer's web opt-out is a stateful ASP.NET wizard: it requires a prior
    search to reach the opt-out step, multiple VIEWSTATE postbacks through
    modals, and a FULL STREET ADDRESS to identify records (which many of our
    users don't have on file). That is fragile and often un-completable. Its
    published privacy contact (privacy / notice-at-collection pages, verified
    2026-08-27) is support@spydialer.com, so we send a formal deletion request
    there instead: reliable, works for every user, same legal force.
    """
    return run_ccpa_email_optout("spydialercom", dataRow,
                                 privacy_email="support@spydialer.com",
                                 run_mode=run_mode)
