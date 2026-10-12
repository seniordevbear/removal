"""IDM (us.com) — do-not-sell form (written 2026-10-12 from the live page).

New broker from the gap list, confirmed by 14 sources. A single Gravity Form
on idm.us.com/do-not-sell-my-personal-information/. Field names verified
against the captured markup rather than inferred from order:

    input_7 Email*   input_1 First Name*  input_2 Last Name*
    input_3 Address* input_4 City*        input_5 State*   input_6 Zip*

Every one is required, so a profile missing any of them is parked as
needs-data rather than submitted and rejected.
"""
from time import sleep

from lib.broker_helpers import (
    safe_chromium_for_broker, screenshot_step, log_step, dismiss_common_consents,
    fill_field, click_safe, submission_verdict, missing_pii, state_abbrev,
    unfilled_required_fields,
)
from lib.captcha import get_solver

URL = "https://idm.us.com/do-not-sell-my-personal-information/"


def uscom(dataRow, website_name, in_user_email, run_mode):
    broker = "uscom"
    name = (dataRow.get("Name") or "").strip()
    if not name:
        raise RuntimeError(broker + ": no name on this profile")
    first, last = name.split()[0], name.split()[-1]

    email = (dataRow.get("User Email") or "").strip()
    address = (dataRow.get("Address") or dataRow.get("Street") or "").strip()
    city = (dataRow.get("City") or "").strip()
    state = (dataRow.get("State") or "").strip()
    zipc = str(dataRow.get("Zipcode") or "").strip()
    for label, value in (("User Email", email), ("Address", address),
                         ("City", city), ("State", state), ("Zipcode", zipc)):
        if not value:
            raise missing_pii(label)

    with safe_chromium_for_broker(broker, headless=(run_mode == "headless")) as page:
        page.get(URL)
        sleep(4)
        try:
            dismiss_common_consents(page, broker)
        except Exception:
            pass

        fill_field(page, "tag:input@@name=input_7", email, timeout=12, broker=broker)
        fill_field(page, "tag:input@@name=input_1", first, broker=broker)
        fill_field(page, "tag:input@@name=input_2", last, broker=broker)
        fill_field(page, "tag:input@@name=input_3", address, broker=broker)
        fill_field(page, "tag:input@@name=input_4", city, broker=broker)
        fill_field(page, "tag:input@@name=input_5", state_abbrev(state) or state, broker=broker)
        fill_field(page, "tag:input@@name=input_6", zipc, broker=broker)

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

        missing = unfilled_required_fields(page)
        if missing:
            screenshot_step(page, broker, "error_incomplete")
            raise missing_pii(*missing)

        screenshot_step(page, broker, "before_submit")
        click_safe(page, "tag:input@@id=gform_submit_button_2", broker=broker)
        sleep(4)
        submission_verdict(page, broker)
        return screenshot_step(page, broker, "after_submit")
