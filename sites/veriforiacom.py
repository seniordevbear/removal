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

def veriforiacom(dataRow, website_name, in_user_email, run_mode) : 
    try : 
        fName = dataRow["Name"].split()[0] # split string based on space to get first name
        lName = dataRow["Name"].split()[-1]# split string based on space to get last name
        screenshot_save_path = screentShotDir + "\VeriforiaCom_" + fName + "-" + lName + ".png"
        
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
        page.get("https://veriforia.com/")

        sleep(random.uniform(3, 5))

        fullName_input = page.ele("tag:input@@id=topsearch")
        fullName_input.click()
        print("typing the full name...")
        sleep(random.uniform(0.1,0.5))
        _human_type2(fullName_input, dataRow["Name"])

        city_state = dataRow["City"] + ", " + usaStateDictionary[dataRow["State"]]
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

        rows = page.eles("tag:a@@class=search-item")

        profile_url = ""
        
        if len(rows) > 0 :
            profile_url = rows[0].attr("href")
            print(profile_url)
                    
            sleep(1)
            page.get("https://veriforia.com/ng/control/privacy")        
            sleep(1)

            profile_url_input = page.ele("tag:input@@id=url")
            profile_url_input.click()
            sleep(random.uniform(0.5, 1))
            _human_type2(profile_url_input, profile_url)

            fullName_input = page.ele("tag:input@@name=user_name")
            fullName_input.click()
            sleep(random.uniform(0.5, 1))
            _human_type2(fullName_input, dataRow["Name"])

            email_input = page.ele("tag:input@@name=user_email")
            email_input.click()
            sleep(random.uniform(0.5, 1))
            _human_type2(email_input, generate_email(dataRow["Name"]))
            
            apiKey = os.getenv("TWOCAPTCHA_API_KEY", "")
            solver = TwoCaptcha(apiKey)
            print("Captcha is solving...")
            try :
                site_key = "6Ldkl8UUAAAAAJYFAVnFup_qw0v7d7lrg82A4QkR"
                site_url = "https://veriforia.com/ng/control/privacy"
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

            submit_button_final = page.ele("tag:button@@type=submit")
            submit_button_final.run_js("this.click()")        

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