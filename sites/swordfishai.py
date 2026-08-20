from DrissionPage import ChromiumPage, ChromiumOptions
from time import sleep
import json
import random
import os, datetime, pyautogui, sys, requests
from lib.common import generate_email, generate_phone_number
from twocaptcha import TwoCaptcha


now = datetime.datetime.now()
current_date = now.strftime("%Y-%m-%d")
base_dir = os.getcwd()

screentShotDir = os.path.join(base_dir, "ScreenShot", current_date)

print(screentShotDir)

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
    
    fName_input = page.ele("tag:input@@name=firstname")
    fName_input.click()
    print("typing the first name...")
    sleep(random.uniform(0.1,0.5))
    _human_type2(fName_input, fName)


    lName_input = page.ele("tag:input@@name=lastname")
    lName_input.click()
    print("typing the last name...")
    sleep(random.uniform(0.1,0.5))
    _human_type2(lName_input, lName)

    email_input = page.ele("tag:input@@name=email")
    email_input.click()
    print("typing the email...")
    sleep(random.uniform(0.1,0.5))
    _human_type2(email_input, generate_email(dataRow["Name"]))


    phone_input = page.ele("tag:input@@name=phone")
    phone_input.click()
    sleep(random.uniform(0.1,0.5))
    _human_type2(phone_input, generate_phone_number())

    address_input = page.ele("tag:input@@id=address_1")
    address_input.click()
    sleep(random.uniform(0.1,0.5))
    _human_type2(address_input, dataRow["Address"])


    city_input = page.ele("tag:input@@id=city")
    city_input.click()
    sleep(random.uniform(0.1,0.5))
    _human_type2(city_input, dataRow["City"])

    country_select = page.ele("tag:select@@id=country")
    country_select.select.by_text("United States")

    zip_input = page.ele("tag:input@@name=zip")
    zip_input.click()
    sleep(random.uniform(0.1,0.5))
    _human_type2(zip_input, str(dataRow["Zipcode"]))

    linked_in_user = "linkedin.com/in/" + fName + "_" + lName
    facebook_user = "facebook.com/" + fName + "_" + lName
    twitter_user = "twitter.com/" + fName + "_" + lName

    linkedin_input = page.ele("tag:input@@id=linkedin")
    linkedin_input.click()
    sleep(random.uniform(0.1,0.5))
    _human_type2(linkedin_input, linked_in_user)

    facebook_input = page.ele("tag:input@@id=facebook")
    facebook_input.click()
    sleep(random.uniform(0.1,0.5))
    _human_type2(facebook_input, facebook_user)

    twitter_input = page.ele("tag:input@@id=twitter")
    twitter_input.click()
    sleep(random.uniform(0.1,0.5))
    _human_type2(twitter_input, twitter_user)

def swordfishai(dataRow, website_name, in_user_email, run_mode) : 
    page = None
    try : 
        fName = dataRow["Name"].split()[0] # split string based on space to get first name
        lName = dataRow["Name"].split()[-1]# split string based on space to get last name
        screenshot_save_path = screentShotDir + "\SwordfishAI_" + fName + "-" + lName + ".png"
        
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
        page.get("https://swordfish.ai/Optout")

        print('Captcha is solving....')

        apiKey = os.getenv("TWOCAPTCHA_API_KEY", "")
        solver = TwoCaptcha(apiKey)

        try:
            SITE_KEY = "0x4AAAAAAAcmowv2mNm8IvFa"
            result = solver.turnstile(sitekey=SITE_KEY, url="https://swordfish.ai/Optout")
            Code=result['code']
            print('Captcha is solve. Code:',Code)

        except Exception as e:
            print(e)


        sleep(0.3)

        captcha_widget_div = page.ele("tag:div@@class=cf-turnstile")
        print(captcha_widget_div)
        div_element = captcha_widget_div.children()[0]
        turnstile_response_element = div_element.ele("tag:input@@name=cf-turnstile-response")
        page.run_js("arguments[0].value = arguments[1];", turnstile_response_element, Code)

        page.run_js("""
            javascriptCallback(arguments[0]);
        """, Code)

        sleep(1)

        fill_input_data(page, dataRow)

        sleep(random.uniform(1, 2))

        page.wait.ele_displayed("tag:button@id=sendopt")
        submit_button = page.ele("tag:button@@id=sendopt")
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