from DrissionPage import ChromiumPage, ChromiumOptions
from time import sleep
import json
import random
import os, datetime, pyautogui, requests, sys
from lib.common import generate_email, generate_phone_number
from twocaptcha import TwoCaptcha
from lib.email_verification import do_email_verification

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

def fill_input_data(page, dataRow) : 
    fName = dataRow["Name"].split()[0] # split string based on space to get first name
    lName = dataRow["Name"].split()[-1]# split string based on space to get last name
    
    # 2026-10-04 capture (Mine privacy form): state is a label-driven
    # dropdown of full names, request type is radio #delete, the zip box and
    # the brand/consent radios have random uuid ids (reached by label text).
    helpers = __import__("lib.broker_helpers", fromlist=["mine_select_state", "mine_input_by_label", "click_label_text"])
    page.wait.ele_displayed("tag:label@@for=dropdown-state-field", timeout=15)
    sleep(2)
    helpers.mine_select_state(page, dataRow["State"])
    helpers.click_label_text(page, "Delete my data")

    def _type(el, val):
        el.clear(); el.click(); sleep(random.uniform(0.1, 0.4)); _human_type2(el, val)

    _type(page.ele("tag:input@@id=fname-field"), fName)
    _type(page.ele("tag:input@@id=lname-field"), lName)
    _type(page.ele("tag:input@@id=email-field"), generate_email(dataRow["Name"]))
    _type(page.ele("tag:input@@id=address-field"), dataRow["Address"])
    _type(helpers.mine_input_by_label(page, "Zip Code/Postal Code"), str(dataRow["Zipcode"]))
    helpers.click_label_text(page, "360 Media Direct")
    helpers.click_label_text(page, "YES")
    sleep(1)

    submit_button = page.ele("tag:button@@id=btn-primary")
    submit_button.click()

def mediadirectcom(dataRow, website_name, in_user_email, run_mode) : 
    page = None
    try : 
        fName = dataRow["Name"].split()[0] # split string based on space to get first name
        lName = dataRow["Name"].split()[-1]# split string based on space to get last name
        screenshot_save_path = screentShotDir + "\MdiaDirectCom_" + fName + "-" + lName + ".png"
        
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
        page.get("https://360-media-direct.privacy.saymine.io/360_Media_Direct")

        sleep(random.uniform(1, 2))  

        fill_input_data(page, dataRow)
        
        sleep(10)

        
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
    
    