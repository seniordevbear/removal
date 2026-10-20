from DrissionPage import ChromiumPage, ChromiumOptions
from time import sleep
import json
import random
import logging
import os, datetime, pyautogui, requests
from lib.common import generate_email, generate_phone_number
from lib.email_verification import do_email_verification
from cloudsolver.extension import proxies
from twocaptcha import TwoCaptcha
from lib.broker_helpers import (fill_field, submission_verdict, missing_pii, log_step,
                                unique_shot_path, _state_full_name)
from lib.broker_helpers import unique_shot_path

now = datetime.datetime.now()
current_date = now.strftime("%Y-%m-%d")
base_dir = os.getcwd()

screentShotDir = os.path.join(base_dir, "ScreenShot", current_date)
os.makedirs(screentShotDir, exist_ok=True)
usaStateDictionary = { 'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR', 'California': 'CA', 'Colorado': 'CO', 'Connecticut': 'CT', 'Delaware': 'DE', 'District of Columbia': 'DC', 'Florida': 'FL', 'Georgia': 'GA', 'Hawaii': 'HI', 'Idaho': 'ID', 'Illinois': 'IL', 'Indiana': 'IN', 'Iowa': 'IA', 'Kansas': 'KS', 'Kentucky': 'KY', 'Louisiana': 'LA', 'Maine': 'ME', 'Maryland': 'MD', 'Massachusetts': 'MA', 'Michigan': 'MI', 'Minnesota': 'MN', 'Mississippi': 'MS', 'Missouri': 'MO', 'Montana': 'MT', 'Nebraska': 'NE', 'Nevada': 'NV', 'New Hampshire': 'NH', 'New Jersey': 'NJ', 'New Mexico': 'NM', 'New York': 'NY', 'North Carolina': 'NC', 'North Dakota': 'ND', 'Ohio': 'OH', 'Oklahoma': 'OK', 'Oregon': 'OR', 'Pennsylvania': 'PA', 'Rhode Island': 'RI', 'South Carolina': 'SC', 'South Dakota': 'SD', 'Tennessee': 'TN', 'Texas': 'TX', 'Utah': 'UT', 'Vermont': 'VT', 'Virginia': 'VA', 'Washington': 'WA', 'West Virginia': 'WV', 'Wisconsin': 'WI', 'Wyoming': 'WY' }

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

# 2026-10-20: rebuilt from the round-10 capture. /privacyform/ now serves a
# people-search funnel; the data-subject request form is TrustArc's IRM page,
# linked from members.idstrong.com/opt-out. Fields carry GUID ids, the two
# dropdowns are react-select comboboxes (type, then click the option), there
# is a confirmation checkbox, a hidden honeypot named irm_<timestamp> that
# must stay empty, and reCAPTCHA v3 (api.js?render=6LdSn6gU...). 6 "No
# element found." failures a day against the old OneTrust ids.
TRUSTARC_URL = ("https://submit-irm.trustarc.com/services/validation/"
                "8bec428f-079d-421f-8b6b-3ede6c5d5930/?brandId=beaae2c1-19bc-4369-9a5c-21ce0c61625c")
F_NAME  = "00000000-0000-0000-0000-000000001002"
F_EMAIL = "00000000-0000-0000-0000-000000001003"
F_STATE = "00000000-0000-0000-0000-000000001004"   # "Resident of *"
F_TYPE  = "00000000-0000-0000-0000-000000001005"   # "Type of Request *"
F_DETAILS = "3551d89e-af3d-4b23-b9f2-1ee64b32e5c4"
SUBMIT_ID = "8bec428f-079d-421f-8b6b-3ede6c5d5930-submit"
RECAPTCHA_V3_KEY = "6LdSn6gUAAAAAKZ5SiEQ8PdCUOgV9sf1ei4utXrB"


