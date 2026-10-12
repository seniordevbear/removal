"""LocateSmarter — CCPA opt-out form (written 2026-10-12 from the live page).

New broker from the data-broker gap list. forms.locatesmarter.com/optoutform
is a single self-service form: name, e-mail, full address, a "submitting this
for myself" checkbox, a "do not sell" checkbox and reCAPTCHA. No search step.
"""
import random
from time import sleep

from lib.broker_helpers import (
    safe_chromium_for_broker, screenshot_step, log_step, dismiss_common_consents,
    select_state, missing_pii, fill_field, click_safe, submission_verdict,
)
from lib.captcha import get_solver
from lib.common import generate_email

URL = "https://forms.locatesmarter.com/optoutform"


def locatesmartercom(dataRow, website_name, in_user_email, run_mode):
    broker = "locatesmartercom"
    name = (dataRow.get("Name") or "").strip()
    if not name:
        raise RuntimeError(broker + ": no name on this profile")
    first, last = name.split()[0], name.split()[-1]
    for field in ("Address", "City", "State", "Zipcode"):
        if not str(dataRow.get(field) or "").strip():
            raise missing_pii(field if field != "Zipcode" else "Zipcode")

    with safe_chromium_for_broker(broker, headless=(run_mode == "headless")) as page:
        page.get(URL)
        sleep(4)
        try:
            dismiss_common_consents(page, broker)
        except Exception:
            pass

        fill_field(page, "tag:input@@id=FormData_FirstName", first, broker=broker)
        fill_field(page, "tag:input@@id=FormData_LastName", last, broker=broker)
        fill_field(page, "tag:input@@id=FormData_Email",
                   (dataRow.get("User Email") or "").strip() or generate_email(name), broker=broker)
        fill_field(page, "tag:input@@id=FormData_Address1", dataRow["Address"], broker=broker)
        fill_field(page, "tag:input@@id=FormData_City", dataRow["City"], broker=broker)
        st = page.ele("tag:select@@id=FormData_State", timeout=5)
        if st:
            select_state(st, dataRow["State"])
        fill_field(page, "tag:input@@id=FormData_ZipCode", str(dataRow["Zipcode"]), broker=broker)

        # "I am submitting this request for myself" — NOT the authorised-agent
        # branch, which asks for agent details we do not have.
        click_safe(page, "tag:input@@id=FormData_IsSelfRequest", required=False, broker=broker)
        click_safe(page, "tag:input@@id=FormData_RequestToNotSell", required=False, broker=broker)

        key = page.run_js("var e=document.querySelector('[data-sitekey]');return e?e.getAttribute('data-sitekey'):'';")
        if key:
            try:
                token = get_solver().recaptcha(sitekey=key, url=URL)["code"]
                page.run_js(
                    "var t=arguments[0];document.querySelectorAll(\"textarea[name='g-recaptcha-response'],"
                    "input[name='g-recaptcha-response']\").forEach(function(e){e.style.display='block';e.value=t;});", token)
                sleep(1)
            except Exception as e:
                log_step(broker, "captcha solve failed: %s" % e)

        screenshot_step(page, broker, "before_submit")
        click_safe(page, "css:form button[type=submit], form input[type=submit]", broker=broker)
        sleep(4)
        submission_verdict(page, broker)
        return screenshot_step(page, broker, "after_submit")
