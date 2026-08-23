from lib.broker_helpers import (
    safe_chromium_for_broker, find_input, screenshot_step, log_step,
    state_abbrev,
)
from lib.captcha import get_solver
from time import sleep
import json as _json
import re as _re


# Rewritten 2026-08-23 from the live form (user-supplied HTML). Vue/Inertia
# app at optout.audienceacuity.com: typed fields (real key events keep Vue's
# state in sync), state select uses two-letter VALUES, both suppression
# checkboxes, and a Google reCAPTCHA v2 whose sitekey only exists at runtime
# in the widget iframe URL.
def audienceacuitycom(dataRow, website_name, in_user_email, run_mode):
    broker = "audienceacuitycom"
    name_full = (dataRow.get("Name") or "").strip()
    parts = name_full.split()
    first = parts[0] if parts else ""
    last = parts[-1] if len(parts) > 1 else ""
    address = (dataRow.get("Address") or dataRow.get("Street") or "").strip()
    city = (dataRow.get("City") or "").strip()
    zipc = (dataRow.get("Zipcode") or "").strip()
    email = dataRow.get("User Email") or in_user_email
    if not (first and last and email):
        raise RuntimeError(broker + ": form requires name and email")

    with safe_chromium_for_broker(broker,
                                  headless=(run_mode == "headless")) as page:
        try:
            log_step(broker, "GET https://optout.audienceacuity.com")
            page.get("https://optout.audienceacuity.com")
            sleep(4)  # Inertia app boot

            for sel, val in (("css:#first_name", first),
                             ("css:#last_name", last),
                             ("css:#email", email),
                             ("css:#street_address", address),
                             ("css:#city", city),
                             ("css:#zip_code", zipc)):
                if not val:
                    continue
                el = find_input(page, sel, timeout=8.0)
                el.click()
                el.input(val)
                sleep(0.25)

            try:
                page.ele("css:#state", timeout=5).select.by_value(
                    state_abbrev(dataRow.get("State") or ""))
            except Exception as e:
                log_step(broker, "state select skipped: " + str(e))
            sleep(0.3)

            for cb in ("css:#individual_level", "css:#household_level"):
                el = page.ele(cb, timeout=5)
                try:
                    el.click()
                except Exception:
                    el.click(by_js=True)
                sleep(0.2)

            # sitekey lives only in the rendered widget iframe URL (k=...)
            frame = page.ele("css:iframe[src*='recaptcha']", timeout=10)
            m = _re.search(r"[?&]k=([\w-]+)", frame.attr("src") or "")
            if not m:
                raise RuntimeError(broker + ": recaptcha sitekey not found")
            sitekey = m.group(1)
            log_step(broker, "solving recaptcha " + sitekey)
            token = get_solver().recaptcha(sitekey=sitekey, url=page.url)["code"]
            page.run_js(
                "var t=document.querySelector('textarea[name=\"g-recaptcha-response\"]');"
                "if(!t){t=document.createElement('textarea');"
                "t.name='g-recaptcha-response';t.style.display='none';"
                "document.querySelector('form').appendChild(t);}"
                "t.value=" + _json.dumps(token) + ";"
                "if(window.grecaptcha){window.grecaptcha.getResponse="
                "function(){return " + _json.dumps(token) + ";};}")

            shot = screenshot_step(page, broker, "before_submit")
            find_input(page, "css:button[type=submit]", timeout=6.0).click()
            sleep(6)
            shot = screenshot_step(page, broker, "after_submit") or shot
            log_step(broker, "submitted")
            return shot
        except Exception:
            try:
                screenshot_step(page, broker, "error")
            except Exception:
                pass
            raise
