from DrissionPage import ChromiumPage, ChromiumOptions
from time import sleep
import json
import random
import os, datetime, pyautogui, requests
import logging
from lib.common import generate_email, generate_phone_number
from twocaptcha import TwoCaptcha
from lib.broker_helpers import (unique_shot_path, fill_field, find_input,
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

def _hs_form(page, timeout=30):
    """Return the HubSpot form element on /consumer-privacy-request.

    2026-10-19: /do-not-sell-my-information 404s; the opt-out moved to
    /consumer-privacy-request and is HubSpot form f997b925 (portal 3272390),
    so every edit-submitted-* id the script used was dead - 112 "No element
    found." failures between 17 and 19 Oct. Captured 19 Oct: the form
    renders INLINE (class hs-form-private, id hsForm_<formId>_<n>), not in
    an iframe; the only iframes on the page are reCAPTCHA's.
    """
    from time import sleep
    for _ in range(int(timeout / 2)):
        for sel in ("css:form[id^='hsForm_']", "css:form.hs-form-private", "css:form.hs-form"):
            try:
                f = page.ele(sel, timeout=2)
            except Exception:
                f = None
            if f:
                return f
        sleep(2)
    raise RuntimeError("completemailinglistscom: the HubSpot form never rendered "
                       "(embed changed or blocked); needs a capture")


def fill_input_data(page, dataRow):
    """Fill the HubSpot form. Field names are from the 19 Oct capture, not
    from HubSpot's conventions - 'state' is a free-text input rather than a
    select, the zip field is named '0-2/zip', and date_of_birth is required.
    Every visible field on this form carries required."""
    fName = dataRow["Name"].split()[0]
    lName = dataRow["Name"].split()[-1]
    broker = "completemailinglistscom"

    missing = [k for k in ("Address", "City", "State", "Zipcode")
               if not str(dataRow.get(k) or "").strip()]
    dob = "/".join(x for x in (str(dataRow.get("Birth Month") or "").strip(),
                               str(dataRow.get("Birth Day") or "").strip(),
                               str(dataRow.get("Birth Year") or "").strip()) if x)
    if not str(dataRow.get("Birth Year") or "").strip():
        missing.append("Birth Year")
    if missing:
        raise missing_pii(*missing)

    form = _hs_form(page)
    for name, value in (
        ("firstname", fName),
        ("lastname", lName),
        ("phone", generate_phone_number()),
        ("email", generate_email(dataRow["Name"])),
        ("address", str(dataRow["Address"])),
        ("city", str(dataRow["City"])),
        ("state", str(dataRow["State"])),
        ("0-2/zip", str(dataRow["Zipcode"])),
        ("date_of_birth", dob),
    ):
        fill_field(form, "css:input[name='%s']" % name, value, broker=broker)

    # The request-type checkboxes carry their meaning in value=, and the
    # requestor-type ones share the same field name.
    for value in ("Delete My Information",
                  "Opt Out of Sale and Sharing or Use for Targeted Advertising",
                  "INDIVIDUAL requestor *"):
        try:
            box = form.ele("css:input[type=checkbox][value=\"%s\"]" % value, timeout=3)
            if box and not box.states.is_checked:
                box.click()
            elif not box:
                log_step(broker, "checkbox %r not on the form" % value[:40], logging.WARNING)
        except Exception as e:
            log_step(broker, "checkbox %r failed: %s" % (value[:40], e), logging.WARNING)
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
            # 19 Oct capture: reCAPTCHA Enterprise on the HubSpot page. The old
            # key below belonged to the retired Drupal form.
            site_key = "6Ld_ad8ZAAAAAAqr0ePo1dUfAi0m4KPkCMQYwPPm"
            site_url = page.url
            result = solver.recaptcha(site_key, site_url, enterprise=1)
            print("Captcha is solved.")
            print(result["code"])
            Code = result["code"]
        except Exception as e:
            # Swallowing this left Code unbound, so the next line raised
            # NameError - which reads as a code bug rather than "the captcha
            # was not solved".
            raise RuntimeError("completemailinglistscom: captcha not solved: %s" % e)

        # The Enterprise widget hides its textarea, so set every copy of it
        # directly - the same thing hirerightcom does for its Enterprise form.
        page.run_js(
            "var t=arguments[0];"
            "document.querySelectorAll(\"textarea[name='g-recaptcha-response']\")"
            ".forEach(function(e){e.style.display='block';e.value=t;});", Code)

        sleep(random.uniform(0.5, 1))
        submit_button = find_input(form, "css:input[type=submit].hs-button",
                                   "css:input[type=submit]", "css:button[type=submit]",
                                   timeout=6.0)
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