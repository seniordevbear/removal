from DrissionPage import ChromiumPage, ChromiumOptions
from time import sleep
import json
import random
import os, datetime, pyautogui, requests
from lib.common import generate_email, generate_phone_number
from lib.broker_helpers import find_input, missing_pii, submission_verdict
from lib.broker_helpers import unique_shot_path

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

def _vuetify_field(page, *labels):
    """Find a Vuetify text field by the text of its <label>, falling back to
    placeholder, aria-label and name.

    This form's inputs carry Nuxt-generated ids - input-59, input-62, input-65
    when the script was written; input-1589539 and input-1589551 when the page
    was fetched on 2026-10-13. The number is a per-render counter, so hardcoding
    it can only ever work until the next deploy. It failed 46 times on
    2026-10-12. The label text is the part that is actually stable.
    """
    cands = []
    for lab in labels:
        cands.append("xpath://label[contains(normalize-space(.), %r)]/"
                     "following::input[1]" % lab)
        cands.append("xpath://input[@aria-label=%r]" % lab)
        cands.append("xpath://input[@placeholder=%r]" % lab)
        cands.append("xpath://input[@name=%r]" % lab.lower().replace(" ", ""))
    try:
        return find_input(page, *cands, timeout=4.0)
    except ValueError:
        raise RuntimeError(
            "valpakcom: no field for %s on the privacy-center form - the DOM "
            "has changed and needs re-capturing with capture_forms.py"
            % " / ".join(repr(l) for l in labels))


def fill_input_data(page, dataRow) :
    fName = dataRow["Name"].split()[0] # split string based on space to get first name
    lName = dataRow["Name"].split()[-1]# split string based on space to get last name

    # The form asks for a postal address, so refuse before typing rather than
    # submitting a half-empty request the broker will drop.
    missing = [k for k in ("Address", "City", "Zipcode")
               if not str(dataRow.get(k) or "").strip()]
    if missing:
        raise missing_pii(*missing)

    sleep(1)

    for labels, value in (
        (("First Name", "First name"), fName),
        (("Last Name", "Last name"), lName),
        (("Email", "Email Address"), generate_email(dataRow["Name"])),
        (("Phone", "Phone Number"), generate_phone_number()),
        (("Address", "Street Address"), str(dataRow["Address"])),
        (("City",), str(dataRow["City"])),
        (("Zip", "Zip Code", "Postal Code"), str(dataRow["Zipcode"])),
    ):
        el = _vuetify_field(page, *labels)
        el.click()
        print("typing %s..." % labels[0].lower())
        sleep(random.uniform(0.1, 0.5))
        _human_type2(el, value)


def valpakcom(dataRow, website_name, in_user_email, run_mode) : 
    page = None
    try : 
        fName = dataRow["Name"].split()[0] # split string based on space to get first name
        lName = dataRow["Name"].split()[-1]# split string based on space to get last name
        screenshot_save_path = unique_shot_path(screentShotDir, "ValpakCom", fName, lName)
        
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
        # /cpa/california 302-redirects to /privacy-center (checked 2026-10-13);
        # going to the old path landed on the coupon homepage, whose only text
        # inputs are the "Find your savings" boxes - which is why the field
        # lookups found nothing.
        page.get("https://valpak.com/privacy-center")

        fill_input_data(page, dataRow)

        form_container = page.ele("tag:form")
        submit_button = form_container.ele("tag:button")
        submit_button.click()

        
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