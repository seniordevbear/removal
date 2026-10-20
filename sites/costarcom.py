from DrissionPage import ChromiumPage, ChromiumOptions
from time import sleep
import json
import random
import logging
import os, datetime, pyautogui, requests, sys
from lib.common import generate_email, generate_phone_number
from twocaptcha import TwoCaptcha
from lib.email_verification import do_email_verification
from cloudsolver.extension import proxies
from lib.broker_helpers import (unique_shot_path, fill_field, submission_verdict,
                                missing_pii, log_step, state_abbrev)
from lib.broker_helpers import unique_shot_path

api_key = os.getenv("TWOCAPTCHA_API_KEY", "")
solver = TwoCaptcha(api_key)

now = datetime.datetime.now()
current_date = now.strftime("%Y-%m-%d")
base_dir = os.getcwd()

screentShotDir = os.path.join(base_dir, "ScreenShot", current_date)
os.makedirs(screentShotDir, exist_ok=True)

def get_chromium_options(arguments: list) -> ChromiumOptions:
    """
    Configures and returns Chromium options.
    
    :param browser_path: Path to the Chromium browser executable.
    :param arguments: List of arguments for the Chromium browser.
    :return: Configured ChromiumOptions instance.
    """
    options = ChromiumOptions()
    # options.no_imgs(True)
    # options.no_imgs(True).mute(True).no_js(True)
    # options.set_argument('--auto-open-devtools-for-tabs', 'true') # we don't need this anymore
    for argument in arguments:
        options.set_argument(argument)
    return options

def _human_type2(element , text: str) -> None:
    """
    Types in a way reminiscent of a human, with a random delay in between 50ms to 100ms for every character
    :param element: Input element to type text to
    :param text: Input to be typed
    """

    for c in text:
        element.input(c)

        sleep(random.uniform(0.05, 0.1))

def make_standard_num(num) :
    ret = str(num)
    if len(ret) < 2 : ret = "0" + ret

    return ret

# 2026-10-20: rebuilt from the round-12 capture. The OneTrust webform the
# script used returns 135 bytes and is dead; CoStar replaced it with its own
# portal at privacy.costar.com/DSAR-submission/, which is e-mail-verification
# gated: you submit an address, CoStar e-mails a link, and only the page
# behind that link carries the request form. So the flow mirrors
# contactoutcom - fill the gate, then let do_email_verification open the link
# and fill the real form in the tab it hands back.
#
# From the capture's own getRequestTypes(): country is a 3-letter code
# ("USA"), state is the 2-letter code, and the opt-out radio only exists for
# CA CO CT VA UT TX MT OR DE IA IN TN - every other state gets Delete, which
# is the stronger request anyway. The gate has a honeypot named
# additionalValues labelled "Leave this field blank": never touched.
FORM_URL = "https://privacy.costar.com/DSAR-submission/"
OPT_OUT_STATES = {"CA", "CO", "CT", "VA", "UT", "TX", "MT", "OR", "DE", "IA", "IN", "TN"}


