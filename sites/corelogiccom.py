"""CoreLogic - now Cotality (the corelogiccom key is kept for the queue).

2026-10-20: www.corelogic.com redirects to www.cotality.com, and the page
the old script drove (/employee-applicant-privacy-form/) was the EMPLOYEE
and applicant form in any case - 102 "No element found." failures between
17 and 19 Oct against a form that was never meant for consumers. The
California notice at /legal/california-notice-at-collection says consumers
"may submit a request to know, delete and/or correct your information
through our Online Privacy Portal" - a Ketch widget with no addressable
URL - "or by calling 1-866-221-9291", and names
datasubjectrequests@cotality.com for requests. The e-mail route is the one
that can be driven and verified.
"""
from lib.broker_helpers import run_ccpa_email_optout


def corelogiccom(dataRow, website_name, in_user_email, run_mode="non-headless"):
    return run_ccpa_email_optout("corelogiccom", dataRow,
                                 privacy_email="datasubjectrequests@cotality.com",
                                 run_mode=run_mode)
