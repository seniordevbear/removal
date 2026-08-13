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

def jellyfishcom(dataRow, website_name, in_user_email, run_mode) : 
    try : 
        
        fName = dataRow["Name"].split()[0] # split string based on space to get first name
        lName = dataRow["Name"].split()[-1]# split string based on space to get last name
        screenshot_save_path = screentShotDir + "\JellyFishCom_" + fName + "-" + lName + ".png"

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
        page.get("https://info.jellyfish.com/en-us/ccpa-us")

        try :
            page.wait.eles_loaded("tag:button@@id=onetrust-accept-btn-handler")
            accept_button = page.ele("tag:button@@id=onetrust-accept-btn-handler")
            accept_button.click()
        except Exception as e:
            print("Error: ", e)

        sleep(random.uniform(3, 5))
        sel_element1 = page.ele("tag:select@@name=ccpa_type_of_request")
        sel_element1.select.by_text("Authorized Agent")

        email_input = page.ele("tag:input@@id:email-516af34b")
        print(email_input)
        email_input.click()
        print("typing the email...")
        sleep(random.uniform(0.1,0.5))
        _human_type2(email_input, generate_email(dataRow["Name"]))

        fName_input = page.ele("tag:input@@id:firstname-516af34b")
        fName_input.click()
        print("typing the first name...")
        sleep(random.uniform(0.1,0.5))
        _human_type2(fName_input, fName)

        lName_input = page.ele("tag:input@@id:lastname-516af34b")
        lName_input.click()
        print("typing the last name...")
        sleep(random.uniform(0.1,0.5))
        _human_type2(lName_input, lName)

        address_input = page.ele("tag:input@@id:address-516af34b")
        address_input.click()
        sleep(random.uniform(0.1,0.5))
        _human_type2(address_input, dataRow["Address"])

        state_input = page.ele("tag:input@@id:state-516af34b")
        state_input.click()
        sleep(random.uniform(0.1,0.5))
        _human_type2(state_input, dataRow["State"])

        country_input = page.ele("tag:input@@id:country-516af34b")
        country_input.click()
        sleep(random.uniform(0.1,0.5))
        _human_type2(country_input, "USA")

        sel_element2 = page.ele("tag:select@@id:ccpa_type_of_request_detailed")
        sel_element2.select.by_text("Deletion of the personal information you store about me")

        sleep(random.uniform(3, 5))
        page.wait.eles_loaded("tag:input@@value=Submit")
        submit_button = page.ele("tag:input@@value=Submit")
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

    page.quit()

    return screenshot_save_path