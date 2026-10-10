"""Endato / Enformion privacy portal — rewritten 2026-10-10 from the live page.

endato.com/privacy-policy/opt-out/ now redirects to go.enformion.com's portal.
Captured fields: requesterType select, firstName / middleName / lastName /
email, a privacyAuthorization checkbox, a hidden requestType=optout, and
`yourFavoriteNumber` — a HONEYPOT that must stay empty. Submit is
<input type="button">, so a form.submit() would bypass its handler.
"""
import random
from time import sleep

from lib.broker_helpers import (
    safe_chromium_for_broker, screenshot_step, log_step, dismiss_common_consents, missing_pii,
)
from lib.captcha import get_solver

URL = "https://go.enformion.com/privacy-policy/opt-out/"
SITE_KEY = "6LctO8YpAAAAAPjFnOnh1XSs0a0Y2pJCOuMuSDjg"


def endatocom(dataRow, website_name, in_user_email, run_mode):
    broker = "endatocom"
    name = (dataRow.get("Name") or "").strip()
    email = (dataRow.get("User Email") or "").strip()
    if not name:
        raise RuntimeError(broker + ": no name on this profile")
    if not email:
        raise missing_pii("User Email")
    parts = name.split()
    first, last = parts[0], parts[-1]
    middle = parts[1] if len(parts) > 2 else ""

    with safe_chromium_for_broker(broker, headless=(run_mode == "headless")) as page:
        page.get(URL)
        sleep(5)
        try:
            dismiss_common_consents(page, broker)
        except Exception:
            pass

        # "I am:" — the consumer, not an authorised agent (that branch asks for
        # agent details we do not have).
        sel = page.ele("tag:select@@name=requesterType", timeout=12)
        if not sel:
            raise RuntimeError(broker + ": requesterType select not found (portal changed)")
        picked = False
        for text in ("Consumer", "Myself", "The consumer", "Individual"):
            try:
                sel.select.by_text(text)
                picked = True
                break
            except Exception:
                continue
        if not picked:
            try:
                sel.select.by_index(1)
            except Exception:
                pass
        sleep(1)

        def box(nm, value, required=True):
            el = page.ele("tag:input@@name=" + nm, timeout=8 if required else 3)
            if not el:
                if required:
                    raise RuntimeError("%s: no input[name=%s]" % (broker, nm))
                return
            el.click()
            sleep(random.uniform(0.1, 0.3))
            el.input(value)

        box("firstName", first)
        if middle:
            box("middleName", middle, required=False)
        box("lastName", last)
        box("email", email)
        # yourFavoriteNumber is the honeypot — deliberately left untouched.

        cb = page.ele("tag:input@@name=privacyAuthorization", timeout=4)
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
        btn = (page.ele("css:input[type=button][value='Submit']", timeout=6)
               or page.ele("xpath://input[@value='Submit'] | //button[contains(.,'Submit')]", timeout=3))
        if not btn:
            raise RuntimeError(broker + ": no Submit control on the portal form")
        btn.click()
        sleep(7)
        path = screenshot_step(page, broker, "after_submit")
        html = (page.html or "").lower()
        if any(w in html for w in ("thank you", "received", "submitted", "confirmation")):
            log_step(broker, "submitted, portal confirmed")
            return path
        raise RuntimeError(broker + ": no confirmation after submit")
