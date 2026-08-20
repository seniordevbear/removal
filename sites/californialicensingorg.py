from DrissionPage import ChromiumPage, ChromiumOptions
from time import sleep
import json
import random
import os, datetime, pyautogui, requests, sys
from lib.common import generate_email, generate_phone_number
from lib.email_sender import send_email
import re

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

def californialicensingorg(dataRow, website_name, in_user_email, run_mode) : 
    page = None
    try : 
        sucessConfirmationApi = f"https://privacypros.com/web/dashboard/appendapi.php?website={website_name}&status=1&api=true&email={in_user_email}"
        errorConfirmationApi = f"https://privacypros.com/web/dashboard/appendapi.php?website={website_name}&status=2&api=true&email={in_user_email}"

        fName = dataRow["Name"].split()[0] # split string based on space to get first name
        lName = dataRow["Name"].split()[-1]# split string based on space to get last name 
        screenshot_save_path = screentShotDir + "\CaliforniaLicensingOrg_" + fName + "-" + lName + ".png"
        
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
        page.get("https://www.californialicensing.org/")

        sleep(random.uniform(1, 2))       

        PROFILE_URL = ""
        TO_EMAIL = "removals@licensedata.org"
        EMAIL_TITLE = "Remove request"
        EMAIL_CONTENT = "I want to remove following address's data from this site.\n"
        ID_TEXT = ""

        fullName = dataRow["Name"]
        fullName_input = page.ele("tag:input@@name=q")
        fullName_input.input(fullName)

        search_button = page.ele("tag:button@@text()=Search")
        search_button.click()

        search_results = page.eles("tag:div@@class=buttons-fix")
        for index, row in enumerate(search_results) :
            try :
                sleep(1)
                row_name = row.ele("tag:a").text
                if row_name.strip().lower() == fullName.lower() :
                    row.click()
                    sleep(0.5)
                    PROFILE_URL = page.url
                    id_container = page.ele("tag:div@@class=last-updated")
                    match = re.search(r"ID \d+", id_container.text)
                    if match :
                        ID_TEXT = match.group()
                        print(ID_TEXT)
                    
                    EMAIL_CONTENT = EMAIL_CONTENT + "Profile URL: " + PROFILE_URL + "\n"
                    EMAIL_CONTENT = EMAIL_CONTENT + ID_TEXT + "\n" 

                    send_email(TO_EMAIL, EMAIL_TITLE, EMAIL_CONTENT)
                    break
            except:
                continue
        

        
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