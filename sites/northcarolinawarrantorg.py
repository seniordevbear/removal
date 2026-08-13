# northcarolinawarrantorg.py - REWRITTEN 2026-05-28. InfoPay backend.
from lib.broker_helpers import run_infopay_optout
def northcarolinawarrantorg(dataRow, website_name, in_user_email, run_mode):
    return run_infopay_optout("northcarolinawarrantorg",
                              "https://members.verifyrecords.com/customer/opt-out",
                              dataRow, run_mode)