def _pick_combobox(page, input_id, candidates, broker):
    """react-select: type into the combobox input, then click the option
    whose text contains the candidate. Tries each candidate in turn."""
    inp = page.ele("css:input#" + input_id, timeout=8)
    if not inp:
        raise RuntimeError("%s: combobox %s not on the form" % (broker, input_id[-4:]))
    tried = []
    for cand in [c for c in candidates if c]:
        tried.append(cand)
        try:
            inp.click(); sleep(0.3); inp.clear(); inp.input(cand); sleep(1.0)
        except Exception:
            pass
        low = cand.lower()
        opt = page.ele("xpath://div[contains(@class,'select__option') and contains(translate(.,"
                       "'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), %r)]" % low, timeout=3)
        if opt:
            opt.click(); sleep(0.5)
            return cand
    raise RuntimeError("%s: no option matched for %s; tried %r" % (broker, input_id[-4:], tried))


def fill_input_data(page, dataRow):
    broker = "idstrongcom"
    state_raw = (dataRow.get("State") or "").strip()
    if not state_raw:
        raise missing_pii("State")
    fill_field(page, "css:input#" + F_NAME, dataRow["Name"], broker=broker)
    fill_field(page, "css:input#" + F_EMAIL, generate_email(dataRow["Name"]), broker=broker)
    _pick_combobox(page, F_STATE, [_state_full_name(state_raw), state_raw], broker)
    try:
        chosen = _pick_combobox(page, F_TYPE, ["delete", "deletion", "erase", "opt out", "do not sell"], broker)
        log_step(broker, "request type: %s" % chosen)
    except Exception as e:
        log_step(broker, "request type not chosen (%s); submitting without it" % e, logging.WARNING)
    details = ("Please delete all records about me and stop selling or sharing my personal "
               "information (CCPA/CPRA Sec. 1798.105/1798.120). Name: %s. State: %s. "
               "Submitted by PrivacyDuck as the consumer's authorized agent." % (dataRow["Name"], state_raw))
    fill_field(page, "css:textarea#" + F_DETAILS, details, required=False, broker=broker)
    box = page.ele("css:input[type=checkbox][id^='00000000-0000-0000-0000-000000001007']", timeout=4)
    if box:
        try:
            if not box.states.is_checked:
                box.click()
        except Exception:
            box.click()
    else:
        log_step(broker, "confirmation checkbox not found", logging.WARNING)
    # honeypot irm_<timestamp>: never touched.


def idstrongcom(dataRow, website_name, in_user_email, run_mode):
    page = None
    try:
        fName = dataRow["Name"].split()[0]
        lName = dataRow["Name"].split()[-1]
        screenshot_save_path = unique_shot_path(screentShotDir, "IdstrongCom", fName, lName)
        arguments = ["-no-first-run", "--start-maximized", "-disable-gpu", "-disable-sensors"]
        options = get_chromium_options(arguments).auto_port()
        if run_mode == "headless":
            options.headless()
        page = ChromiumPage(addr_or_opts=options)
        page.get(TRUSTARC_URL)
        sleep(random.uniform(3, 5))
        fill_input_data(page, dataRow)

        # reCAPTCHA v3: the page executes it on submit; a solved token is set
        # on the hidden textarea as well, so either path has a token.
        try:
            solver = TwoCaptcha(os.getenv("TWOCAPTCHA_API_KEY", ""))
            result = solver.recaptcha(sitekey=RECAPTCHA_V3_KEY, url=TRUSTARC_URL,
                                      version="v3", action="submit", score=0.3)
            page.run_js("var t=arguments[0];document.querySelectorAll(\"textarea[name='g-recaptcha-response']\")"
                        ".forEach(function(e){e.value=t;});", result["code"])
        except Exception as e:
            log_step("idstrongcom", "v3 token not obtained (%s); relying on the page's own execute" % e,
                     logging.WARNING)

        btn = page.ele("css:button#" + SUBMIT_ID, timeout=8)
        if not btn:
            raise RuntimeError("idstrongcom: submit button not found")
        btn.click()
        submission_verdict(page, "idstrongcom", success_phrases=(
            "thank you", "received", "submitted", "has been sent"), timeout=20)
        sleep(2)
        page.get_screenshot(screenshot_save_path)
    except Exception:
        try:
            if page is not None:
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
