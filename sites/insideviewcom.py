from lib.broker_helpers import (
    safe_chromium_for_broker, find_input, screenshot_step, log_step,
    _state_full_name,
)
from lib.common import generate_email
from time import sleep
import logging


# Rewritten 2026-08-25 from the live form (user-supplied HTML). InsideView is
# now Demandbase; the opt-out is a Ketch privacy-center SPA. The deletion form
# is revealed after choosing the "Data Deletion" request type, then exposes
# stable ids: #text-field-firstName/-lastName/-email, #select-field-country
# (2-letter values), #text-field-stateRegion (free text), #select-field-typeCode
# ("customer"). Invisible reCAPTCHA guards submit, so this is best-effort — a
# failed run leaves an error screenshot for the next iteration.
def insideviewcom(dataRow, website_name, in_user_email, run_mode):
    broker = "insideviewcom"
    name_full = (dataRow.get("Name") or "").strip()
    parts = name_full.split()
    first = parts[0] if parts else ""
    last = parts[-1] if len(parts) > 1 else ""
    if not first or not last:
        raise RuntimeError(broker + ": form requires first and last name")
    state = _state_full_name(dataRow.get("State") or "") or (dataRow.get("State") or "")

    url = ("https://www.demandbase.com/privacy-center.html"
           "?ketch_preferences_tab=rightsTab")
    with safe_chromium_for_broker(broker,
                                  headless=(run_mode == "headless")) as page:
        try:
            log_step(broker, "GET " + url)
            page.get(url)
            sleep(5)  # Ketch SPA boot

            # Reveal the request form by choosing a deletion-type option.
            # The chooser markup isn't fixed, so try a few text-based handles.
            for sel in ("xpath://*[contains(translate(., 'DELETE', 'delete'),"
                        " 'delete')][not(self::script)]",
                        "xpath://*[contains(., 'Data Deletion')]",
                        "css:[data-role='right-tile']"):
                try:
                    el = page.ele(sel, timeout=4)
                    if el:
                        try:
                            el.click()
                        except Exception:
                            el.click(by_js=True)
                        sleep(2)
                        break
                except Exception:
                    pass

            # The form fields have stable ids once the form is shown.
            fn = find_input(page, "css:#text-field-firstName", timeout=10.0)
            fn.click(); fn.input(first); sleep(0.2)
            find_input(page, "css:#text-field-lastName").input(last); sleep(0.2)
            find_input(page, "css:#text-field-email").input(
                generate_email(name_full)); sleep(0.2)

            try:
                page.ele("css:#select-field-country", timeout=4).select.by_value("US")
            except Exception:
                log_step(broker, "country select skipped", logging.WARNING)
            sleep(0.2)

            try:
                find_input(page, "css:#text-field-stateRegion").input(state)
            except Exception:
                pass
            sleep(0.2)

            try:
                page.ele("css:#select-field-typeCode", timeout=4).select.by_value("customer")
            except Exception:
                log_step(broker, "typeCode select skipped", logging.WARNING)
            sleep(0.3)

            shot = screenshot_step(page, broker, "before_submit")

            btn = find_input(page, "css:#right-invocation-form button[type=submit]",
                             "css:button[type=submit]", timeout=6.0)
            try:
                btn.click()
            except Exception:
                btn.click(by_js=True)
            sleep(6)

            # Confirmation copy or a thank-you replaces the form on success.
            html = (page.html or "").lower()
            if ("thank" in html or "received" in html or "confirmation" in html
                    or "check your email" in html):
                shot = screenshot_step(page, broker, "after_submit") or shot
                log_step(broker, "submitted")
                return shot
            # No clear confirmation — likely the invisible reCAPTCHA blocked it.
            screenshot_step(page, broker, "error")
            raise RuntimeError(
                broker + ": submitted but no confirmation seen "
                "(invisible reCAPTCHA may have blocked it)")
        except Exception:
            try:
                screenshot_step(page, broker, "error")
            except Exception:
                pass
            raise
