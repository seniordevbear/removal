from lib.broker_helpers import (
    safe_chromium_for_broker, find_input, screenshot_step, log_step, _state_full_name,
)
from lib.common import generate_email, generate_phone_number
from lib.captcha import get_solver
from time import sleep
import json as _json
import re as _re
import logging


# Rewritten 2026-08-29 from the live form. gostrata's opt-out is a Gravity
# Form (id 5) at /do-not-sell-my-personal-information/: name block
# (input_5_12_3/_12_6), address block (13_1 street, 13_3 city, 13_4 state
# SELECT, 13_5 zip), Email (14) + Email confirmation (8), Phone (15,
# required), a certification checkbox (16_1), and reCAPTCHA v2. The old
# script targeted input_13.4 as an <input> (it is a <select>) and missed the
# required phone/confirmation — hence the crash.
def gostratacom(dataRow, website_name, in_user_email, run_mode):
    broker = "gostratacom"
    name_full = (dataRow.get("Name") or "").strip()
    parts = name_full.split()
    first = parts[0] if parts else ""
    last = parts[-1] if len(parts) > 1 else ""
    if not first or not last:
        raise RuntimeError(broker + ": requires first and last name")
    email = generate_email(name_full)
    phone = (dataRow.get("Phone Number") or "").strip() or generate_phone_number()
    state_full = _state_full_name(dataRow.get("State") or "")

    with safe_chromium_for_broker(broker,
                                  headless=(run_mode == "headless")) as page:
        try:
            log_step(broker, "GET https://www.gostrata.com/do-not-sell-my-personal-information/")
            page.get("https://www.gostrata.com/do-not-sell-my-personal-information/")
            sleep(3)

            def fill(sel, val):
                if not val:
                    return
                el = find_input(page, sel, timeout=6.0)
                el.click(); el.input(val); sleep(0.2)

            fill("css:#input_5_12_3", first)
            fill("css:#input_5_12_6", last)
            fill("css:#input_5_13_1", (dataRow.get("Address") or dataRow.get("Street") or "").strip())
            fill("css:#input_5_13_3", (dataRow.get("City") or "").strip())
            fill("css:#input_5_13_5", (dataRow.get("Zipcode") or "").strip())
            fill("css:#input_5_14", email)
            fill("css:#input_5_8", email)       # confirmation must match
            fill("css:#input_5_15", phone)

            if state_full:
                try:
                    page.ele("css:#input_5_13_4", timeout=4).select.by_text(state_full)
                except Exception:
                    try:
                        page.ele("css:select[name='input_13.4']").select.by_text(state_full)
                    except Exception as e:
                        log_step(broker, "state select skipped: " + str(e), logging.WARNING)
            sleep(0.2)

            # certification checkbox
            try:
                cb = page.ele("css:#input_5_16_1", timeout=4)
                if cb:
                    try:
                        cb.click()
                    except Exception:
                        cb.click(by_js=True)
            except Exception:
                pass
            sleep(0.3)

            # reCAPTCHA v2 — sitekey lives in the widget iframe URL at runtime
            frame = page.ele("css:iframe[src*='recaptcha']", timeout=10)
            m = _re.search(r"[?&]k=([\w-]+)", frame.attr("src") or "")
            if not m:
                raise RuntimeError(broker + ": recaptcha sitekey not found")
            log_step(broker, "solving recaptcha " + m.group(1))
            token = get_solver().recaptcha(sitekey=m.group(1), url=page.url)["code"]
            page.run_js(
                "var t=document.getElementById('g-recaptcha-response');"
                "if(t){t.value=" + _json.dumps(token) + ";}"
                "document.querySelectorAll('textarea[name=\"g-recaptcha-response\"]')"
                ".forEach(function(x){x.value=" + _json.dumps(token) + ";});")
            sleep(0.5)

            shot = screenshot_step(page, broker, "before_submit")
            find_input(page, "css:#gform_submit_button_5", "css:input[type=submit]",
                       "css:button[type=submit]", timeout=6).click()
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
