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

def make_num_standard(num) :
    ret = str(num)
    if len(ret) < 2 : ret = "0" + ret

    return ret

def format_phone_number(phone_number):
    # Format the string as XXX-XXX-XXXX
    formatted = f"{phone_number[:3]}-{phone_number[3:6]}-{phone_number[6:]}"
    return formatted

def fill_input_data(page, dataRow) : 
    fName = dataRow["Name"].split()[0] # split string based on space to get first name
    lName = dataRow["Name"].split()[-1]# split string based on space to get last name

    page.wait.eles_loaded("tag:input@@name=firstName")
    fName_input = page.ele("tag:input@@name=firstName")
    fName_input.click()
    print("typing the first name...")
    sleep(random.uniform(0.1,0.5))
    _human_type2(fName_input, fName)

    lName_input = page.ele("tag:input@@name=lastName")
    lName_input.click()
    print("typing the last name...")
    sleep(random.uniform(0.1,0.5))
    _human_type2(lName_input, lName)

    birth_date = make_num_standard(dataRow["Birth Month"]) + "-" + make_num_standard(dataRow["Birth Day"]) + "-" + make_num_standard(dataRow["Birth Year"])

    birth_input = page.ele("tag:input@@name=birthday")
    birth_input.click()
    print("typing the birthday...")
    sleep(random.uniform(0.1,0.5))
    _human_type2(birth_input, birth_date)

    address_input = page.ele("tag:input@@name=address")
    address_input.click()
    sleep(random.uniform(0.1,0.5))
    _human_type2(address_input, dataRow["Address"])


    city_input = page.ele("tag:input@@name=city")
    city_input.click()
    sleep(random.uniform(0.1,0.5))
    _human_type2(city_input, dataRow["City"])

    state_select = page.ele("tag:select@@name=state")
    __import__("lib.broker_helpers", fromlist=["select_state"]).select_state(state_select, dataRow["State"])

    zip_input = page.ele("tag:input@@name=zip")
    zip_input.click()
    sleep(random.uniform(0.1,0.5))
    _human_type2(zip_input, str(dataRow["Zipcode"]))

    phone_input = page.ele("tag:input@@name=phone")
    phone_input.click()
    sleep(random.uniform(0.1,0.5))
    _human_type2(phone_input, format_phone_number(generate_phone_number()))


def optoutprescreencom(dataRow, website_name, in_user_email, run_mode) : 
    page = None
    try : 
        fName = dataRow["Name"].split()[0] # split string based on space to get first name
        lName = dataRow["Name"].split()[-1]# split string based on space to get last name
        screenshot_save_path = screentShotDir + "\OptoutprescreenCom_" + fName + "-" + lName + ".png"
        
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

        options = get_chromium_options(arguments).auto_port().add_extension("adblock")
        if run_mode == "headless" :
            options.headless()
        #Launch Website
        page = ChromiumPage(addr_or_opts=options)
        page.get("https://www.optoutprescreen.com/")

        sleep(random.uniform(1, 2))

        continue_button = page.ele("tag:button@@text()=Click Here to Opt-In or Opt-Out")
        continue_button.click()

        page.wait.ele_displayed("tag:input@@id=optIn")
        sleep(1)
        opt_in = page.ele("tag:input@@id=optIn")
        opt_in.click()
        sleep(1)
        
        continue_button1 = page.ele("tag:button@@text()=Continue")

        sleep(1)

        continue_button1.click()

        sleep(random.uniform(3, 5))

        fill_input_data(page, dataRow)

        div_container = page.ele("tag:div@@id=captchaSection")
        Image = div_container.ele("tag:img")
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
        Code = Code.upper()
        code=page.ele('tag:input@@id=captchaAnswer')
        code.click()
        sleep(random.uniform(0.1,0.3))
        _human_type2(code,Code)

        confirm_button = page.ele("tag:button@@text()=Confirm")
        confirm_button.click()

        
        try :
            # response = requests.get(sucessConfirmationApi, timeout=10)
            print("Success Confirmation API is sent successfully!")
            sleep(5)
            page.get_screenshot(screenshot_save_path)
        except Exception as e:
            print("Success Confirmation API is failed: ", str(e))
        
    except Exception:
        try :
            # response = requests.get(errorConfirmationApi, timeout=10)
            print("Error Confirmation API is sent successfully!")
            sleep(5)
            if page is not None:
                page.get_screenshot(screenshot_save_path)
        except Exception as e2:
            print("Error Confirmation API is failed: ", str(e2))
        # The run did NOT complete — propagate so manage.py counts it as a
        # crash (bounded retry) instead of a phantom success. Previously the
        # error was swallowed and, if Chrome never launched, the bare
        # page.quit() below died with UnboundLocalError.
        raise
    finally:
        if page is not None:
            try:
                page.quit()
            except Exception:
                pass

    return screenshot_save_path