def _fill_request_form(tab, dataRow, email_str, shot_path):
    """Fill the form that appears behind the verification link."""
    broker = "costarcom"
    sleep(4)
    st = state_abbrev(dataRow["State"])          # raises missing_pii if not a US state

    for sid, value in (("brand", "CoStar"), ("country", "USA")):
        el = tab.ele("css:select#" + sid, timeout=15)
        if not el:
            raise RuntimeError("costarcom: select #%s not on the form" % sid)
        try:
            el.select.by_value(value)
        except Exception:
            el.select.by_text("CoStar" if sid == "brand" else "United States")
        sleep(0.8)

    el = tab.ele("css:select#state", timeout=10)
    if el:
        try:
            el.select.by_value(st)
        except Exception:
            el.select.by_text(dataRow["State"])
        sleep(1.2)

    el = tab.ele("css:select#relationship", timeout=10)
    if el:
        el.select.by_text("Customer")
        sleep(0.8)

    # Request-type radios are rendered by JS once country and state are set.
    wanted = "opt-out" if st in OPT_OUT_STATES else "delete"
    radio = tab.ele("css:input#request-%s" % wanted, timeout=10) or tab.ele("css:input#request-delete", timeout=5)
    if not radio:
        raise RuntimeError("costarcom: no request-type radio appeared for state %s" % st)
    radio.click()
    log_step(broker, "request type: %s" % wanted)
    sleep(0.5)

    fName = dataRow["Name"].split()[0]
    lName = dataRow["Name"].split()[-1]
    fill_field(tab, "css:input#first-name", fName, broker=broker)
    fill_field(tab, "css:input#last-name", lName, broker=broker)
    fill_field(tab, "css:input#email", email_str, broker=broker)
    fill_field(tab, "css:input#address", str(dataRow.get("Address") or ""), broker=broker)
    fill_field(tab, "css:input#city", str(dataRow.get("City") or ""), broker=broker)
    fill_field(tab, "css:input#zip-code", str(dataRow.get("Zipcode") or ""), broker=broker)
    fill_field(tab, "css:input#phone", generate_phone_number(), broker=broker)
    ps = tab.ele("css:select#personal-state", timeout=6)
    if ps:
        try:
            ps.select.by_value(st)
        except Exception:
            ps.select.by_text(dataRow["State"])
    fill_field(tab, "css:textarea#additional-details",
               "Please delete all personal information you hold about me and stop selling "
               "or sharing it. Submitted by PrivacyDuck as the consumer's authorized agent.",
               broker=broker)

    btn = tab.ele("xpath://button[@type='submit' or contains(normalize-space(.), 'Submit Privacy Request')]",
                  timeout=10)
    if not btn:
        raise RuntimeError("costarcom: Submit Privacy Request button not found")
    btn.click()
    submission_verdict(tab, broker, success_phrases=(
        "thank you", "received", "submitted", "your request"), timeout=25)
    sleep(2)
    try:
        tab.get_screenshot(shot_path)
    except Exception:
        pass


def costarcom(dataRow, website_name, in_user_email, run_mode):
    page = None
    screenshot_save_path = None
    try:
        fName = dataRow["Name"].split()[0]
        lName = dataRow["Name"].split()[-1]
        screenshot_save_path = unique_shot_path(screentShotDir, "CostarCom", fName, lName)
        for field in ("Address", "City", "State", "Zipcode"):
            if not str(dataRow.get(field) or "").strip():
                raise missing_pii(field)

        arguments = ["-no-first-run", "--start-maximized", "-disable-gpu", "-disable-sensors"]
        options = get_chromium_options(arguments).auto_port()
        if run_mode == "headless":
            options.headless()
        page = ChromiumPage(addr_or_opts=options)
        page.get(FORM_URL)
        sleep(random.uniform(3, 5))

        email_str = generate_email(dataRow["Name"])
        fill_field(page, "css:input#verification-email", email_str, broker="costarcom")
        btn = page.ele("css:button#send-link-button", timeout=10)
        if not btn:
            raise RuntimeError("costarcom: 'Send verification link' button not found")
        btn.click()
        sleep(4)
        page.get_screenshot(screenshot_save_path)

        from lib.email_verification import do_email_verification
        ok = do_email_verification(
            "costar", screenshot_save_path,
            after_click=lambda tab: _fill_request_form(tab, dataRow, email_str, screenshot_save_path),
            to_address=email_str, wait_seconds=180)
        if not ok:
            raise RuntimeError("costarcom: verification link sent to %s but no mail arrived" % email_str)
    except Exception:
        try:
            if page is not None and screenshot_save_path:
                page.get_screenshot(screenshot_save_path)
        except Exception:
            pass
        raise
    finally:
        if page is not None:
            try:
                page.quit()
            except Exception:
                pass
    return screenshot_save_path
