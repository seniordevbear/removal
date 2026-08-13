from lib.broker_helpers import run_arrests_org_optout


def kentuckyarrestsorg(dataRow, website_name, in_user_email, run_mode):
    """Auto-implemented 2026-05-28 via shared template.
    All *arrests.org / *courtrecords.us sites use the same /request-portal form.
    """
    return run_arrests_org_optout("kentuckyarrestsorg", dataRow, run_mode=run_mode)
