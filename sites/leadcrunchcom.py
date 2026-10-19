from DrissionPage import ChromiumPage, ChromiumOptions
from time import sleep
import json
import random
import logging
import os, datetime, pyautogui, requests
from lib.common import generate_email, generate_phone_number
from lib.broker_helpers import (unique_shot_path, fill_field, click_label_text,
                                submission_verdict, missing_pii, log_step)

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

def fill_input_data(page, dataRow):
    """Fill the GetRev privacy-request form.

    Rebuilt from the 2026-10-19 capture. The form was rewritten as a React
    app and every selector the script used had gone: the name fields are
    camelCase (firstName / lastName, not first_name), country and state are
    text inputs rather than selects, the e-mail field is split into
    workEmail / otherEmail, the address fields are textareas, the consent
    label text changed, and Submit is a <button>Submit Request</button>
    rather than <input type=submit value=Submit>. 78 "No element found."
    failures between 17 and 19 Oct.

    privacyRequestHoneypot is a trap field - it must be left empty.
    """
    fName = dataRow["Name"].split()[0]
    lName = dataRow["Name"].split()[-1]
    broker = "leadcrunchcom"
    state_raw = (dataRow.get("State") or "").strip()
    if not state_raw:
        raise missing_pii("State")

    fill_field(page, "css:input[name='firstName']", fName, broker=broker)
    fill_field(page, "css:input[name='lastName']", lName, broker=broker)
    fill_field(page, "css:input[name='country']", "United States", broker=broker)
    fill_field(page, "css:input[name='state']", state_raw, broker=broker)
    fill_field(page, "css:input[name='otherEmail']",
               generate_email(dataRow["Name"]), broker=broker)

    phone = generate_phone_number()
    for sel in ("css:input[name='phone']",):
        try:
            fill_field(page, sel, phone, required=False, broker=broker)
        except Exception:
            pass

    addr = ", ".join(x for x in (str(dataRow.get("Address") or "").strip(),
                                 str(dataRow.get("City") or "").strip(),
                                 state_raw,
                                 str(dataRow.get("Zipcode") or "").strip()) if x)
    if addr:
        try:
            fill_field(page, "css:textarea[name='otherAddress']", addr,
                       required=False, broker=broker)
        except Exception:
            pass

    # The request-type and consent boxes are React-controlled and carry no
    # name or value, so the label text is the only handle.
    for text in ("Deletion", "I certify that the information provided is accurate"):
        try:
            click_label_text(page, text, timeout=6)
        except Exception as e:
            log_step(broker, "could not tick %r: %s" % (text[:40], e), logging.WARNING)

    btn = page.ele("xpath://button[contains(normalize-space(.), 'Submit Request')]", timeout=8)
    if not btn:
        raise RuntimeError("leadcrunchcom: no 'Submit Request' button on the form")
    btn.click()


def leadcrunchcom(dataRow, website_name, in_user_email, run_mode) : 
    page = None
    try : 
        fName = dataRow["Name"].split()[0] # split string based on space to get first name
        lName = dataRow["Name"].split()[-1]# split string based on space to get last name
        screenshot_save_path = unique_shot_path(screentShotDir, "LeadcrunchCom", fName, lName)
        
        sucessConfirmationApi = f"https://privacypros.com/web/dashboard/appendapi.php?website={website_name}&status=1&api=true&email={in_user_email}"
        errorConfirmationApi = f"https://privacypros.com/web/dashboard/appendapi.php?website={website_name}&status=2&api=true&email={in_user_email}"

        arguments = [
            "-no-first-run",
            "--start-maximized",
            # "--incognito",
            "-disable-javascript",
            "-disable-gpu",
            "-disable-sensors",
        ]

        options = get_chromium_options(arguments).auto_port()
        if run_mode == "headless" :
            options.headless()
        #Launch Website
        page = ChromiumPage(addr_or_opts=options)
        page.get("https://getrev.ai/privacy-request/")

        sleep(random.uniform(1, 2))

        fill_input_data(page, dataRow)

        
        try :
            # response = requests.get(sucessConfirmationApi, timeout=10)
            print("Success Confirmation API is sent successfully!")
            sleep(5)
            page.get_screenshot(screenshot_save_path)
        except Exception as e:
            print("Success Confirmation API is failed: ", str(e))
        
    except Exception as e:
        try :
            # response = requests.get(errorConfirmationApi, timeout=10)
            print("Error Confirmation API is sent successfully!")
            sleep(5)
            page.get_screenshot(screenshot_save_path)
        except Exception as e:
            print("Error Confirmation API is failed: ", str(e))
        raise

    finally:
        if page is not None:
            try:
                page.quit()
            except Exception:
                pass

    return screenshot_save_path