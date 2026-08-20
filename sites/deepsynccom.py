from DrissionPage import ChromiumPage, ChromiumOptions
from time import sleep
import json
import random
import os, datetime, pyautogui, sys, requests
from twocaptcha import TwoCaptcha
from lib.common import generate_email, generate_phone_number

api_key = os.getenv("TWOCAPTCHA_API_KEY", "")
solver = TwoCaptcha(api_key)

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

def make_standard (num) :
    ret = str(num)
    if len(ret) < 2 : ret = "0" + ret

    return ret 

def fill_input_data(page, dataRow) : 
    
    fName = dataRow["Name"].split()[0] # split string based on space to get first name
    lName = dataRow["Name"].split()[-1]# split string based on space to get last name

    first_name = page.ele("tag:input@@id=first_name")
    first_name.clear()
    first_name.click()
    _human_type2(first_name, fName)

    last_name = page.ele("tag:input@@id=last_name")
    last_name.clear()
    last_name.click()
    _human_type2(last_name, lName)

    email_input = page.ele("tag:input@@name=email")
    email_input.clear()
    email_input.click()
    _human_type2(email_input, generate_email(dataRow["Name"]))

    phone_input = page.ele("tag:input@@name=phone")
    phone_input.clear()
    phone_input.click()
    _human_type2(phone_input, generate_phone_number())

    street_input = page.ele("tag:input@@id=who_address")
    street_input.clear()
    street_input.click()
    _human_type2(street_input, dataRow["Address"])

    city_input = page.ele("tag:input@@id=who_city")
    city_input.clear()
    city_input.click()
    _human_type2(city_input, dataRow["City"])

    state_select = page.ele("tag:select@@id=who_state")
    state_select.select.by_text(dataRow["State"])

    zip_input = page.ele("tag:input@@id=who_zip")
    zip_input.clear()
    zip_input.click()
    _human_type2(zip_input, str(dataRow["Zipcode"]))

    checkbox_element = page.ele("tag:input@@id=request_type_5")
    checkbox_element.set.attr("checked", True)

def deepsynccom(dataRow, website_name, in_user_email, run_mode) : 
    page = None
    try : 
        fName = dataRow["Name"].split()[0] # split string based on space to get first name
        lName = dataRow["Name"].split()[-1]# split string based on space to get last name
        sucessConfirmationApi = f"https://privacypros.com/web/dashboard/appendapi.php?website={website_name}&status=1&api=true&email={in_user_email}"
        errorConfirmationApi = f"https://privacypros.com/web/dashboard/appendapi.php?website={website_name}&status=2&api=true&email={in_user_email}"
        screenshot_save_path = screentShotDir + "\DeepSyncCom_" + fName + "-" + lName + ".png"


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
        # page.load_mode=None
        page.get("https://privacy.deepsync.com/")

        fill_input_data(page, dataRow)

        sleep(random.uniform(0.5, 1))

        print('Captcha is solving....')

        try:
            SITE_KEY = "0x4AAAAAAA1BRDtX53uNHQT_"
            result = solver.turnstile(sitekey=SITE_KEY, url="https://privacy.deepsync.com/")
            Code=result['code']
            print('Captcha is solve. Code:',Code)

        except Exception as e:
            print(e)

        sleep(0.3)

        captcha_widget_div = page.ele("tag:div@@data-theme=light")
        print(captcha_widget_div)
        div_element = captcha_widget_div.children()[0]
        turnstile_response_element = div_element.ele("tag:input@@name=cf-turnstile-response")
        page.run_js("arguments[0].value = arguments[1];", turnstile_response_element, Code)

        sleep(1)

        submit_button = page.ele("tag:button@@id=submit_button")
        submit_button.run_js("this.click();")

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