from DrissionPage import ChromiumPage, ChromiumOptions
from time import sleep
import json
import random
import logging
import os, datetime, pyautogui, requests
from lib.common import generate_email, generate_phone_number
from twocaptcha import TwoCaptcha
from lib.broker_helpers import (unique_shot_path, fill_field, submission_verdict, missing_pii, log_step,
                                select_onetrust_autocomplete, select_onetrust_state, select_onetrust_country)

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

# 2026-10-20: rebuilt from the round-10 capture. The GoDaddy legal page the
# script used to drive now embeds a OneTrust webform; its own URL was in the
# page. The form is two-step: "I am a (an)" Customer / Other first, then the
# standard OneTrust *DSARElement fields and a request-type chooser, then
# dsar-webform-submit-button (present in the capture). 5 failures a day.
ONETRUST_URL = ("https://privacyportal.onetrust.com/webform/9c7cf400-5967-40b4-9f91-7df7b5eff86b/"
                "e5068a23-1539-4b4a-978a-8d5320ab0de7")


def _click_request_type(page, broker):
    for needle in ("delete", "deletion", "do not sell", "do not share", "opt out"):
        el = page.ele("xpath://span[contains(translate(normalize-space(.),"
                      "'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), %r)]" % needle, timeout=2)
        if el:
            el.click(); sleep(0.5)
            log_step(broker, "request type: %r" % needle)
            return True
    log_step(broker, "no request-type option matched; continuing", logging.WARNING)
    return False


def fill_input_data(page, dataRow):
    broker = "datastreamgroupcom"
    fName = dataRow["Name"].split()[0]
    lName = dataRow["Name"].split()[-1]
    state_raw = (dataRow.get("State") or "").strip()
    if not state_raw:
        raise missing_pii("State")

    # step 1: who is asking
    select_onetrust_autocomplete(page, "subjectTypesDSARElement", ["Other", "Customer"])
    sleep(2)

    # step 2: the standard OneTrust fields (ids shared with costar's form)
    fill_field(page, "css:input#firstNameDSARElement", fName, broker=broker, timeout=20)
    fill_field(page, "css:input#lastNameDSARElement", lName, broker=broker)
    fill_field(page, "css:input#emailDSARElement", generate_email(dataRow["Name"]), broker=broker)
    if page.ele("css:input#countryDSARElement", timeout=2):
        try:
            select_onetrust_country(page, "United States")
        except Exception as e:
            log_step(broker, "country not set: %s" % e, logging.WARNING)
    if page.ele("css:input#stateDSARElement", timeout=2):
        try:
            select_onetrust_state(page, state_raw)
        except Exception as e:
            log_step(broker, "state not set: %s" % e, logging.WARNING)
    _click_request_type(page, broker)


def datastreamgroupcom(dataRow, website_name, in_user_email, run_mode):
    page = None
    try:
        fName = dataRow["Name"].split()[0]
        lName = dataRow["Name"].split()[-1]
        screenshot_save_path = unique_shot_path(screentShotDir, "DatastreamgroupCom", fName, lName)
        arguments = ["-no-first-run", "--start-maximized", "-disable-gpu", "-disable-sensors"]
        options = get_chromium_options(arguments).auto_port()
        if run_mode == "headless":
            options.headless()
        page = ChromiumPage(addr_or_opts=options)
        page.get(ONETRUST_URL)
        sleep(random.uniform(4, 6))
        fill_input_data(page, dataRow)

        # OneTrust shows a reCAPTCHA v2 widget on some forms; solve it only if present.
        rc = page.ele("css:.g-recaptcha[data-sitekey]", timeout=3)
        if rc:
            try:
                solver = TwoCaptcha(os.getenv("TWOCAPTCHA_API_KEY", ""))
                token = solver.recaptcha(sitekey=rc.attr("data-sitekey"), url=ONETRUST_URL)["code"]
                page.run_js("var t=arguments[0];document.querySelectorAll(\"textarea[name='g-recaptcha-response']\")"
                            ".forEach(function(e){e.style.display='block';e.value=t;});", token)
            except Exception as e:
                raise RuntimeError("datastreamgroupcom: captcha not solved: %s" % e)

        btn = page.ele("css:button#dsar-webform-submit-button", timeout=8)
        if not btn:
            raise RuntimeError("datastreamgroupcom: dsar-webform-submit-button not found")
        btn.click()
        submission_verdict(page, "datastreamgroupcom", success_phrases=(
            "thank you", "received", "submitted", "request has been"), timeout=20)
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
