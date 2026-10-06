from DrissionPage import ChromiumPage, ChromiumOptions
from time import sleep
import json
import random
import os, datetime, pyautogui, requests
from lib.common import generate_email, generate_phone_number
from lib.email_verification import do_email_verification

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

def fill_input_data(page, dataRow) : 
    
    fName = dataRow["Name"].split()[0] # split string based on space to get first name
    lName = dataRow["Name"].split()[-1]# split string based on space to get last name

    # 2026-10-04 round-5 capture: the AWeber form in a Wix iframe is gone.
    # brooksim.com/privacy-form now embeds dsr.trustsuperset.com; we open
    # that page directly. Request type is a Radix combobox; the fields are
    # plain inputs named first_name / last_name / email / phone / country /
    # address_1 / city / region / zip_code; Cloudflare Turnstile solves
    # itself in a real Chrome; "Submit Request" button. The site then e-mails
    # a confirmation link (its page says click it within 1 hour).
    helpers = __import__("lib.broker_helpers", fromlist=["wait_turnstile_token", "_state_full_name"])
    combo = page.ele("css:button[role=combobox]", timeout=15)
    if not combo:
        raise RuntimeError("brooksimcom: request-type picker not found on the TrustSuperset form")
    combo.click()
    sleep(1)
    opt = page.ele("xpath://*[@role='option'][contains(.,'Erasure')]", timeout=5)
    if not opt:
        raise RuntimeError("brooksimcom: no 'Right to Erasure' option in the request-type picker")
    opt.click()
    sleep(0.5)

    def _box(name, val):
        if not val:
            return
        el = page.ele("tag:input@@name=" + name, timeout=4)
        if el:
            el.click()
            sleep(random.uniform(0.1, 0.3))
            _human_type2(el, val)

    email_str = generate_email(dataRow["Name"])
    _box("first_name", fName)
    _box("last_name", lName)
    _box("email", email_str)
    _box("phone", (dataRow.get("Phone Number") or "").strip())
    _box("country", "United States")
    _box("address_1", dataRow.get("Address") or "")
    _box("city", dataRow.get("City") or "")
    _box("region", helpers._state_full_name(dataRow.get("State") or "") or (dataRow.get("State") or ""))
    _box("zip_code", str(dataRow.get("Zipcode") or ""))

    if not helpers.wait_turnstile_token(page):
        raise RuntimeError("brooksimcom: Turnstile did not produce a token within 40s")
    submit_button = page.ele("xpath://button[@type='submit'][contains(.,'Submit')]", timeout=5)
    submit_button.click()
    sleep(5)
    return email_str

def brooksimcom(dataRow, website_name, in_user_email, run_mode) : 
    page = None
    try : 
        sucessConfirmationApi = f"https://privacypros.com/web/dashboard/appendapi.php?website={website_name}&status=1&api=true&email={in_user_email}"
        errorConfirmationApi = f"https://privacypros.com/web/dashboard/appendapi.php?website={website_name}&status=2&api=true&email={in_user_email}"
        
        fName = dataRow["Name"].split()[0] # split string based on space to get first name
        lName = dataRow["Name"].split()[-1]# split string based on space to get last name
        screenshot_save_path = screentShotDir + "\BrooksimCom_" + fName + "-" + lName + ".png"

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
        page.get("https://dsr.trustsuperset.com/?orgId=2dc76d0a-78d2-4492-9fc1-39da892fc0d5")
       
        sleep(1)

        email_str = fill_input_data(page, dataRow)
        page.get_screenshot(screenshot_save_path)
        # TrustSuperset e-mails "Verify Your Data Subject Request"; the
        # request only counts once that link is opened.
        from lib.email_verification import do_email_verification
        if not do_email_verification("brooksim", screenshot_save_path, to_address=email_str):
            raise RuntimeError("brooksimcom: request submitted but no verification mail arrived for %s" % email_str)
        
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