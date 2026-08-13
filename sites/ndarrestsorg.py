from lib.broker_helpers import run_arrests_org_optout


def ndarrestsorg(dataRow, website_name, in_user_email, run_mode):
    """Auto-implemented 2026-05-28 via shared template.
    All *arrests.org / *courtrecords.us sites use the same /request-portal form.
    """
    return run_arrests_org_optout("ndarrestsorg", dataRow, run_mode=run_mode)
