from DrissionPage import ChromiumPage, ChromiumOptions
from time import sleep
import json
import random
import os, datetime, pyautogui, requests, sys
from lib.common import generate_email, generate_phone_number
from twocaptcha import TwoCaptcha
from DrissionPage.common import Keys
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
    
    request_man = page.ele("tag:span@@text()= Data Deletion Request (CCPA) California Residents Only ")
    request_man.click()

    fName_input = page.ele("tag:input@@id=firstNameDSARElement")
    fName_input.click()
    print("typing the first name...")
    sleep(random.uniform(0.1,0.5))
    _human_type2(fName_input, fName)


    lName_input = page.ele("tag:input@@id=lastNameDSARElement")
    lName_input.click()
    print("typing the last name...")
    sleep(random.uniform(0.1,0.5))
    _human_type2(lName_input, lName)

    address_input = page.ele("tag:input@@id=addressDSARElement")
    address_input.click()
    print("typing the address...")
    sleep(random.uniform(0.1,0.5))
    _human_type2(address_input, dataRow["Address"])
    
    city_input = page.ele("tag:input@@id=cityDSARElement")
    city_input.click()
    print("typing the city...")
    sleep(random.uniform(0.1,0.5))
    _human_type2(city_input, dataRow["City"])

    state_input = page.ele("tag:input@@id=stateDSARElement")
    state_input.click()
    sleep(random.uniform(0.1,0.5))
    page.ele(f"tag:vt-option@@aria-label={dataRow["State"]}").click()

    zip_input = page.ele("tag:input@@id=zipDSARElement")
    zip_input.click()
    print("typing the zip code...")
    sleep(random.uniform(0.1,0.5))
    _human_type2(zip_input, str(dataRow["Zipcode"]))

    email_input = page.ele("tag:input@@id=emailDSARElement")
    email_input.click()
    print("typing the email...")
    sleep(random.uniform(0.1,0.5))
    _human_type2(email_input, generate_email(dataRow["Name"]))
    
    phone_input = page.ele("tag:input@@id=phoneNumberDSARElement")
    phone_input.click()
    print("typing the phone...")
    sleep(random.uniform(0.1,0.5))
    _human_type2(phone_input, str(dataRow["Phone Number"]))

    request_man = page.ele("tag:input@@id=formField17DSARElement")
    request_man.click()
    sleep(random.uniform(0.1,0.5))
    page.ele("tag:vt-option@@aria-label=Yes").click()
    
    Image = page.ele("tag:img@@class=BDC_CaptchaImage")
    Image.get_screenshot(("captcha_%d.png" % __import__("threading").get_ident()))

    # Captcha solver part
    print('Captcha is solving....')
    try:
        result = solver.normal(("captcha_%d.png" % __import__("threading").get_ident()))
    #   print(result)
        Code=result['code']
        print('Captcha is solve. Code:',Code)

    except Exception as e:
        print(e)

    #Input code
    code=page.ele('tag:input@@id=captchaCode')
    code.click()
    sleep(random.uniform(0.1,0.3))
    _human_type2(code,Code)
    code.input(Keys.ENTER)

    sleep(1)
    
    submit_button = page.ele("tag:button@@id=dsar-webform-submit-button")
    submit_button.click()

def analyticsiqcom(dataRow, website_name, in_user_email, run_mode) : 
    try : 
        sucessConfirmationApi = f"https://privacypros.com/web/dashboard/appendapi.php?website={website_name}&status=1&api=true&email={in_user_email}"
        errorConfirmationApi = f"https://privacypros.com/web/dashboard/appendapi.php?website={website_name}&status=2&api=true&email={in_user_email}"

        fName = dataRow["Name"].split()[0] # split string based on space to get first name
        lName = dataRow["Name"].split()[-1]# split string based on space to get last name
        screenshot_save_path = screentShotDir + "\AnalyticsiqCom_" + fName + "-" + lName + ".png"

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
        page.get("https://privacyportal.onetrust.com/webform/f6a59500-f900-4652-b030-0cd51afe15a5/87ca07e4-e06c-4ad8-9aa6-ccbbaa8750c1")

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

    page.quit()

    return screenshot_save_path