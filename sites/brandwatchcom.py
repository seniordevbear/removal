from lib.broker_helpers import run_ccpa_email_optout


def brandwatchcom(dataRow, website_name, in_user_email, run_mode):
    """2026-10-04: the DPOrganizer portal this script drove
    (portals.dporganizer.com/4d3f1506-...) now answers "This page is no
    longer available" and brandwatch.com/p/legal-data/ redirects to it.
    Brandwatch's own data-subject-request page says a request can be
    initiated by e-mail to privacy@brandwatch.com, so that is the route now
    (0/29 portal runs succeeded in the 24 Sep-2 Oct logs).
    """
    return run_ccpa_email_optout("brandwatchcom", dataRow,
                                 privacy_email="privacy@brandwatch.com",
                                 run_mode=run_mode)
