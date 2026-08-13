# ndbcom.py - REWRITTEN 2026-05-28. Same InfoPay backend as infotracer.
from lib.broker_helpers import run_infopay_optout
def ndbcom(dataRow, website_name, in_user_email, run_mode):
    return run_infopay_optout("ndbcom",
                              "https://infotracer.com/optout/",
                              dataRow, run_mode)
