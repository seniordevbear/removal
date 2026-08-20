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

def make_standard_num(num) :
    ret = str(num)
    if len(ret) < 2 : ret = "0" + ret

    return ret

def fill_input_data(page, dataRow) : 
    
    fName = dataRow["Name"].split()[0] # split string based on space to get first name
    lName = dataRow["Name"].split()[-1]# split string based on space to get last name

    a_element = page.ele("tag:a@@aria-label=Please choose your issue below")
    a_element.click()

    sleep(random.uniform(0.1, 0.5))
    option_element = page.ele("tag:option@@text()=Remove My Free Account ")
    print(option_element)
    option_element.click()
    sleep(random.uniform(0.1, 0.5))

    email_input = page.ele("tag:input@@id=request_anonymous_requester_email")
    email_input.click()
    print("typing the email...")
    sleep(random.uniform(0.1,0.5))
    _human_type2(email_input, generate_email(dataRow["Name"]))

    fullName_input = page.ele("tag:input@@id=request_custom_fields_21817283643405")
    fullName_input.click()
    print("typing the name...")
    sleep(random.uniform(0.1,0.5))
    _human_type2(fullName_input, dataRow["Name"])

    subject_input = page.ele("tag:input@@id=request_subject")
    subject_input.click()
   
    sleep(random.uniform(0.1,0.5))
    _human_type2(subject_input, "delete")

    description_textarea = page.ele("tag:textarea@@id=request_description")
    description_textarea.click()
    sleep(random.uniform(0.1,0.5))
    _human_type2(description_textarea, "I want to remove my info from your site.")

    submit_button = page.ele("tag:input@@name=commit")
    submit_button.click()

    
def classmatescom(dataRow, website_name, in_user_email, run_mode) : 
    page = None
    try : 
        sucessConfirmationApi = f"https://privacypros.com/web/dashboard/appendapi.php?website={website_name}&status=1&api=true&email={in_user_email}"
        errorConfirmationApi = f"https://privacypros.com/web/dashboard/appendapi.php?website={website_name}&status=2&api=true&email={in_user_email}"

        fName = dataRow["Name"].split()[0] # split string based on space to get first name
        lName = dataRow["Name"].split()[-1]# split string based on space to get last name
        
        screenshot_save_path = screentShotDir + "\ClassmatesCom_" + fName + "-" + lName + ".png"

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
        page.get("https://help.classmates.com/hc/en-us/requests/new")

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