from lib.broker_helpers import (
    safe_chromium_for_broker, find_input, screenshot_step, log_step,
    _state_full_name,
)
from lib.captcha import get_solver
from time import sleep
import json as _json


# Rewritten 2026-08-23 from the live form (user-supplied HTML). The opt-out
# moved to /privacy-rights-request/ — a Gravity Form (id 4) with a required
# address block, phone, a "Privacy Choice" select (we pick "Delete"), a
# consent checkbox, and Cloudflare Turnstile whose token field is named
# cf-turnstile-response_4.
def dataaxlecom(dataRow, website_name, in_user_email, run_mode):
    broker = "dataaxlecom"
    name_full = (dataRow.get("Name") or "").strip()
    parts = name_full.split()
    first = parts[0] if parts else ""
    last = parts[-1] if len(parts) > 1 else ""
    address = (dataRow.get("Address") or dataRow.get("Street") or "").strip()
    city = (dataRow.get("City") or "").strip()
    state_full = _state_full_name(dataRow.get("State") or "")
    zipc = (dataRow.get("Zipcode") or "").strip()
    email = dataRow.get("User Email") or in_user_email
    # Phone is REQUIRED by this form. Policy (__removal.py): never fabricate
    # PII sent to a broker — a made-up phone could match a real stranger and
    # taints the request's attestation of accuracy. No phone -> honest skip.
    phone = (dataRow.get("Phone Number") or "").strip()

    missing = [k for k, v in (("name", first and last), ("address", address),
                              ("city", city), ("state", state_full),
                              ("zip", zipc), ("email", email),
                              ("phone", phone)) if not v]
    if missing:
        raise RuntimeError(broker + ": form requires " + ", ".join(missing))

    with safe_chromium_for_broker(broker,
                                  headless=(run_mode == "headless")) as page:
        try:
            log_step(broker, "GET https://www.data-axle.com/privacy-rights-request/")
            page.get("https://www.data-axle.com/privacy-rights-request/")
            sleep(3)

            for sel, val in (("css:#input_4_1", first),
                             ("css:#input_4_3", last),
                             ("css:#input_4_14_1", address),
                             ("css:#input_4_14_3", city),
                             ("css:#input_4_14_5", zipc),
                             ("css:#input_4_9", email),
                             ("css:#input_4_10", phone)):
                el = find_input(page, sel, timeout=8.0)
                el.click()
                el.input(val)
                sleep(0.25)

            page.ele("css:#input_4_14_4", timeout=6).select.by_value(state_full)
            sleep(0.3)
            page.ele("css:#input_4_11", timeout=6).select.by_value("Delete")
            sleep(0.3)

            consent = page.ele("css:#choice_4_13_1", timeout=6)
            try:
                consent.click()
            except Exception:
                consent.click(by_js=True)
            sleep(0.3)

            ts = page.ele("css:#cf-turnstile_4", timeout=6)
            sitekey = ts.attr("data-sitekey")
            log_step(broker, "solving turnstile " + str(sitekey))
            token = get_solver().turnstile(sitekey=sitekey, url=page.url)["code"]
            page.run_js(
                "var f=document.querySelector('#gform_4');"
                "var i=f.querySelector('input[name=\"cf-turnstile-response_4\"],"
                "textarea[name=\"cf-turnstile-response_4\"]');"
                "if(!i){i=document.createElement('input');i.type='hidden';"
                "i.name='cf-turnstile-response_4';f.appendChild(i);}"
                "i.value=" + _json.dumps(token) + ";")

            shot = screenshot_step(page, broker, "before_submit")
            find_input(page, "css:#gform_submit_button_4",
                       "css:button[type=submit]", timeout=6.0).click()
            sleep(7)
            shot = screenshot_step(page, broker, "after_submit") or shot
            log_step(broker, "submitted")
            return shot
        except Exception:
            try:
                screenshot_step(page, broker, "error")
            except Exception:
                pass
            raise
