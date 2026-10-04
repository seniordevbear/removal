from lib.broker_helpers import run_ccpa_email_optout


def alescodatacom(dataRow, website_name, in_user_email, run_mode):
    """2026-10-04: /do-not-sell-my-personal-information/ is a 404. The
    replacement, alescodata.com/privacy-center/, embeds a HubSpot form that
    only renders in a browser, and its text states: "you can also opt out of
    the sell of your personal information by emailing us at:
    privacy@alescodata.com". Use that documented route until the HubSpot
    form has been captured and scripted (0/73 runs succeeded before).
    """
    return run_ccpa_email_optout("alescodatacom", dataRow,
                                 privacy_email="privacy@alescodata.com",
                                 run_mode=run_mode)
