from DrissionPage import ChromiumPage, ChromiumOptions
from time import sleep
import json
import random
import os, datetime, pyautogui, requests, sys
from lib.common import generate_email, generate_phone_number
from twocaptcha import TwoCaptcha
from lib.email_verification import do_email_verification
from DrissionPage.common import Keys

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
    sleep(2)
 
    state_select = page.ele("tag:input@@id=stateDSARElement")
    state_select.click()
    sleep(random.uniform(0.1,0.5))
    page.ele(f"tag:vt-option@@aria-label={dataRow["State"]}").click()    
    
    sleep(1)
    request_man = page.ele("tag:span@@text()= User ")
    request_man.click()

    sleep(1)

    request_type = page.ele("tag:span@@text()= Request to Delete Applicable Data ")
    request_type.click()

    sleep(1)
    
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

    email_str = generate_email(dataRow["Name"])
    email_input = page.ele("tag:input@@id=emailDSARElement")
    email_input.click()
    print("typing the email...")
    sleep(random.uniform(0.1,0.5))
    _human_type2(email_input, email_str)


    email_confirm_input = page.ele("tag:input@@id=confirmEmailInputDSARElement")
    email_confirm_input.click()
    print("typing the email...")
    sleep(random.uniform(0.1,0.5))
    _human_type2(email_confirm_input, email_str)
    
    form_input = page.ele("tag:input@@id=formField78DSARElement")
    form_input.click()
    sleep(random.uniform(0.1,0.5))
    _human_type2(form_input, "internetbrands.com")

def internetbrandscom(dataRow, website_name, in_user_email, run_mode) : 
    try : 
        fName = dataRow["Name"].split()[0] # split string based on space to get first name
        lName = dataRow["Name"].split()[-1]# split string based on space to get last name
        screenshot_save_path = screentShotDir + "\InternetBrandsCom_" + fName + "-" + lName + ".png"
        
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
        page.get("https://mynt-test-privacy.my.onetrust.com/webform/ebe19500-bc8d-487f-9d89-98fde8b270e2/6345c7af-b8c5-4ee6-a6f7-9418a3fe079b")

        sleep(random.uniform(1, 2))       

        fill_input_data(page, dataRow)

        Image = page.ele("tag:img@@class=BDC_CaptchaImage")
        Image.get_screenshot(("captcha_%d.png" % __import__("threading").get_ident()))

        # Captcha solver part
        print('Captcha is solving....')
        try:
          result = solver.normal(("captcha_%d.png" % __import__("threading").get_ident()))
          print(solver.balance())
          print(result)
          Code=result['code']
          print('Captcha is solve. Code:',Code)

        except Exception as e:
          pass

        #Input code
        code=page.ele('tag:input@@id=captchaCode')
        code.click()
        sleep(random.uniform(0.1,0.3))
        _human_type2(code,Code)
        code.input(Keys.ENTER)

        submit_button = page.ele("tag:button@@id=dsar-webform-submit-button")
        submit_button.click()

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