# staterecordsorg.py - REWRITTEN 2026-05-28. InfoPay backend.
from lib.broker_helpers import run_infopay_optout
def staterecordsorg(dataRow, website_name, in_user_email, run_mode):
    return run_infopay_optout("staterecordsorg",
                              "https://staterecords.org/optout",
                              dataRow, run_mode)
