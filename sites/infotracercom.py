# infotracercom.py - REWRITTEN 2026-05-28
# Old: 0/107 prod success. Was missing JS, no consent dismissal,
# brittle selectors, no per-step screenshots so failures were invisible.
# All InfoPay-backend brokers (7 total: this, ndbcom,
# northcarolinawarrantorg, ohioarrestwarrantorg, searchquarrycom,
# staterecordsorg, recordsfindercom) now delegate to
# lib.broker_helpers.run_infopay_optout().
from lib.broker_helpers import run_infopay_optout


def infotracercom(dataRow, website_name, in_user_email, run_mode):
    return run_infopay_optout("infotracercom",
                              "https://infotracer.com/optout/",
                              dataRow, run_mode)
