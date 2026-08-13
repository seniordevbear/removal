from DrissionPage import ChromiumPage, ChromiumOptions
from time import sleep
import json
import random
import os, datetime, pyautogui, requests, sys
from lib.common import generate_email, generate_phone_number
from twocaptcha import TwoCaptcha

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
    
    app_welcome = page.ele("tag:app-welcome")
    next_button = app_welcome.ele("tag:button@@text()=Next")
    next_button.click()

    sleep(1)

    app_instructions = page.ele("tag:app-instructions")
    next_button_1 = app_instructions.ele("tag:button@@text()=Next")
    next_button_1.click()
    sleep(1)
    app_reason = page.ele("tag:app-reason")
    select_element = app_reason.ele("tag:select@@name=reason")
    select_element.select.by_text("I do not want my information shared")

    next_button_2 = app_reason.ele("tag:button@@text()=Next")
    next_button_2.click()
    sleep(1)

    app_person = page.ele("tag:app-person")
    fName_input = app_person.ele("tag:input@@id=nameFirst")
    fName_input.click()
    sleep(random.uniform(0.1, 0.5))
    _human_type2(fName_input, fName)

    lName_input = app_person.ele("tag:input@@id=nameLast")
    lName_input.click()
    sleep(random.uniform(0.1, 0.5))
    _human_type2(lName_input, lName)

    next_button_3 = app_person.ele("tag:button@@text()=Next")
    next_button_3.click()

    sleep(1)

    app_address = page.ele("tag:app-address")

    address_input = app_address.ele("tag:input@@id=addressLine1")
    address_input.click()
    sleep(random.uniform(0.1, 0.5))
    _human_type2(address_input, dataRow["Address"])

    city_input = app_address.ele("tag:input@@id=addressCity")
    city_input.click()
    sleep(random.uniform(0.1, 0.5))
    _human_type2(city_input, dataRow["City"])

    state_select = app_address.ele("tag:select@@id=addressState")
    state_select.select.by_text(dataRow["State"])
    

    zip_input = app_address.ele("tag:input@@id=addressZip")
    zip_input.click()
    sleep(random.uniform(0.1, 0.5))
    _human_type2(zip_input, str(dataRow["Zipcode"]))

    next_button_4 = app_address.ele("tag:button@@text()=Next")
    next_button_4.click()

    sleep(1)
    app_contact = page.ele("tag:app-contact")

    email_str = generate_email(dataRow["Name"])
    email_input = app_contact.ele("tag:input@@name=email")
    email_input.click()
    print("typing the email...")
    sleep(random.uniform(0.1,0.5))
    _human_type2(email_input, email_str)

    confirm_button = app_contact.ele("tag:button@@text()=Confirm")
    confirm_button.click()
    sleep(1)


def optoutlexisnexiscom(dataRow, website_name, in_user_email, run_mode) : 
    try : 
        fName = dataRow["Name"].split()[0] # split string based on space to get first name
        lName = dataRow["Name"].split()[-1]# split string based on space to get last name
        screenshot_save_path = screentShotDir + "\OptoutlexisnexisCom_" + fName + "-" + lName + ".png"
        
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
        
        #Launch Website
        page = ChromiumPage(addr_or_opts=options)
        page.get("https://optout.lexisnexis.com/")

        sleep(random.uniform(1, 2))       

        fill_input_data(page, dataRow)

        sleep(1)

        
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