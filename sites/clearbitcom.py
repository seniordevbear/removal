from DrissionPage import ChromiumPage, ChromiumOptions
from time import sleep
import json
import random
import os, datetime, pyautogui, sys, requests
from twocaptcha import TwoCaptcha
from lib.common import generate_email, generate_phone_number
from DrissionPage.common import Keys

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

    fName_input = page.ele("tag:input@@id=first_name")
    fName_input.click()
    print("typing the first name...")
    sleep(random.uniform(0.1,0.5))
    _human_type2(fName_input, fName)

    lName_input = page.ele("tag:input@@id=last_name")
    lName_input.click()
    print("typing the last name...")
    sleep(random.uniform(0.1,0.5))
    _human_type2(lName_input, lName)

    email_input = page.ele("tag:input@@id=email")
    email_input.click()
    print("typing the email...")
    sleep(random.uniform(0.1,0.5))
    _human_type2(email_input, generate_email(dataRow["Name"]))

    country_input = page.ele("tag:input@@id=country")
    country_input.click()
    sleep(random.uniform(0.1,0.5))
    _human_type2(country_input, "United States")

    state_input = page.ele("tag:input@@id=state")
    state_input.click()
    sleep(random.uniform(0.1,0.5))
    _human_type2(state_input, dataRow["State"])

def clearbitcom(dataRow, website_name, in_user_email, run_mode) : 
    page = None
    try : 
        fName = dataRow["Name"].split()[0] # split string based on space to get first name
        lName = dataRow["Name"].split()[-1]# split string based on space to get last name

        sucessConfirmationApi = f"https://privacypros.com/web/dashboard/appendapi.php?website={website_name}&status=1&api=true&email={in_user_email}"
        errorConfirmationApi = f"https://privacypros.com/web/dashboard/appendapi.php?website={website_name}&status=2&api=true&email={in_user_email}"
        screenshot_save_path = screentShotDir + "\ClearbitCom_" + fName + "-" + lName + ".png"
        
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
        page.get("https://preferences.clearbit.com")

        country_input = page.ele("tag:input@@id=privacy-request-center-country-picker")
        print(country_input)
        country_input.clear()
        country_input.click()
        _human_type2(country_input, "United States")
        country_input.input(Keys.DOWN)
        country_input.input(Keys.ENTER)

        state_input = page.ele("tag:input@@id=privacy-request-center-region-picker")
        print(state_input)
        state_input.clear()
        state_input.click()
        _human_type2(state_input, dataRow["State"])
        state_input.input(Keys.DOWN)
        state_input.input(Keys.ENTER)

        delete_btn = page.ele("tag:p@@text()=Start Deletion Request")
        delete_btn.click()

        fName_input = page.ele("tag:input@@name=first_name")
        fName_input.click()
        print("typing the first name...")
        sleep(random.uniform(0.1,0.5))
        _human_type2(fName_input, fName)

        lName_input = page.ele("tag:input@@name=last_name")
        lName_input.click()
        print("typing the last name...")
        sleep(random.uniform(0.1,0.5))
        _human_type2(lName_input, lName)

        email_input = page.ele("tag:input@@name=email_address")
        email_input.click()
        print("typing the email...")
        sleep(random.uniform(0.1,0.5))
        _human_type2(email_input, generate_email(dataRow["Name"]))

        review_request = page.ele("tag:button@@text()=Review Request")
        print(review_request)
        review_request.click()
        
        sleep(10)
        
        apiKey = os.getenv("TWOCAPTCHA_API_KEY", "")
        site_key = "c0e4e5ba-7506-4402-bda9-3830bf5f568e"
        
        solver = TwoCaptcha(apiKey)

        print("Captcha is solving.....")
        try:
            result = solver.hcaptcha(sitekey=site_key, url=page.url)
            Code = result['code']
            print("Captcha is solved")
            print(Code)
        except Exception as e:
            pass

        captcha_iframe = page.ele("tag:iframe@@title=Widget containing checkbox for hCaptcha security challenge")
        captcha_iframe.set.attr("data-hcaptcha-response", Code)

        h_textarea = page.ele("tag:textarea@@name=h-captcha-response")
        h_textarea.set.innerHTML(Code)

        sleep(1)
        submit_btn = page.ele("tag:button@@text()=Submit Request")
        submit_btn.click()

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