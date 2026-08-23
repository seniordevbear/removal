from lib.broker_helpers import (
    safe_chromium_for_broker, find_input, screenshot_step, log_step,
)
from lib.common import generate_email
from lib.captcha import get_solver
from time import sleep
import json as _json


# Rewritten 2026-08-23 from the live form (user-supplied HTML). Plain POST
# form at https://www.fastpeoplesearch.com/removal: select am=subject, name/email fields, legal checkbox,
# Cloudflare Turnstile. Submitting emails an opt-out link to the address we
# give — the @privacyprosremoval.com catch-all that main.py watches and
# auto-clicks — so step 2 here means "request initiated", completed by the
# inbox bot.
def fastpeoplesearchcom(dataRow, website_name, in_user_email, run_mode):
    broker = "fastpeoplesearchcom"
    name_full = (dataRow.get("Name") or "").strip()
    parts = name_full.split()
    first = parts[0] if parts else ""
    last = parts[-1] if len(parts) > 1 else ""
    if not first or not last:
        raise RuntimeError(broker + ": form requires first AND last name")

    with safe_chromium_for_broker(broker,
                                  headless=(run_mode == "headless")) as page:
        try:
            log_step(broker, "GET https://www.fastpeoplesearch.com/removal")
            page.get("https://www.fastpeoplesearch.com/removal")
            sleep(3)
            if "Just a moment" in (page.html or ""):
                sleep(8)  # Cloudflare interstitial

            # "I am: the subject of this request"
            am = page.ele("css:select[name=am]", timeout=10)
            try:
                am.select.by_value("subject")
            except Exception:
                page.run_js(
                    "var s=document.querySelector('select[name=am]');"
                    "s.value='subject';"
                    "s.dispatchEvent(new Event('change',{bubbles:true}));")
            sleep(0.4)

            for sel, val in (("css:#firstname", first),
                             ("css:#lastname", last),
                             ("css:#email", generate_email(name_full))):
                el = find_input(page, sel, timeout=8.0)
                el.click()
                el.input(val)
                sleep(0.3)

            legal = page.ele("css:input[name=legal]", timeout=6)
            try:
                legal.click()
            except Exception:
                legal.click(by_js=True)
            sleep(0.3)

            ts = page.ele("css:.cf-turnstile[data-sitekey]", timeout=6)
            sitekey = ts.attr("data-sitekey")
            log_step(broker, "solving turnstile " + str(sitekey))
            token = get_solver().turnstile(sitekey=sitekey, url=page.url)["code"]
            page.run_js(
                "var f=document.querySelector('#optout-start');"
                "var i=f.querySelector('input[name=\"cf-turnstile-response\"]');"
                "if(!i){i=document.createElement('input');i.type='hidden';"
                "i.name='cf-turnstile-response';f.appendChild(i);}"
                "i.value=" + _json.dumps(token) + ";")

            shot = screenshot_step(page, broker, "before_submit")
            find_input(page, "css:#optout-start button[type=submit]",
                       "css:button[type=submit]", timeout=6.0).click()
            sleep(6)
            shot = screenshot_step(page, broker, "after_submit") or shot
            log_step(broker, "submitted — confirmation link goes to the "
                             "monitored inbox")
            return shot
        except Exception:
            try:
                screenshot_step(page, broker, "error")
            except Exception:
                pass
            raise
