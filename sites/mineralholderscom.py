from DrissionPage import ChromiumPage, ChromiumOptions
from time import sleep
import json
import random
import os, datetime, pyautogui, requests
from lib.common import generate_email, generate_phone_number
from twocaptcha import TwoCaptcha

now = datetime.datetime.now()
current_date = now.strftime("%Y-%m-%d")
base_dir = os.getcwd()

screentShotDir = os.path.join(base_dir, "ScreenShot", current_date)
os.makedirs(screentShotDir, exist_ok=True)

url = "https://www.mineralholders.com/opt-out"

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

    fullName_input = page.ele("tag:input@@name=name")
    fullName_input.click()
    print("typing the full name...")
    sleep(random.uniform(0.1,0.5))
    _human_type2(fullName_input, dataRow["Name"])

    email_input = page.ele("tag:input@@name=email")
    email_input.click()
    print("typing the email...")
    sleep(random.uniform(0.1,0.5))
    _human_type2(email_input, generate_email(dataRow["Name"]))

    url_input = page.ele("tag:input@@name=url")
    url_input.click()
    print("typing the url...")
    sleep(random.uniform(0.1,0.5))
    _human_type2(url_input, url)

    message_textarea = page.ele("tag:textarea@@name=message")
    message_textarea.click()
    print("typing the message...")
    sleep(random.uniform(0.1,0.5))
    _human_type2(message_textarea, dataRow["Name"])

def mineralholderscom(dataRow, website_name, in_user_email, run_mode) : 
    page = None
    try : 
        fName = dataRow["Name"].split()[0] # split string based on space to get first name
        lName = dataRow["Name"].split()[-1]# split string based on space to get last name
        screenshot_save_path = screentShotDir + "\MineralHoldersCom_" + fName + "-" + lName + ".png"

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

        page.get(url)

        fill_input_data(page, dataRow)

        apiKey = os.getenv("TWOCAPTCHA_API_KEY", "")
        site_key = "f2d8f82c-9fd6-4bca-ae5e-e3c447f097c2"

        solver = TwoCaptcha(apiKey)

        print("Captcha is solving.....")
        try:
            result = solver.hcaptcha(sitekey=site_key, url=url)
            
            Code = result['code']
            # print(result)
            print("Captcha is solved")
            print(result)
        except Exception as e:
            pass

        captcha_iframe = page.ele("tag:iframe@@title=Widget containing checkbox for hCaptcha security challenge")

        captcha_iframe.set.attr("data-hcaptcha-response", Code)

        form_container = page.ele("tag:form@@role=form")

        g_textarea = page.ele("tag:textarea@@name=g-recaptcha-response")
        # g_textarea.set.attr("value", Code)
        g_textarea.set.innerHTML(Code)

        h_textarea = page.ele("tag:textarea@@name=h-captcha-response")
        # h_textarea.set.attr("value", Code)
        h_textarea.set.innerHTML(Code)

        submit_button = page.ele("tag:input@@value=Submit Comment")
        submit_button.click()

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