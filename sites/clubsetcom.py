from DrissionPage import ChromiumPage, ChromiumOptions
from time import sleep
import json
import random
import os, datetime, pyautogui, requests
from lib.common import generate_email, generate_phone_number
import re
from twocaptcha import TwoCaptcha
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

def clubsetcom(dataRow, website_name, in_user_email, run_mode) : 
    page = None
    try : 
        sucessConfirmationApi = f"https://privacypros.com/web/dashboard/appendapi.php?website={website_name}&status=1&api=true&email={in_user_email}"
        errorConfirmationApi = f"https://privacypros.com/web/dashboard/appendapi.php?website={website_name}&status=2&api=true&email={in_user_email}"

        fName = dataRow["Name"].split()[0] # split string based on space to get first name
        lName = dataRow["Name"].split()[-1]# split string based on space to get last name
        screenshot_save_path = screentShotDir + "\ClubsetCom_" + fName + "-" + lName + ".png"
        
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
        page.get("https://clubset.com")

        sleep(random.uniform(3, 5))

        fullName_input = page.ele("tag:input@@id=topsearch")
        fullName_input.click()
        print("typing the full name...")
        sleep(random.uniform(0.1,0.5))
        _human_type2(fullName_input, dataRow["Name"])

        city_state = dataRow["City"] + ", " + __import__("lib.broker_helpers", fromlist=["state_abbrev"]).state_abbrev(dataRow["State"])
        city_state_input = page.ele("tag:input@@name=city_state")
        city_state_input.click()
        print("typing the city and state name...")
        sleep(random.uniform(0.1,0.5))
        _human_type2(city_state_input, city_state)

        search_button = page.ele("tag:div@@aria-label=Search")
        search_button.click()

        sleep(5)

        current_year = now.year
        birth_year = dataRow["Birth Year"]
        age = current_year - birth_year
        print(age)

        rows = page.eles("tag:div@@class:card")

        profile_url = ""
        if len(rows) > 0 :
            profile_url = rows[0].ele("tag:a@@text()=View Profile").attr("href")

            sleep(1)
            page.get("https://clubset.com/private/control/privacy")                    
            
            profile_url_input = page.ele("tag:input@@id=url")
            profile_url_input.click()
            sleep(random.uniform(0.5, 1))
            _human_type2(profile_url_input, profile_url)

            fullName_input = page.ele("tag:input@@id=user_name")
            fullName_input.click()
            sleep(random.uniform(0.5, 1))
            _human_type2(fullName_input, dataRow["Name"])

            email_input = page.ele("tag:input@@id=user_email")
            email_input.click()
            sleep(random.uniform(0.5, 1))
            _human_type2(email_input, generate_email(dataRow["Name"]))

            print('Captcha is solving....')
            apiKey = os.getenv("TWOCAPTCHA_API_KEY", "")
            solver = TwoCaptcha(apiKey)
            try:
                SITE_KEY = "0x4AAAAAAAB9SRPPDcY-d2fS"
                result = solver.turnstile(sitekey=SITE_KEY, url="https://clubset.com/private/control/privacy")
                Code=result['code']
                print('Captcha is solve. Code:',Code)
                                
            except Exception as e:
                pass
            
            turnstile_response_element = page.ele("tag:input@@name=cf_captcha_token")
            # turnstile_response_element.set.attr("value", Code)
            page.run_js("arguments[0].value = arguments[1];", turnstile_response_element, Code)
            print(turnstile_response_element)

            submit_button_final = page.ele("tag:button@@text()=Submit Opt Out Request")
            print(submit_button_final)
            submit_button_final.click()

        
        
        try :
            # response = requests.get(sucessConfirmationApi, timeout=10)
            print("Success Confirmation API is sent successfully!")
            sleep(2)
            page.get_screenshot(screenshot_save_path)
        except Exception as e:
            print("Success Confirmation API is failed: ", str(e))
        
    
    except Exception as e:
        try :
            # response = requests.get(errorConfirmationApi, timeout=10)
            print("Error Confirmation API is sent successfully!")
            sleep(2)
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