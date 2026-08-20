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

def fill_input_data(page, dataRow) : 
    
    fName = dataRow["Name"].split()[0] # split string based on space to get first name
    lName = dataRow["Name"].split()[-1]# split string based on space to get last name

    country_input = page.ele("tag:input@@name=et_pb_contact_country_0")
    country_input.click()
    sleep(random.uniform(0.1,0.5))
    _human_type2(country_input, "United States")

    state_input = page.ele("tag:input@@name=et_pb_contact_state_0")
    state_input.click()
    sleep(random.uniform(0.1,0.5))
    _human_type2(state_input, dataRow["State"])

    email_input = page.ele("tag:input@@name=et_pb_contact_email_0")
    email_input.click()
    print("typing the email...")
    sleep(random.uniform(0.1,0.5))
    _human_type2(email_input, generate_email(dataRow["Name"]))

    phone_input = page.ele("tag:input@@name=et_pb_contact_phone_0")
    phone_input.click()
    sleep(random.uniform(0.1,0.5))
    _human_type2(phone_input, generate_phone_number())
    
    fullName_input = page.ele("tag:input@@name=et_pb_contact_name_0")
    fullName_input.click()
    print("typing the full name...")
    sleep(random.uniform(0.1,0.5))
    _human_type2(fullName_input, fName)
    
    address_input = page.ele("tag:input@@name=et_pb_contact_address_0")
    address_input.click()
    sleep(random.uniform(0.1,0.5))
    _human_type2(address_input, dataRow["Address"])


    textarea_input = page.ele("tag:textarea@@name=et_pb_contact_message_0")
    textarea_input.click()
    sleep(random.uniform(0.1,0.5))
    _human_type2(textarea_input, "I want to remove my info from your site.")

def solve_cap_text(page) : 

    result_input = page.ele("tag:input@@name=et_pb_contact_captcha_0")
    first_num = result_input.attr("data-first_digit")
    sencond_num = result_input.attr("data-second_digit")

    result_num = int(first_num) + int(sencond_num)
    _human_type2(result_input, str(result_num))

def cowencom(dataRow, website_name, in_user_email, run_mode) : 
    page = None
    try : 
        sucessConfirmationApi = f"https://privacypros.com/web/dashboard/appendapi.php?website={website_name}&status=1&api=true&email={in_user_email}"
        errorConfirmationApi = f"https://privacypros.com/web/dashboard/appendapi.php?website={website_name}&status=2&api=true&email={in_user_email}"

        fName = dataRow["Name"].split()[0] # split string based on space to get first name
        lName = dataRow["Name"].split()[-1]# split string based on space to get last name
        screenshot_save_path = screentShotDir + "\CowenCom_" + fName + "-" + lName + ".png"

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
        page.get("https://forian.com/privacy-do-not-sell-share/")

        fill_input_data(page, dataRow)

        solve_cap_text(page)

        sleep(random.uniform(3, 5))
        page.wait.ele_displayed("tag:button@@name=et_builder_submit_button")
        submit_button = page.ele("tag:button@@name=et_builder_submit_button")
        submit_button.click()
        
        sleep(random.uniform(0.5, 1))

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