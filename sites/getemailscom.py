"""GetEmails / Retention.com (app.retention.com/optout) — rewritten 2026-10-10.

Captured form: optout-email + optout-zipcode, an "authorized agent" checkbox
we leave unticked, reCAPTCHA, and a plain button (not type=submit).
126 crashes / 0 successes in the 5-8 Oct logs on the old selectors.
"""
import random
from time import sleep

from lib.broker_helpers import (
    safe_chromium_for_broker, screenshot_step, log_step, dismiss_common_consents, missing_pii,
)
from lib.captcha import get_solver

URL = "https://app.retention.com/optout/"
SITE_KEY = "6LdSFZAaAAAAADBGqs4Mm5BHXkBKJ4kZXdnlhf_p"


def getemailscom(dataRow, website_name, in_user_email, run_mode):
    broker = "getemailscom"
    email = (dataRow.get("User Email") or "").strip()
    zipc = str(dataRow.get("Zipcode") or "").strip()
    if not email:
        raise missing_pii("User Email")
    if not zipc:
        raise missing_pii("Zipcode")

    with safe_chromium_for_broker(broker, headless=(run_mode == "headless")) as page:
        page.get(URL)
        sleep(4)
        try:
            dismiss_common_consents(page, broker)
        except Exception:
            pass

        em = page.ele("tag:input@@id=optout-email", timeout=12)
        if not em:
            raise RuntimeError(broker + ": no #optout-email box (page changed)")
        em.click()
        em.input(email)
        sleep(random.uniform(0.2, 0.5))

        zp = page.ele("tag:input@@id=optout-zipcode", timeout=5)
        if zp:
            zp.click()
            zp.input(zipc)

        try:
            token = get_solver().recaptcha(sitekey=SITE_KEY, url=URL)["code"]
            page.run_js(
                "var t=arguments[0];document.querySelectorAll(\"textarea[name='g-recaptcha-response']\")"
                ".forEach(function(e){e.style.display='block';e.value=t;});", token)
            sleep(1)
        except Exception as e:
            log_step(broker, "captcha solve failed: %s" % e)

        screenshot_step(page, broker, "before_submit")
        # the submit control is <button type="button"> inside #verify_opt
        btn = (page.ele("css:#verify_opt button", timeout=5)
               or page.ele("xpath://button[contains(.,'Opt') or contains(.,'Submit')]", timeout=3))
        if not btn:
            raise RuntimeError(broker + ": no submit button in #verify_opt")
        btn.click()
        sleep(6)
        path = screenshot_step(page, broker, "after_submit")
        html = (page.html or "").lower()
        if any(w in html for w in ("thank", "check your email", "confirm", "received", "success")):
            log_step(broker, "submitted, page confirmed")
            return path
        raise RuntimeError(broker + ": no confirmation message after submit")
