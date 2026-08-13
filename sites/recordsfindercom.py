# recordsfindercom.py - REWRITTEN 2026-05-28. InfoPay backend.
from lib.broker_helpers import run_infopay_optout
def recordsfindercom(dataRow, website_name, in_user_email, run_mode):
    return run_infopay_optout("recordsfindercom",
                              "https://recordsfinder.com/optout/",
                              dataRow, run_mode)
