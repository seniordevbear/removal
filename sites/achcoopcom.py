from lib.broker_helpers import (
    safe_chromium_for_broker, find_input, screenshot_step, log_step,
)
from time import sleep
import logging


def achcoopcom(dataRow, website_name, in_user_email, run_mode):
    """Rewritten 2026-08-21. The site rebuilt on Wix: inputs have UUID ids
    (form-field-input-<uuid>) so the old name=first-name selectors can never
    match. The stable handles are the human-readable placeholders
    ("Enter your first name" ...) and aria-labels — surveyed live."""
    broker = "achcoopcom"
    name_full = (dataRow.get("Name") or "").strip()
    parts = name_full.split()
    first = parts[0] if parts else ""
    last = parts[-1] if len(parts) > 1 else ""

    with safe_chromium_for_broker(broker,
                                  headless=(run_mode == "headless")) as page:
        try:
            log_step(broker, "GET https://www.achcoop.com/do-not-sell-my-personal-info")
            page.get("https://www.achcoop.com/do-not-sell-my-personal-info")
            sleep(3)

            def fill(frag, value, required=False):
                if not value:
                    if required:
                        raise RuntimeError("missing value for " + frag)
                    return
                try:
                    el = find_input(
                        page,
                        "css:input[placeholder*='%s' i]" % frag,
                        "css:input[aria-label*='%s' i]" % frag,
                        timeout=6.0,
                    )
                except ValueError:
                    if required:
                        raise
                    log_step(broker, frag + " field absent, skipped",
                             logging.WARNING)
                    return
                try:
                    el.click()
                except Exception:
                    el.click(by_js=True)
                el.input(value)
                sleep(0.3)

            fill("first name", first, required=True)
            fill("last name", last, required=True)
            fill("your address", dataRow.get("Address") or dataRow.get("Street"))
            fill("your city", dataRow.get("City"))
            fill("zip code", dataRow.get("Zipcode"))

            # request-type checkbox ("Select your request") — the form marks
            # it required; tick the first option.
            try:
                cb = page.ele("css:input[type=checkbox][name*='request' i]",
                              timeout=4.0)
                if cb:
                    try:
                        cb.click()
                    except Exception:
                        cb.click(by_js=True)
                    sleep(0.3)
            except Exception:
                log_step(broker, "request checkbox not found", logging.WARNING)

            shot = screenshot_step(page, broker, "before_submit")

            submit = find_input(
                page,
                "css:button[type=submit]",
                "xpath://button[contains(translate(., 'SUBMIT', 'submit'), 'submit')]",
                timeout=6.0,
            )
            try:
                submit.click()
            except Exception:
                submit.click(by_js=True)
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
