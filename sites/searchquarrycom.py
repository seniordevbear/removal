# searchquarrycom.py - REWRITTEN 2026-05-28. InfoPay backend.
from lib.broker_helpers import run_infopay_optout
def searchquarrycom(dataRow, website_name, in_user_email, run_mode):
    return run_infopay_optout("searchquarrycom",
                              "https://members.searchquarry.com/terms?tab=optout",
                              dataRow, run_mode)
