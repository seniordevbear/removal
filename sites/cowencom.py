from DrissionPage import ChromiumPage, ChromiumOptions
from time import sleep
import json
import re
import random
import logging
import os, datetime, pyautogui, requests
from lib.common import generate_email, generate_phone_number
from lib.broker_helpers import (unique_shot_path, fill_field, submission_verdict,
                                missing_pii, log_step)

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

# 2026-10-20: rebuilt from the round-11 capture. Cowen is Forian now, and
# /privacy-do-not-sell-share/ redirects to the homepage; the consumer request
# form lives at /privacy-consumer-requests/ (linked from the footer). It is a
# Divi contact form - every field name is et_pb_contact_*_0 - with two
# required selects whose option values are spelled out in full, and Divi's own
# arithmetic captcha, whose two operands are published on the input as
# data-first_digit / data-second_digit. No solver needed: read them and add.
FORM_URL = "https://forian.com/privacy-consumer-requests/"
REQUEST_TYPE = "Request to Delete Personal Information Obtained about You"
WHO = "Consumer"


def _answer_divi_captcha(page, broker):
    """Divi publishes the sum's operands as attributes on the answer box."""
    box = page.ele("css:input[name='et_pb_contact_captcha_0']", timeout=8)
    if not box:
        raise RuntimeError("cowencom: captcha box not on the form")
    a, b = box.attr("data-first_digit"), box.attr("data-second_digit")
    if not (a and b):
        q = page.ele("css:.et_pb_contact_captcha_question", timeout=3)
        nums = re.findall(r"\d+", (q.text if q else "") or "")
        if len(nums) < 2:
            raise RuntimeError("cowencom: could not read the captcha operands")
        a, b = nums[0], nums[1]
    total = str(int(a) + int(b))
    box.click(); box.clear(); box.input(total)
    log_step(broker, "captcha %s + %s = %s" % (a, b, total))


def fill_input_data(page, dataRow):
    broker = "cowencom"
    addr = ", ".join(x for x in (str(dataRow.get("Address") or "").strip(),
                                 str(dataRow.get("City") or "").strip(),
                                 str(dataRow.get("State") or "").strip(),
                                 str(dataRow.get("Zipcode") or "").strip()) if x)
    if not addr:
        raise missing_pii("Address", "City", "State", "Zipcode")

    for name, value in (("et_pb_contact_request_type_0", REQUEST_TYPE),
                        ("et_pb_contact_who_request_0", WHO)):
        sel = page.ele("css:select[name='%s']" % name, timeout=10)
        if not sel:
            raise RuntimeError("cowencom: select %s not on the form" % name)
        sel.select.by_value(value)
        sleep(0.3)

    fill_field(page, "css:input[name='et_pb_contact_name_0']", dataRow["Name"], broker=broker)
    fill_field(page, "css:input[name='et_pb_contact_email_0']",
               generate_email(dataRow["Name"]), broker=broker)
    fill_field(page, "css:input[name='et_pb_contact_address_0']", addr, broker=broker)
    fill_field(page, "css:textarea[name='et_pb_contact_message_0']",
               "Please delete all personal information you hold about me and stop selling "
               "or sharing it. Submitted by PrivacyDuck as the consumer's authorized agent.",
               required=False, broker=broker)
    _answer_divi_captcha(page, broker)


def cowencom(dataRow, website_name, in_user_email, run_mode):
    page = None
    screenshot_save_path = None
    try:
        fName = dataRow["Name"].split()[0]
        lName = dataRow["Name"].split()[-1]
        screenshot_save_path = unique_shot_path(screentShotDir, "CowenCom", fName, lName)
        arguments = ["-no-first-run", "--start-maximized", "-disable-gpu", "-disable-sensors"]
        options = get_chromium_options(arguments).auto_port()
        if run_mode == "headless":
            options.headless()
        page = ChromiumPage(addr_or_opts=options)
        page.get(FORM_URL)
        sleep(random.uniform(3, 5))
        fill_input_data(page, dataRow)

        # The page also carries CleanTalk's hidden anti-spam fields; they are
        # filled by its own JS in a real browser, so nothing to do here.
        btn = page.ele("css:button[name='et_builder_submit_button']", timeout=8)
        if not btn:
            raise RuntimeError("cowencom: submit button not found")
        btn.click()
        submission_verdict(page, "cowencom", success_phrases=(
            "thank you", "your request", "received", "submitted"), timeout=20)
        sleep(2)
        page.get_screenshot(screenshot_save_path)
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
