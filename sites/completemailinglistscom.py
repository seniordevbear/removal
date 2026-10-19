from DrissionPage import ChromiumPage, ChromiumOptions
from time import sleep
import json
import random
import os, datetime, pyautogui, requests
from lib.common import generate_email, generate_phone_number
from twocaptcha import TwoCaptcha
from lib.broker_helpers import (unique_shot_path, fill_field, find_input,
                                select_state, submission_verdict, missing_pii)

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

def _hs_form(page, timeout=20):
    """The HubSpot embed renders inside an iframe; return something to query.

    2026-10-19: /do-not-sell-my-information now 404s and the opt-out moved to
    /consumer-privacy-request, which embeds HubSpot form
    f997b925-9a37-4196-8d46-529376ceda52 (portal 3272390) instead of the old
    Drupal webform. Every edit-submitted-* id the script used is gone, which
    is where 112 "No element found." failures came from between 17 and 19 Oct.
    Same iframe pattern giantpartnerscom already uses.
    """
    from time import sleep
    for _ in range(int(timeout / 2)):
        for sel in ("tag:iframe@@id=hs-form-iframe-0",
                    "css:iframe.hs-form-iframe",
                    "css:iframe[id^='hs-form-iframe']"):
            try:
                fr = page.ele(sel, timeout=2)
            except Exception:
                fr = None
            if fr:
                return fr
        try:
            if page.ele("css:form.hs-form", timeout=1):
                return page          # some embeds render inline
        except Exception:
            pass
        sleep(2)
    raise RuntimeError("completemailinglistscom: the HubSpot form never rendered "
                       "(embed changed or blocked); needs a capture")


def fill_input_data(page, dataRow):
    fName = dataRow["Name"].split()[0]
    lName = dataRow["Name"].split()[-1]
    state_raw = (dataRow.get("State") or "").strip()
    if not state_raw:
        raise missing_pii("State")

    form = _hs_form(page)
    broker = "completemailinglistscom"

    # HubSpot names its standard contact properties the same way on every
    # portal, so these are the platform's names rather than a guess about
    # this site; fill_field verifies the value actually landed, so a wrong
    # one fails loudly instead of submitting a half-empty form.
    for names, value, required in (
        (("firstname", "first_name"), fName, True),
        (("lastname", "last_name"), lName, True),
        (("email",), generate_email(dataRow["Name"]), True),
        (("phone", "mobilephone"), generate_phone_number(), False),
        (("address", "street_address"), str(dataRow.get("Address") or ""), False),
        (("city",), str(dataRow.get("City") or ""), False),
        (("zip", "zipcode", "zip_code"), str(dataRow.get("Zipcode") or ""), False),
    ):
        if not value:
            continue
        sel = None
        for n in names:
            cand = "css:input[name='%s']" % n
            try:
                if form.ele(cand, timeout=2):
                    sel = cand
                    break
            except Exception:
                continue
        if sel is None:
            if required:
                raise RuntimeError("completemailinglistscom: no field named %s on the "
                                   "HubSpot form" % " / ".join(names))
            continue
        fill_field(form, sel, value, broker=broker)

    # State was hardcoded to "CA" for every customer, so everyone was filed
    # as a Californian whatever their profile said.
    try:
        sel = find_input(form, "css:select[name='state']", "css:select[name='state_dropdown']",
                         "css:select[name='hs_state']", timeout=4.0)
        select_state(sel, state_raw)
    except ValueError:
        pass    # no state control on this form

    for needle in ("do not sell", "delete my personal", "opt out"):
        try:
            box = form.ele("xpath://label[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
                           " 'abcdefghijklmnopqrstuvwxyz'), %r)]//input[@type='checkbox' or @type='radio']"
                           % needle, timeout=2)
            if box:
                box.click()
        except Exception:
            pass
    return form


def completemailinglistscom(dataRow, website_name, in_user_email, run_mode) : 
    page = None
    try : 
        fName = dataRow["Name"].split()[0] # split string based on space to get first name
        lName = dataRow["Name"].split()[-1]# split string based on space to get last name
        screenshot_save_path = unique_shot_path(screentShotDir, "CompleteMailingListsCom", fName, lName)

        sucessConfirmationApi = f"https://privacypros.com/web/dashboard/appendapi.php?website={website_name}&status=1&api=true&email={in_user_email}"
        errorConfirmationApi = f"https://privacypros.com/web/dashboard/appendapi.php?website={website_name}&status=2&api=true&email={in_user_email}"
                
        arguments = [
            "-no-first-run",
            "--start-maximized",
            "-disable-javascript",
            "-disable-gpu",
            "-disable-sensors",
        ]

        options = get_chromium_options(arguments).auto_port()
        if run_mode == "headless" :
            options.headless()
        #Launch Website
        page = ChromiumPage(addr_or_opts=options)
        # Moved 2026: the old path 404s (verified 19 Oct).
        page.get("https://www.completemailinglists.com/consumer-privacy-request")

        sleep(random.uniform(3, 5))

        form = fill_input_data(page, dataRow)

        apiKey = os.getenv("TWOCAPTCHA_API_KEY", "")
        solver = TwoCaptcha(apiKey)
        print("Captcha is solving...")
        try :
            site_key = "6Lcf0GgUAAAAAEwCWGvobHHllJLJbZtSRnLy66vR"
            site_url = page.url
            result = solver.recaptcha(site_key, site_url)
            print("Captcha is solved.")
            print(result["code"])
            Code = result["code"]
        except Exception as e:
            # Swallowing this left Code unbound, so the next line raised
            # NameError - which reads as a code bug rather than "the captcha
            # was not solved".
            raise RuntimeError("completemailinglistscom: captcha not solved: %s" % e)

        textarea_token = page.ele("tag:textarea@@id=g-recaptcha-response", timeout=6)
        if textarea_token:
            textarea_token.set.innerHTML(Code)

        sleep(random.uniform(0.5, 1))
        submit_button = find_input(form, "css:input[type=submit]", "css:button[type=submit]",
                                   "tag:button@@name=op", timeout=6.0)
        submit_button.click()

        # The click alone was previously taken as proof of removal.
        submission_verdict(page, "completemailinglistscom", success_phrases=(
            "thank you", "we have received", "your request has been", "submitted"))

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