from lib.broker_helpers import (
    safe_chromium_for_broker, find_input, screenshot_step, log_step,
)
from lib.common import generate_email
from lib.captcha import get_solver
from time import sleep
import json as _json


# Rewritten 2026-08-27 from the live form (user-supplied HTML). TruePeopleSearch
# privacy form at /removal: RightsExerciseType="subject", First/Last name, Email,
# a required AuthorizeContact checkbox, and an hCaptcha (NOT Turnstile). The
# confirmation link is emailed to the address we give, so we use the monitored
# @privacyprosremoval.com inbox (main.py auto-confirms).
def truepeoplesearchcom(dataRow, website_name, in_user_email, run_mode):
    broker = "truepeoplesearchcom"
    name_full = (dataRow.get("Name") or "").strip()
    parts = name_full.split()
    first = parts[0] if parts else ""
    last = parts[-1] if len(parts) > 1 else ""
    if not first or not last:
        raise RuntimeError(broker + ": requires first and last name")

    with safe_chromium_for_broker(broker,
                                  headless=(run_mode == "headless")) as page:
        try:
            log_step(broker, "GET https://www.truepeoplesearch.com/removal")
            page.get("https://www.truepeoplesearch.com/removal")
            sleep(3)
            if "Just a moment" in (page.html or ""):
                sleep(8)

            try:
                page.ele("css:#RightsExerciseType", timeout=6).select.by_value("subject")
            except Exception:
                pass
            sleep(0.2)

            find_input(page, "css:#FirstName", timeout=8).input(first); sleep(0.2)
            find_input(page, "css:#LastName").input(last); sleep(0.2)
            find_input(page, "css:#Email").input(generate_email(name_full)); sleep(0.2)

            cb = page.ele("css:#AuthorizeContact", timeout=5)
            try:
                cb.click()
            except Exception:
                cb.click(by_js=True)
            sleep(0.3)

            # hCaptcha
            hc = page.ele("css:.h-captcha[data-sitekey]", timeout=8)
            sitekey = hc.attr("data-sitekey")
            log_step(broker, "solving hcaptcha " + str(sitekey))
            token = get_solver().hcaptcha(sitekey=sitekey, url=page.url)["code"]
            # both textareas the widget exposes must carry the token
            page.run_js(
                "document.querySelectorAll("
                "'textarea[name=\"h-captcha-response\"],textarea[name=\"g-recaptcha-response\"]')"
                ".forEach(function(t){t.value=" + _json.dumps(token) + ";});")
            sleep(0.5)

            shot = screenshot_step(page, broker, "before_submit")
            find_input(page, "css:button[type=submit]", timeout=6).click()
            sleep(6)

            html = (page.html or "").lower()
            if ("thank" in html or "check your email" in html or "received" in html
                    or "confirmation" in html or "sent" in html):
                shot = screenshot_step(page, broker, "after_submit") or shot
                log_step(broker, "submitted")
                return shot
            screenshot_step(page, broker, "error")
            raise RuntimeError(broker + ": submitted but no confirmation seen")
        except Exception:
            try:
                screenshot_step(page, broker, "error")
            except Exception:
                pass
            raise
