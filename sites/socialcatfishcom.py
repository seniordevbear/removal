from lib.broker_helpers import (
    safe_chromium_for_broker, find_input, screenshot_step, log_step, state_abbrev,
)
from lib.common import generate_email
from lib.captcha import get_solver
from time import sleep
import json as _json
import logging


# Rewritten 2026-08-27 from the live opt-out form (user-supplied HTML). The
# real form lives at /opt-out?id=request_optout (the earlier search widget was
# a different page). Direct POST form: firstname/lastname/email (mandatory) +
# a Cloudflare Turnstile. Confirmation goes to the email we supply, so we use
# the monitored @privacyprosremoval.com inbox (main.py auto-confirms). The
# "third_party_opt" checkbox is left UNchecked (we are the data subject).
def socialcatfishcom(dataRow, website_name, in_user_email, run_mode):
    broker = "socialcatfishcom"
    name_full = (dataRow.get("Name") or "").strip()
    parts = name_full.split()
    first = parts[0] if parts else ""
    last = parts[-1] if len(parts) > 1 else ""
    if not first or not last:
        raise RuntimeError(broker + ": requires first and last name")

    with safe_chromium_for_broker(broker,
                                  headless=(run_mode == "headless")) as page:
        try:
            url = "https://socialcatfish.com/opt-out?id=request_optout"
            log_step(broker, "GET " + url)
            page.get(url)
            sleep(4)
            if "Just a moment" in (page.html or ""):
                sleep(8)  # Cloudflare interstitial

            find_input(page, "css:#first-name", "css:input[name=firstname]",
                       timeout=10).input(first)
            sleep(0.2)
            find_input(page, "css:#last-name", "css:input[name=lastname]").input(last)
            sleep(0.2)
            find_input(page, "css:#email", "css:input[name=email]").input(
                generate_email(name_full))
            sleep(0.3)

            # Hidden state field the form posts; fill from the profile if blank.
            st = (dataRow.get("State") or "").strip()
            if st:
                try:
                    ab = state_abbrev(st)
                    page.run_js(
                        "var s=document.querySelector('input[name=\"state\"]');"
                        "if(s){s.value=" + _json.dumps(ab) + ";}")
                except Exception:
                    pass

            # Cloudflare Turnstile
            ts = page.ele("css:.cf-turnstile[data-sitekey]", timeout=8)
            sitekey = ts.attr("data-sitekey")
            log_step(broker, "solving turnstile " + str(sitekey))
            token = get_solver().turnstile(sitekey=sitekey, url=page.url)["code"]
            page.run_js(
                "var i=document.querySelector('input[name=\"cf-turnstile-response\"]');"
                "if(!i){i=document.createElement('input');i.type='hidden';"
                "i.name='cf-turnstile-response';"
                "document.getElementById('request_optout_form').appendChild(i);}"
                "i.value=" + _json.dumps(token) + ";")
            sleep(0.5)

            shot = screenshot_step(page, broker, "before_submit")
            find_input(page, "css:#request_optout_form button[type=submit]",
                       "css:button[type=submit]", timeout=6).click()
            sleep(6)

            html = (page.html or "").lower()
            if ("thank" in html or "received" in html or "check your email" in html
                    or "confirmation" in html or "success" in html):
                shot = screenshot_step(page, broker, "after_submit") or shot
                log_step(broker, "submitted")
                return shot
            screenshot_step(page, broker, "error")
            raise RuntimeError(broker + ": submitted but no confirmation seen")
        except Exception:
            try:
                screenshot_step(page, broker, "error")
            except Exception:
                pass
            raise
