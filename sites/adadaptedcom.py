from lib.broker_helpers import (
    safe_chromium_for_broker, find_input, screenshot_step, log_step,
)
from time import sleep


def adadaptedcom(dataRow, website_name, in_user_email, run_mode):
    """Rewritten 2026-08-21. The old page had name/email fields; the site
    moved to /do-not-sell/ with a Gravity Forms form that asks ONLY for an
    email address (input_2_4). Old selectors (tag:input@@name=email) can
    never match again — surveyed live before this rewrite."""
    broker = "adadaptedcom"
    with safe_chromium_for_broker(broker,
                                  headless=(run_mode == "headless")) as page:
        try:
            log_step(broker, "GET https://adadapted.com/do-not-sell/")
            page.get("https://adadapted.com/do-not-sell/")
            sleep(2.5)

            email_input = find_input(
                page,
                "css:#input_2_4",
                "css:input[type=email]",
                "css:input[placeholder*='email' i]",
                timeout=8.0,
            )
            email_input.click()
            email_input.input(dataRow.get("User Email") or in_user_email)
            sleep(0.5)

            shot = screenshot_step(page, broker, "before_submit")

            submit = find_input(
                page,
                "css:#gform_submit_button_2",
                "css:input[type=submit]",
                "css:button[type=submit]",
                timeout=6.0,
            )
            submit.click()
            sleep(5)
            shot = screenshot_step(page, broker, "after_submit") or shot
            log_step(broker, "submitted")
            return shot
        except Exception:
            try:
                screenshot_step(page, broker, "error")
            except Exception:
                pass
            raise
