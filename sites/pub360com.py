from time import sleep
import logging
import os, datetime, pyautogui, requests, sys, random
from cloudsolver.CloudflareBypasser import CloudflareBypasser
from DrissionPage import ChromiumPage, ChromiumOptions
from cloudsolver.extension import proxies
from twocaptcha import TwoCaptcha
from lib.common import generate_email, generate_phone_number
import re

now = datetime.datetime.now()
current_date = now.strftime("%Y-%m-%d")
base_dir = os.getcwd()

screentShotDir = os.path.join(base_dir, "ScreenShot", current_date)
os.makedirs(screentShotDir, exist_ok=True)

def _human_type2(element , text: str) -> None:
    """
    Types in a way reminiscent of a human, with a random delay in between 50ms to 100ms for every character
    :param element: Input element to type text to
    :param text: Input to be typed
    """

    for c in text:
        element.input(c)

        sleep(random.uniform(0.05, 0.1))

def get_chromium_options(arguments: list) -> ChromiumOptions:
    """
    Configures and returns Chromium options.
    
    :param browser_path: Path to the Chromium browser executable.
    :param arguments: List of arguments for the Chromium browser.
    :return: Configured ChromiumOptions instance.
    """
    options = ChromiumOptions()
    # options.set_argument('--auto-open-devtools-for-tabs', 'true') # we don't need this anymore
    for argument in arguments:
        options.set_argument(argument)
    return options

usaStateDictionary = { 'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR', 'California': 'CA', 'Colorado': 'CO', 'Connecticut': 'CT', 'Delaware': 'DE', 'District of Columbia': 'DC', 'Florida': 'FL', 'Georgia': 'GA', 'Hawaii': 'HI', 'Idaho': 'ID', 'Illinois': 'IL', 'Indiana': 'IN', 'Iowa': 'IA', 'Kansas': 'KS', 'Kentucky': 'KY', 'Louisiana': 'LA', 'Maine': 'ME', 'Maryland': 'MD', 'Massachusetts': 'MA', 'Michigan': 'MI', 'Minnesota': 'MN', 'Mississippi': 'MS', 'Missouri': 'MO', 'Montana': 'MT', 'Nebraska': 'NE', 'Nevada': 'NV', 'New Hampshire': 'NH', 'New Jersey': 'NJ', 'New Mexico': 'NM', 'New York': 'NY', 'North Carolina': 'NC', 'North Dakota': 'ND', 'Ohio': 'OH', 'Oklahoma': 'OK', 'Oregon': 'OR', 'Pennsylvania': 'PA', 'Rhode Island': 'RI', 'South Carolina': 'SC', 'South Dakota': 'SD', 'Tennessee': 'TN', 'Texas': 'TX', 'Utah': 'UT', 'Vermont': 'VT', 'Virginia': 'VA', 'Washington': 'WA', 'West Virginia': 'WV', 'Wisconsin': 'WI', 'Wyoming': 'WY' }

def pub360com(dataRow, website_name, in_user_email, run_mode):
    page = None
    
    try :
        fName = dataRow["Name"].split()[0] # split string based on space to get first name
        lName = dataRow["Name"].split()[-1]# split string based on space to get last name
        screenshot_save_path = screentShotDir + "\Pub360Com_" + fName + "-" + lName + ".png"

        sucessConfirmationApi = f"https://privacypros.com/web/dashboard/appendapi.php?website={website_name}&status=1&api=true&email={in_user_email}"
        errorConfirmationApi = f"https://privacypros.com/web/dashboard/appendapi.php?website={website_name}&status=2&api=true&email={in_user_email}"

        arguments = [
            "-no-first-run",
            "--start-maximized",
            "-force-color-profile=srgb",
            "-metrics-recording-only",
            "-password-store=basic",
            "-use-mock-keychain",
            "-export-tagged-pdf",
            "-no-default-browser-check",
            "-disable-background-mode",
            "-enable-features=NetworkService,NetworkServiceInProcess,LoadCryptoTokenExtension,PermuteTLSExtensions",
            "-disable-features=FlashDeprecationWarning,EnablePasswordsAccountStorage",
            "-deny-permission-prompts",
            "-disable-gpu",
            "-accept-lang=en-US",
        ]
        
        options = get_chromium_options(arguments)
        options.auto_port()

        if run_mode == 'headless':
            options.headless()

        page = ChromiumPage(addr_or_opts=options)
        url="https://pub360.com/control/privacy"
        page.get(url)

        cnt = 0

        while True:
            cnt = cnt + 1
            if cnt > 20 : 
                break
            page_title = page.title
            if "just a moment" in page_title.lower() :
                page.actions.click()
                page.actions.key_down("TAB")
                sleep(0.2)
                page.actions.key_up("TAB")
                sleep(0.2)

                page.actions.key_down("SPACE")
                sleep(0.2)
                page.actions.key_up("SPACE")

                sleep(1.0)
                print("Cloudflare solving...")
            else :
                break


        fullName_input = page.ele("tag:input@@id=topsearch")
        fullName_input.click()
        sleep(random.uniform(0.1, 0.5))
        _human_type2(fullName_input, dataRow["Name"])

        city_state = dataRow["City"] + ", " + __import__("lib.broker_helpers", fromlist=["state_abbrev"]).state_abbrev(dataRow["State"])
        city_state_input = page.ele("tag:input@@id=city_state")
        city_state_input.click()
        sleep(random.uniform(0.1, 0.5))
        _human_type2(city_state_input, city_state)        

        form_container = page.ele("tag:form@@id=peoplesearch")
        page.run_js("arguments[0].submit();", form_container)

        sleep(10)

        current_year = now.year
        birth_year = dataRow["Birth Year"]
        age = current_year - birth_year

        search_items = page.eles("tag:div@@class=search-item")
        profile_url = ""


        if len(search_items) > 0 :
            profile_url = search_items[0].ele("tag:a").attr("href")
            page.get("https://pub360.com/control/privacy")
            url_input = page.ele("tag:input@@id=url")
            url_input.click()
            sleep(random.uniform(0.1, 0.5))
            _human_type2(url_input, profile_url)

            fullName_input = page.ele("tag:input@@id=user_name")
            fullName_input.click()
            sleep(random.uniform(0.1, 0.5))
            _human_type2(fullName_input, dataRow["Name"])

            email_input = page.ele("tag:input@@id=user_email")
            email_input.click()
            sleep(random.uniform(0.1, 0.5))
            _human_type2(email_input, generate_email(dataRow["Name"]))

            apiKey = os.getenv("TWOCAPTCHA_API_KEY", "")
            solver = TwoCaptcha(apiKey)
            print("Captcha is solving...")
            try :
                site_url = "https://pub360.com/control/privacy"
                site_key = "0x4AAAAAAAB9ONRjrYbRzDWO"
                result = solver.turnstile(site_key, site_url)
                Code = result["code"]
                print("Captcha is solved.")
            except Exception as e:
                print("Error: ", str(e))

            token_input1 = page.ele("tag:input@@name=cf-turnstile-response")
            page.run_js("arguments[0].value=arguments[1];", token_input1, Code)

            token_input2 = page.ele("tag:input@@name=g-recaptcha-response")
            page.run_js("arguments[0].value=arguments[1];", token_input2, Code)

            submit_btn = page.ele("tag:button@@text()=Submit Opt Out Request")
            submit_btn.click()  

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
        raise

    finally:
        if page is not None:
            try:
                page.quit()
            except Exception:
                pass

    return screenshot_save_path
