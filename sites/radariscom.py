from lib.broker_helpers import run_ccpa_email_optout


def radariscom(dataRow, website_name, in_user_email, run_mode):
    """Defunct — verified 2026-09-18.

    radaris.com now serves only "This Domain Has Been Transferred by Court
    Order" (HTTP 200, no search, no listings). The site was seized, so there
    is nothing left to opt out of and customer-service@radaris.com has no
    business behind it any more. NotImplementedError -> step=4 (not
    available), which the pipeline does not retry — same handling as
    vericora.com. 1,419 rows were still queued for it.

    The 2026-08-25 email-based CCPA/GDPR opt-out is kept below, unreachable,
    in case the domain ever returns under the same operator.
    """
    raise NotImplementedError("radaris.com is defunct — domain seized by court order (2026-09-18)")
    return run_ccpa_email_optout("radariscom", dataRow,
                                 privacy_email="customer-service@radaris.com",
                                 run_mode=run_mode)
