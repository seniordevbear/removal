"""FreePhoneTracer — BeenVerified's opt-out flow (written 2026-10-12).

New broker from the gap list. Its captured opt-out page says "Looking To
Opt-Out of Our People Search? Start by searching for your record here" and
the request goes to BeenVerified's suppression system — the capture's own
page title is "Beenverified" and the form posts to beenverified.com. So this
delegates to the beenverified module rather than duplicating that flow: one
place to fix when BeenVerified changes its form, which it did twice this
month.
"""
from sites.beenverifiedcom import beenverifiedcom


def freephonetracercom(dataRow, website_name, in_user_email, run_mode):
    return beenverifiedcom(dataRow, website_name, in_user_email, run_mode)
