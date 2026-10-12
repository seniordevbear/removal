"""LiveRamp — TrustArc data subject request form (written 2026-10-12).

New broker from the gap list, confirmed by 19 sources. The form fields carry
generated UUID names, so every field is addressed by its aria-label, which is
what TrustArc renders consistently across its tenants.
"""
from time import sleep

from lib.broker_helpers import (
    safe_chromium_for_broker, screenshot_step, log_step, dismiss_common_consents,
    fill_field, click_safe, submission_verdict, missing_pii,
)
from lib.captcha import get_solver

URL = ("https://submit-irm.trustarc.com/services/validation/"
       "697ea013-8e66-44aa-94c5-fa9d38dd439c")


def liverampcom(dataRow, website_name, in_user_email, run_mode):
    broker = "liverampcom"
    name = (dataRow.get("Name") or "").strip()
    email = (dataRow.get("User Email") or "").strip()
    if not name:
        raise RuntimeError(broker + ": no name on this profile")
    if not email:
        raise missing_pii("User Email")
    first, last = name.split()[0], name.split()[-1]

    with safe_chromium_for_broker(broker, headless=(run_mode == "headless")) as page:
        page.get(URL)
        sleep(6)
        try:
            dismiss_common_consents(page, broker)
        except Exception:
            pass

        fill_field(page, "css:input[aria-label='Enter First name']", first, timeout=15, broker=broker)
        fill_field(page, "css:input[aria-label='Enter Last name']", last, broker=broker)
        fill_field(page, "css:input[aria-label='Enter Email']", email, broker=broker)

        # the acknowledgement checkbox TrustArc requires before submitting
        click_safe(page, "css:form input[type=checkbox]", required=False, broker=broker)

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
        click_safe(page, "css:form button:not([type=button])", broker=broker)
        sleep(5)
        submission_verdict(page, broker)
        return screenshot_step(page, broker, "after_submit")
