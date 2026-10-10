"""Fetcher (app.fetcher.ai/opt-out) — rewritten 2026-10-10 from the live page.

The old script drove a layout that no longer exists (122 crashes in the
5-8 Oct logs, 0 successes). The current form is three fields inside an Ant
Design form plus reCAPTCHA.
"""
import random
from time import sleep

from lib.broker_helpers import (
    safe_chromium_for_broker, screenshot_step, log_step, dismiss_common_consents,
)
from lib.captcha import get_solver
from lib.common import generate_email

URL = "https://app.fetcher.ai/opt-out"
SITE_KEY = "6LeTnMkUAAAAAJ3xj0Qe1vQWJ0Yk2XQ4vYpTnO3r"  # page-rendered; token is injected by name


def fetcherai(dataRow, website_name, in_user_email, run_mode):
    broker = "fetcherai"
    name = (dataRow.get("Name") or "").strip()
    if not name:
        raise RuntimeError(broker + ": no name on this profile")
    first = name.split()[0]
    last = name.split()[-1]

    with safe_chromium_for_broker(broker, headless=(run_mode == "headless")) as page:
        page.get(URL)
        sleep(4)
        try:
            dismiss_common_consents(page, broker)
        except Exception:
            pass

        def box(el_id, value):
            el = page.ele("tag:input@@id=" + el_id, timeout=12)
            if not el:
                raise RuntimeError("%s: no #%s on the opt-out form" % (broker, el_id))
            el.click()
            sleep(random.uniform(0.1, 0.3))
            el.input(value)

        box("first_name", first)
        box("last_name", last)
        box("email", (dataRow.get("User Email") or "").strip() or generate_email(name))

        # reCAPTCHA: the widget renders its own textarea; solve by sitekey read
        # from the page so a key rotation does not silently break the script.
        key = page.run_js(
            "var e=document.querySelector('[data-sitekey]');return e?e.getAttribute('data-sitekey'):'';") or SITE_KEY
        try:
            token = get_solver().recaptcha(sitekey=key, url=URL)["code"]
            page.run_js(
                "var t=arguments[0];document.querySelectorAll(\"textarea[name='g-recaptcha-response']\")"
                ".forEach(function(e){e.style.display='block';e.value=t;});", token)
            sleep(1)
        except Exception as e:
            log_step(broker, "captcha solve failed: %s" % e)

        screenshot_step(page, broker, "before_submit")
        btn = page.ele("css:form button[type=submit]", timeout=6)
        if not btn:
            raise RuntimeError(broker + ": no submit button on the opt-out form")
        btn.click()
        sleep(6)
        path = screenshot_step(page, broker, "after_submit")
        html = (page.html or "").lower()
        if "thank" in html or "received" in html or "submitted" in html:
            log_step(broker, "submitted, page confirmed")
            return path
        raise RuntimeError(broker + ": no confirmation message after submit")
