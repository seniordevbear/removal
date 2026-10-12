"""People Data Labs — do-not-sell form (written 2026-10-12 from the live page).

New broker from the gap list. peopledatalabs.com/opt-out-form takes a full
name, an e-mail, the region the request comes from, and reCAPTCHA.
"""
from time import sleep

from lib.broker_helpers import (
    safe_chromium_for_broker, screenshot_step, log_step, dismiss_common_consents,
    fill_field, click_safe, submission_verdict, missing_pii, select_state,
)
from lib.captcha import get_solver

URL = "https://www.peopledatalabs.com/opt-out-form"


def peopledatalabscom(dataRow, website_name, in_user_email, run_mode):
    broker = "peopledatalabscom"
    name = (dataRow.get("Name") or "").strip()
    email = (dataRow.get("User Email") or "").strip()
    if not name:
        raise RuntimeError(broker + ": no name on this profile")
    if not email:
        raise missing_pii("User Email")

    with safe_chromium_for_broker(broker, headless=(run_mode == "headless")) as page:
        page.get(URL)
        sleep(5)
        try:
            dismiss_common_consents(page, broker)
        except Exception:
            pass

        fill_field(page, "tag:input@@id=name", name, timeout=12, broker=broker)
        fill_field(page, "tag:input@@id=email", email, broker=broker)
        loc = page.ele("tag:select@@id=origin-location", timeout=4)
        if loc:
            try:
                select_state(loc, dataRow.get("State"))
            except Exception:
                try:
                    loc.select.by_text("United States")
                except Exception as e:
                    log_step(broker, "origin-location: %s" % e)

        key = page.run_js("var e=document.querySelector('[data-sitekey]');return e?e.getAttribute('data-sitekey'):'';")
        if key:
            try:
                token = get_solver().recaptcha(sitekey=key, url=URL)["code"]
                page.run_js(
                    "var t=arguments[0];document.querySelectorAll(\"textarea[name='g-recaptcha-response']\")"
                    ".forEach(function(e){e.style.display='block';e.value=t;});", token)
                sleep(1)
            except Exception as e:
                log_step(broker, "captcha solve failed: %s" % e)

        screenshot_step(page, broker, "before_submit")
        click_safe(page, "tag:button@@id=submit", broker=broker)
        sleep(4)
        submission_verdict(page, broker)
        return screenshot_step(page, broker, "after_submit")
