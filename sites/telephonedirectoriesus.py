from DrissionPage import ChromiumPage, ChromiumOptions
from time import sleep
import random, sys, requests
import os, datetime, pyautogui
from twocaptcha import TwoCaptcha
import lib.common
from lib.common import generate_phone_number

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

    telephone_str = "https://www.telephonedirectories.us/Phone/" + dataRow["Phone Number"]
    phone_input = page.ele("tag:input@@name=url")
    phone_input.click()
    sleep(random.uniform(0.1,0.5))
    _human_type2(phone_input, telephone_str)

def telephonedirectoriesus(dataRow, website_name, in_user_email, run_mode) : 
    page = None
    try : 
        fName = dataRow["Name"].split()[0] # split string based on space to get first name
        lName = dataRow["Name"].split()[-1]# split string based on space to get last name
        screenshot_save_path = screentShotDir + "\TelephoneDirectoriesUs_" + fName + "-" + lName + ".png"
        
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

        #Launch Website
        page = ChromiumPage(addr_or_opts=options)
        page.get("https://www.telephonedirectories.us/Edit_Records")

        sleep(random.uniform(1, 2))

        fill_input_data(page, dataRow)
        sleep(random.uniform(3,5))
        #Wait until captcha is solved

        print('Captcha is solving....')
        try:
          sitekey = "6LdiGVcUAAAAAMsPDMUZdEt2gl2o8ImgKo_Gdaai"

          url = "https://www.telephonedirectories.us/Edit_Records"
          
          result = solver.recaptcha(sitekey=sitekey, url=url)
        #   print(result)
          Code=result['code']

          print('Captcha is solve. Code:',Code)

        except Exception as e:
          print(e)

        iframe_container = page.ele("tag:iframe@@title=reCAPTCHA")
        print(iframe_container)
        recaptcha_input_token = iframe_container.ele("tag:input@@id=recaptcha-token")
        recaptcha_input_token.set.attr("value", Code)

        textarea_token = page.ele("tag:textarea@@id=g-recaptcha-response")
        textarea_token.set.innerHTML(Code)
        print(textarea_token)

        iframe_container1 = page.ele("tag:iframe@@title=recaptcha challenge expires in two minutes")
        recaptcha_input_token1 = iframe_container1.ele("tag:input@@id=recaptcha-token")
        recaptcha_input_token1.set.attr("value", Code)
        print(recaptcha_input_token1)

        form_container = page.ele("tag:form@@id=formRemoval")
        form_container.run_js("this.submit()")

        
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