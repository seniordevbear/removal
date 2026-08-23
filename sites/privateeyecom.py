from lib.broker_helpers import (
    safe_chromium_for_broker, find_input, screenshot_step, log_step,
    _state_full_name,
)
from lib.captcha import get_solver
from time import sleep
import json as _json


# Rewritten 2026-08-23 from the live form (user-supplied HTML). PrivateEye's
# opt-out is GoDaddy's OneTrust DSAR portal (Angular): first a subject-type
# chooser rendered as custom divs (role=option, aria-label "Customer"/
# "Other"), which then reveals the actual fields using OneTrust's standard
# <name>DSARElement ids. reCAPTCHA v2 with OneTrust's shared sitekey; the
# Submit button stays disabled until Angular counts the form valid, so every
# value is entered with real key events.
def privateeyecom(dataRow, website_name, in_user_email, run_mode):
    broker = "privateeyecom"
    name_full = (dataRow.get("Name") or "").strip()
    parts = name_full.split()
    first = parts[0] if parts else ""
    last = parts[-1] if len(parts) > 1 else ""
    email = dataRow.get("User Email") or in_user_email
    if not (first and last and email):
        raise RuntimeError(broker + ": requires name and email")

    with safe_chromium_for_broker(broker,
                                  headless=(run_mode == "headless")) as page:
        try:
            log_step(broker, "GET https://www.godaddy.com/legal/agreements/do-not-share")
            page.get("https://www.godaddy.com/legal/agreements/do-not-share")
            sleep(4)

            # the DSAR webform may itself sit in an iframe on the godaddy page
            scope = page
            fr = page.ele("css:iframe[src*='privacyportal.onetrust.com']",
                          timeout=5)
            if fr:
                scope = page.get_frame(fr)
                sleep(1)

            # subject type: "Other" fits a data-subject who is not a GoDaddy
            # customer; fall back to "Customer" if the option set changed.
            opt = None
            for label in ("Other", "Customer"):
                opt = scope.ele("css:div[role=option][aria-label='%s']" % label,
                                timeout=4)
                if opt:
                    break
            if not opt:
                raise RuntimeError(broker + ": subject-type options not found")
            try:
                opt.click()
            except Exception:
                opt.click(by_js=True)
            sleep(2)  # Angular reveals the real fields

            def fill(frag, value, required=False):
                if not value:
                    return
                el = None
                for sel in ("css:input[id*='%s' i][id$='DSARElement']" % frag,
                            "css:input[id*='%s' i]" % frag):
                    el = scope.ele(sel, timeout=4)
                    if el:
                        break
                if not el:
                    if required:
                        raise RuntimeError(broker + ": field not found: " + frag)
                    log_step(broker, frag + " field absent, skipped")
                    return
                el.click()
                el.input(value)
                sleep(0.3)

            fill("firstName", first, required=True)
            fill("lastName", last, required=True)
            fill("email", email, required=True)
            fill("phone", (dataRow.get("Phone Number") or "").strip())
            fill("address", (dataRow.get("Address") or "").strip())
            fill("city", (dataRow.get("City") or "").strip())
            fill("zip", (dataRow.get("Zipcode") or "").strip())
            fill("postal", (dataRow.get("Zipcode") or "").strip())

            # state, if the revealed form has OneTrust's dropdown
            st = scope.ele("css:input[id*='state' i][id$='DSARElement']",
                           timeout=3)
            if st:
                try:
                    st.click()
                    sleep(0.5)
                    raw = (dataRow.get("State") or "").strip()
                    for cand in (_state_full_name(raw), raw, raw.upper()):
                        o = scope.ele(
                            "tag:vt-option@@aria-label=" + cand, timeout=2)
                        if o:
                            o.click()
                            break
                except Exception as e:
                    log_step(broker, "state select skipped: " + str(e))

            # request-type toggles, if present after reveal: prefer deletion
            for needle in ("delete", "do not sell", "do-not-sell", "opt out"):
                t = scope.ele(
                    "css:div[role=option][aria-label*='%s' i]" % needle,
                    timeout=2)
                if t:
                    try:
                        t.click()
                    except Exception:
                        t.click(by_js=True)
                    sleep(0.4)
                    break

            frame = scope.ele("css:iframe[src*='recaptcha']", timeout=8)
            import re as _re
            m = _re.search(r"[?&]k=([\w-]+)", frame.attr("src") or "")
            if not m:
                raise RuntimeError(broker + ": recaptcha sitekey not found")
            log_step(broker, "solving recaptcha " + m.group(1))
            token = get_solver().recaptcha(sitekey=m.group(1), url=page.url)["code"]
            scope.run_js(
                "var t=document.getElementById('g-recaptcha-response');"
                "if(t){t.value=" + _json.dumps(token) + ";}"
                "if(window.grecaptcha){window.grecaptcha.getResponse="
                "function(){return " + _json.dumps(token) + ";};}")
            sleep(1)

            shot = screenshot_step(page, broker, "before_submit")
            btn = scope.ele("css:#dsar-webform-submit-button", timeout=6)
            if not btn:
                raise RuntimeError(broker + ": submit button not found")
            if (btn.attr("disabled") or "").lower() in ("true", "disabled", ""):
                # still disabled -> a required field Angular wants is missing;
                # try a JS click anyway, then verify below via screenshot
                log_step(broker, "submit still disabled — attempting js click")
            try:
                btn.click()
            except Exception:
                btn.click(by_js=True)
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
