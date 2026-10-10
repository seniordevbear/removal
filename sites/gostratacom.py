"""Strata (gostrata.com/do-not-sell-my-personal-information) — rewritten
2026-10-10 from the live page.

Gravity Forms #5. Field ids from the capture:
  input_5_12_3 first   input_5_12_6 last
  input_5_13_1 street  input_5_13_3 city  input_5_13_4 state  input_5_13_5 zip
  input_5_14 email     input_5_15 phone   input_5_16_1 consent checkbox
  input_5_17 details   input_5_19 / apbct__email_id__gravity_form: HONEYPOTS,
  must stay empty (CleanTalk); filling them marks the request as spam.
"""
import random
from time import sleep

from lib.broker_helpers import (
    safe_chromium_for_broker, screenshot_step, log_step, dismiss_common_consents,
    select_state, missing_pii, fill_field, submission_verdict,
)
from lib.captcha import get_solver
from lib.common import generate_email

URL = "https://www.gostrata.com/do-not-sell-my-personal-information/"
SITE_KEY = "6LddXzgaAAAAAGIeL8C5cg-vK-dynuLbOLmOY0af"


def gostratacom(dataRow, website_name, in_user_email, run_mode):
    broker = "gostratacom"
    name = (dataRow.get("Name") or "").strip()
    if not name:
        raise RuntimeError(broker + ": no name on this profile")
    first, last = name.split()[0], name.split()[-1]
    if not (dataRow.get("State") or "").strip():
        raise missing_pii("State")

    with safe_chromium_for_broker(broker, headless=(run_mode == "headless")) as page:
        page.get(URL)
        sleep(4)
        try:
            dismiss_common_consents(page, broker)
        except Exception:
            pass

        def box(fid, value, required=True):
            if not value and not required:
                return
            fill_field(page, "tag:input@@id=" + fid, value,
                       timeout=8 if required else 3, required=required, broker=broker)
            sleep(random.uniform(0.1, 0.3))

        box("input_5_12_3", first)
        box("input_5_12_6", last)
        box("input_5_13_1", (dataRow.get("Address") or dataRow.get("Street") or "").strip(), required=False)
        box("input_5_13_3", (dataRow.get("City") or "").strip(), required=False)
        st = page.ele("tag:select@@id=input_5_13_4", timeout=4)
        if st:
            select_state(st, dataRow.get("State"))
        box("input_5_13_5", str(dataRow.get("Zipcode") or ""), required=False)
        # 2026-10-11: field_5_8 "Email Address Confirmation" and field_5_15
        # "Phone" are both REQUIRED. The first version skipped them, the form
        # was rejected, and the row was still written as removed. Same shape
        # as the arrests.org Confirm-Email bug.
        email = (dataRow.get("User Email") or "").strip() or generate_email(name)
        box("input_5_14", email)
        box("input_5_8", email)
        phone = (dataRow.get("Phone Number") or "").strip()
        if not phone:
            raise missing_pii("Phone Number")
        box("input_5_15", phone)
        fill_field(page, "tag:textarea@@id=input_5_17",
                   "Please delete my personal information and do not sell or share it.",
                   timeout=3, required=False, broker=broker)
        cb = page.ele("tag:input@@id=input_5_16_1", timeout=3)
        if cb and not cb.states.is_checked:
            cb.click(by_js=True)

        try:
            token = get_solver().recaptcha(sitekey=SITE_KEY, url=URL)["code"]
            page.run_js(
                "var t=arguments[0];document.querySelectorAll(\"textarea[name='g-recaptcha-response']\")"
                ".forEach(function(e){e.style.display='block';e.value=t;});", token)
            sleep(1)
        except Exception as e:
            log_step(broker, "captcha solve failed: %s" % e)

        screenshot_step(page, broker, "before_submit")
        btn = page.ele("tag:input@@id=gform_submit_button_5", timeout=6)
        if not btn:
            raise RuntimeError(broker + ": no Gravity Forms submit button")
        btn.click()
        sleep(4)
        submission_verdict(page, broker)          # raises unless really accepted
        return screenshot_step(page, broker, "after_submit")
