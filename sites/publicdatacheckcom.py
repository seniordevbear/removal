from lib.broker_helpers import (
    safe_chromium_for_broker, find_input, screenshot_step, log_step,
    _state_full_name, state_abbrev,
)
from lib.common import generate_email
from lib.captcha import get_solver
from time import sleep
import json as _json
import logging


# Rewritten 2026-08-27 from the live form. publicdatacheck's privacy form:
# requestType(select delete), firstName, LAST NAME (obfuscated rotating id
# like O62d0e90506e92ad4 -> located by its "Last Name" label, not hardcoded),
# city, States(select), zip, age(select, required), Confirmation Email, and a
# Cloudflare Turnstile. Confirmation email is sent to the address we give, so
# we use the monitored @privacyprosremoval.com inbox (main.py auto-confirms).
def publicdatacheckcom(dataRow, website_name, in_user_email, run_mode):
    broker = "publicdatacheckcom"
    name_full = (dataRow.get("Name") or "").strip()
    parts = name_full.split()
    first = parts[0] if parts else ""
    last = parts[-1] if len(parts) > 1 else ""
    if not first or not last:
        raise RuntimeError(broker + ": requires first and last name")
    city = (dataRow.get("City") or "").strip()
    zipc = (dataRow.get("Zipcode") or "").strip()
    age = str(dataRow.get("Age") or "").strip()

    with safe_chromium_for_broker(broker,
                                  headless=(run_mode == "headless")) as page:
        try:
            log_step(broker, "GET https://www.publicdatacheck.com/help-center/privacy-requests")
            page.get("https://www.publicdatacheck.com/help-center/privacy-requests")
            sleep(3)

            try:
                page.ele("css:#requestType", timeout=8).select.by_value("delete")
            except Exception:
                log_step(broker, "requestType select failed", logging.WARNING)
            sleep(0.3)

            find_input(page, "css:#firstName", timeout=6).input(first)
            sleep(0.2)

            # Last-name field id rotates; find the input under the "Last Name"
            # label instead of trusting a fixed id.
            ln = None
            try:
                lbl = page.ele("xpath://label[contains(., 'Last Name')]", timeout=4)
                fid = lbl.attr("for") if lbl else None
                if fid:
                    ln = page.ele("css:#" + fid, timeout=3)
            except Exception:
                ln = None
            if not ln:
                ln = page.ele(
                    "xpath://label[contains(.,'Last Name')]/following::input[1]",
                    timeout=4)
            if not ln:
                raise RuntimeError(broker + ": last-name field not found")
            ln.input(last); sleep(0.2)

            if city:
                find_input(page, "css:#city").input(city); sleep(0.2)
            if zipc:
                find_input(page, "css:#zip").input(zipc); sleep(0.2)

            # State select: try full name then 2-letter code.
            try:
                sel = page.ele("css:select[name=States]", timeout=4)
                for cand in (_state_full_name(dataRow.get("State") or ""),
                             state_abbrev(dataRow.get("State") or "")
                             if (dataRow.get("State") or "").strip() else ""):
                    if not cand:
                        continue
                    try:
                        sel.select.by_text(cand); break
                    except Exception:
                        try:
                            sel.select.by_value(cand); break
                        except Exception:
                            pass
            except Exception as e:
                log_step(broker, "state select skipped: " + str(e), logging.WARNING)
            sleep(0.2)

            # Age is required; select it if we have it, else leave for the
            # form to reject (recorded, bounded) rather than fabricate one.
            if age:
                try:
                    page.ele("css:select[name=age]", timeout=3).select.by_value(age)
                except Exception:
                    try:
                        page.ele("css:select[name=age]").select.by_text(age)
                    except Exception:
                        log_step(broker, "age option not matched: " + age,
                                 logging.WARNING)
            sleep(0.2)

            find_input(page, "css:#email").input(generate_email(name_full))
            sleep(0.3)

            # Cloudflare Turnstile
            try:
                ts = page.ele("css:.cf-turnstile[data-sitekey]", timeout=6)
                sitekey = ts.attr("data-sitekey")
                log_step(broker, "solving turnstile " + str(sitekey))
                token = get_solver().turnstile(sitekey=sitekey, url=page.url)["code"]
                page.run_js(
                    "var i=document.querySelector('input[name=\"cf-turnstile-response\"]');"
                    "if(!i){i=document.createElement('input');i.type='hidden';"
                    "i.name='cf-turnstile-response';document.forms[0].appendChild(i);}"
                    "i.value=" + _json.dumps(token) + ";")
            except Exception as e:
                log_step(broker, "turnstile step: " + str(e), logging.WARNING)

            shot = screenshot_step(page, broker, "before_submit")
            find_input(page, "css:#submit-button", "css:button[type=submit]",
                       timeout=6).click()
            sleep(6)
            shot = screenshot_step(page, broker, "after_submit") or shot
            log_step(broker, "submitted")
            return shot
        except Exception:
            try:
                screenshot_step(page, broker, "error")
            except Exception:
                pass
            raise
