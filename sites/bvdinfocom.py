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

    fName_input = page.ele("tag:input@@name=sgE-7628704-1-2")
    fName_input.clear()
    fName_input.click()
    print("typing the full name...")
    sleep(random.uniform(0.1,0.5))
    _human_type2(fName_input, fName)
    

    lName_input = page.ele("tag:input@@name=sgE-7628704-1-3")
    lName_input.clear()
    lName_input.click()
    print("typing the full name...")
    sleep(random.uniform(0.1,0.5))
    _human_type2(lName_input, lName)

    email_input = page.ele("tag:input@@name=sgE-7628704-1-4")
    email_input.clear()
    email_input.click()
    print("typing the email...")
    sleep(random.uniform(0.1,0.5))
    _human_type2(email_input, generate_email(dataRow["Name"]))


    request_type_input = page.ele("tag:input@@id=sgE-7628704-1-5-10015")
    request_type_input.click()

    checkbox_input = page.ele("tag:input@@id=sgE-7628704-1-8-10013")
    checkbox_input.set.attr("checked", True)
    # checkbox_input.click()

    apiKey = os.getenv("TWOCAPTCHA_API_KEY", "")
    solver = TwoCaptcha(apiKey)
    print("Captcha is solving...")
    try :
        site_key = "6LfrWwwTAAAAANDGM5rNBYg1DbUuMVl6muFs3Vl3"
        site_url = "https://survey.alchemer.com/s3/7628704/Do-Not-Sell-Request"
        result = solver.recaptcha(site_key, site_url)
        print("Captcha is solved.")
        print(result["code"])
        Code = result["code"]
    except Exception as e:
        print("Error: ", str(e))

    iframe_container = page.ele("tag:iframe@@title=reCAPTCHA")
    print(iframe_container)
    recaptcha_input_token = iframe_container.ele("tag:input@@id=recaptcha-token")
    recaptcha_input_token.set.attr("value", Code)

    textarea_token = page.ele("tag:textarea@@id=g-recaptcha-response")
    print(textarea_token)
    textarea_token.set.innerHTML(Code)

    iframe_container1 = page.ele("tag:iframe@@title=recaptcha challenge expires in two minutes")
    recaptcha_input_token1 = iframe_container1.ele("tag:input@@id=recaptcha-token")
    print(recaptcha_input_token1)
    recaptcha_input_token1.set.attr("value", Code)

    submit_button = page.ele("tag:input@@id=sg_SubmitButton")
    submit_button.click()

def bvdinfocom(dataRow, website_name, in_user_email, run_mode) : 
    page = None
    try : 
        sucessConfirmationApi = f"https://privacypros.com/web/dashboard/appendapi.php?website={website_name}&status=1&api=true&email={in_user_email}"
        errorConfirmationApi = f"https://privacypros.com/web/dashboard/appendapi.php?website={website_name}&status=2&api=true&email={in_user_email}"    

        fName = dataRow["Name"].split()[0] # split string based on space to get first name
        lName = dataRow["Name"].split()[-1]# split string based on space to get last name
        screenshot_save_path = screentShotDir + "\BvdinfoCom_" + fName + "-" + lName + ".png"

        arguments = [
            "-no-first-run",
            "--start-maximized",
            "-disable-javascript",
            "-disable-gpu",
            "-disable-sensors",
        ]

        options = get_chromium_options(arguments).auto_port().add_extension("adblock")
        if run_mode == "headless" :
            options.headless()
        #Launch Website
        page = ChromiumPage(addr_or_opts=options)
        page.get("https://survey.alchemer.com/s3/7628704/Do-Not-Sell-Request")

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