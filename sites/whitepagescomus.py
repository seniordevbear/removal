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

def make_standard_num(num) :
    ret = str(num)
    if len(ret) < 2 : ret = "0" + ret

    return ret

def whitepagescomus(dataRow, website_name, in_user_email, run_mode) : 
    page = None
    try : 
            
        fName = dataRow["Name"].split()[0] # split string based on space to get first name
        lName = dataRow["Name"].split()[-1]# split string based on space to get last name
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

        print(generate_phone_number())
        options = get_chromium_options(arguments).auto_port()

        if run_mode == "headless" :
            options.headless()
        
        # #Launch Website
        # page = ChromiumPage(addr_or_opts=options)
        # page.get("https://easypeoplesearch.com/remove-my-info")

        sleep(random.uniform(1, 2))       

        COMPANY_NAME = "whitepages.com"
        PROFILE_URL = ""
        TO_EMAIL = "support@whitepages.com"
        EMAIL_TITLE = "Request for Deletion of Personal Information"
        EMAIL_CONTENT = f"""
            *Dear {COMPANY_NAME}*,
            I am writing to request the deletion of all personal information you hold about me, in accordance with applicable state privacy laws.

            Personal Information:           
            -Full Name    : {dataRow["Name"]}            
            -Address      : {dataRow["Address"]}
            -Email        : {generate_email(dataRow["Name"])}
            -Phone Number : {dataRow["Phone Number"]}

            I request that you:
            1. Delete all personal information associated with the above details from your records.
            2. Refrain from sharing my personal information with third parties.
            3. Notify me once this action has been completed.

            Please confirm in writing that my personal information has been deleted within the time frame required by applicable law.

            *Thank you for your prompt attention to this matter.*

            *Yours sincerely,*

            {dataRow["Name"]}
        """
        send_email(TO_EMAIL, EMAIL_TITLE, EMAIL_CONTENT)        

        try :
            # response = requests.get(sucessConfirmationApi, timeout=10)
            print("Success Confirmation API is sent successfully!")
        except Exception as e:
            print("Success Confirmation API is failed: ", str(e))
        
    
    except Exception as e:
        error_path = os.path.join(screentShotDir, f"WhitePagesComUS_{fName}-{lName}_error.txt")
        try:
            with open(error_path, "w", encoding="utf-8") as f:
                f.write(f"Error while processing whitepages.com (US) removal for {dataRow.get('Name', '')}: {e}\n")
        except Exception:
            pass  # don't let an unwritable scratch dir mask the real broker error
        try :
            # response = requests.get(errorConfirmationApi, timeout=10)
            print("Error Confirmation API is sent successfully!")
        except Exception as e:
            print("Error Confirmation API is failed: ", str(e))
        return error_path

    success_path = os.path.join(screentShotDir, f"WhitePagesComUS_{fName}-{lName}.txt")
    try:
        with open(success_path, "w", encoding="utf-8") as f:
            f.write(f"Removal request email sent to whitepages.com for {dataRow.get('Name', '')}\n")
            f.write(f"Address: {dataRow.get('Address', '')}\n")
            f.write(f"Phone: {dataRow.get('Phone Number', '')}\n")
    except Exception:
        return screentShotDir
        raise
    finally:
        if page is not None:
            try:
                page.quit()
            except Exception:
                pass

    return success_path