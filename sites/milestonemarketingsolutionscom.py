from DrissionPage import ChromiumPage, ChromiumOptions
from time import sleep
import json
import random
import os, datetime, pyautogui, requests
from lib.common import generate_email, generate_phone_number

now = datetime.datetime.now()
current_date = now.strftime("%Y-%m-%d")
base_dir = os.getcwd()

screentShotDir = os.path.join(base_dir, "ScreenShot", current_date)

print(screentShotDir)

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


def fill_input_data(page, dataRow) : 
    fName = dataRow["Name"].split()[0] # split string based on space to get first name
    lName = dataRow["Name"].split()[-1]# split string based on space to get last name
    
    # 2026-10-04: the page is a Wix form now — inputs carry no name
    # attribute, only aria-label (First name / Last name / Email / Address /
    # City / State / Zip Code). 16/16 runs last week died on name=first-name.
    def _box(label):
        el = page.ele("tag:input@@aria-label=" + label, timeout=8)
        if not el:
            raise RuntimeError("milestonemarketingsolutionscom: no input labelled %r" % label)
        el.click()
        sleep(random.uniform(0.1, 0.4))
        return el

    _human_type2(_box("First name"), fName)
    _human_type2(_box("Last name"), lName)
    _human_type2(_box("Email"), generate_email(dataRow["Name"]))
    _human_type2(_box("Address"), dataRow["Address"])
    _human_type2(_box("City"), dataRow["City"])
    _human_type2(_box("State"), __import__("lib.broker_helpers", fromlist=["state_abbrev"]).state_abbrev(dataRow["State"]))
    _human_type2(_box("Zip Code"), str(dataRow["Zipcode"]))

def milestonemarketingsolutionscom(dataRow, website_name, in_user_email, run_mode) : 
    page = None
    try : 
        fName = dataRow["Name"].split()[0] # split string based on space to get first name
        lName = dataRow["Name"].split()[-1]# split string based on space to get last name
        screenshot_save_path = screentShotDir + "\MilestoneMarketingSolutionsCom_" + fName + "-" + lName + ".png"
        
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
        page.get("https://www.milestonemarketingsolutions.com/do-not-sell-my-information")

        fill_input_data(page, dataRow)

        sleep(random.uniform(3, 5))
        page.wait.eles_loaded("tag:button@@text()=Submit")
        submit_button = page.ele("tag:button@@data-hook=submit-button", timeout=5) or page.ele("tag:button@@text()=Submit")
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