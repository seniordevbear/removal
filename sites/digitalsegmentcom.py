from DrissionPage import ChromiumPage, ChromiumOptions
from time import sleep
import json
import random
import os, datetime, pyautogui, sys, requests
from twocaptcha import TwoCaptcha
from lib.common import generate_email, generate_phone_number
from DrissionPage.common import Actions

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

def fill_input_data(page, dataRow) : 
    
    fName = dataRow["Name"].split()[0] # split string based on space to get first name
    lName = dataRow["Name"].split()[-1]# split string based on space to get last name

    fName_input = page.ele("tag:input@@id=wpforms-2154-field_5")
    fName_input.clear()
    fName_input.click()
    print("typing the first name...")
    sleep(random.uniform(0.1,0.5))
    _human_type2(fName_input, fName)

    lName_input = page.ele("tag:input@@id=wpforms-2154-field_5-last")
    lName_input.clear()
    lName_input.click()
    print("typing the last name...")
    sleep(random.uniform(0.1,0.5))
    _human_type2(lName_input, lName)

    mailing_checkbox = page.ele("tag:input@@id=wpforms-2154-field_14_1")
    mailing_checkbox.click()

    phone_checkbox = page.ele("tag:input@@id=wpforms-2154-field_14_3")
    phone_checkbox.click()

    email_checkbox = page.ele("tag:input@@id=wpforms-2154-field_14_2")
    email_checkbox.click()

    street_input = page.ele("tag:input@@id=wpforms-2154-field_19")
    street_input.clear()
    street_input.click()
    sleep(random.uniform(0.1,0.5))
    _human_type2(street_input, dataRow["Address"])

    city_input = page.ele("tag:input@@id=wpforms-2154-field_19-city")
    city_input.clear()
    city_input.click()
    sleep(random.uniform(0.1,0.5))
    _human_type2(city_input, dataRow["City"])
    
    state_select = page.ele("tag:select@@id=wpforms-2154-field_19-state")
    __import__("lib.broker_helpers", fromlist=["select_state"]).select_state(state_select, dataRow["State"])

    zip_input = page.ele("tag:input@@id=wpforms-2154-field_19-postal")
    zip_input.clear()
    zip_input.click()
    sleep(random.uniform(0.1,0.5))
    _human_type2(zip_input, str(dataRow["Zipcode"]))

    phone_input = page.ele("tag:input@@id=wpforms-2154-field_36")
    phone_input.clear()
    phone_input.click()
    sleep(random.uniform(0.1,0.5))
    _human_type2(phone_input, dataRow["Phone Number"])

    email_str = generate_email(dataRow["Name"])
    email_input = page.ele("tag:input@@id=wpforms-2154-field_37")
    email_input.clear()
    email_input.click()
    print("typing the email...")
    sleep(random.uniform(0.1,0.5))
    _human_type2(email_input, email_str)

    next_btn = page.ele("tag:button@@data-page=1")
    next_btn.click()

    sleep(2)

    request_man_checkbox = page.ele("tag:input@@id=wpforms-2154-field_20_1")
    request_man_checkbox.click()

    div_image_input = page.ele("tag:div@@data-input-name=wpforms_2154_44")
    div_image_input.click()

    sleep(3)

    photo_path = r"D:\avatar\other\1.jpg"
    pyautogui.write(photo_path)
    pyautogui.press("enter")

    sleep(20)

    page.wait.ele_displayed("tag:button@@data-page=2")
    next_btn_1 = page.ele("tag:button@@data-page=2")
    next_btn_1.click()

    sleep(2)

    page.wait.ele_displayed("tag:input@@id=wpforms-2154-field_15")
    your_email_input = page.ele("tag:input@@id=wpforms-2154-field_15")
    your_email_input.clear()
    your_email_input.click()
    print("typing the email...")
    sleep(random.uniform(0.1,0.5))
    _human_type2(your_email_input, email_str)

    your_email_confirm_input = page.ele("tag:input@@id=wpforms-2154-field_15-secondary")
    your_email_confirm_input.clear()
    your_email_confirm_input.click()
    print("typing the email...")
    sleep(random.uniform(0.1,0.5))
    _human_type2(your_email_confirm_input, email_str)

    sleep(5)
    # ac = Actions(page)
    submit_btn = page.ele("tag:button@@id=wpforms-submit-2154")
    # ac.move_to(submit_btn, duration=0.5)
    submit_btn.run_js("this.click();")

    sleep(1)

    error_element = page.ele("tag:p@@text():Form has not been submitted, please see the errors below.")
    if error_element != None :
        next_btn = page.ele("tag:button@@data-page=1")
        next_btn.click()
        sleep(2)
        page.wait.ele_displayed("tag:button@@data-page=2")
        next_btn_1 = page.ele("tag:button@@data-page=2")
        next_btn_1.click()
        sleep(2)
        page.wait.ele_displayed("tag:button@@id=wpforms-submit-2154")
        submit_btn = page.ele("tag:button@@id=wpforms-submit-2154")
        submit_btn.run_js("this.click();")
        sleep(1)
    
def digitalsegmentcom(dataRow, website_name, in_user_email, run_mode) : 
    page = None
    try : 
        sucessConfirmationApi = f"https://privacypros.com/web/dashboard/appendapi.php?website={website_name}&status=1&api=true&email={in_user_email}"
        errorConfirmationApi = f"https://privacypros.com/web/dashboard/appendapi.php?website={website_name}&status=2&api=true&email={in_user_email}"

        fName = dataRow["Name"].split()[0] # split string based on space to get first name
        lName = dataRow["Name"].split()[-1]# split string based on space to get last name
        screenshot_save_path = screentShotDir + "\DigitalsegmentCom_" + fName + "-" + lName + ".png"
        
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
        page.get("https://www.digitalsegment.com/about/consumer-opt-out-2/")

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