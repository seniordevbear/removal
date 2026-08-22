from time import sleep
import os, datetime, pyautogui, requests, sys, random
from cloudsolver.CloudflareBypasser import CloudflareBypasser
from DrissionPage import ChromiumPage, ChromiumOptions
from cloudsolver.extension import proxies
from twocaptcha import TwoCaptcha
from lib.common import generate_email, generate_phone_number
from DrissionPage.common import Keys
from lib.email_verification import do_email_verification

now = datetime.datetime.now()
current_date = now.strftime("%Y-%m-%d")
base_dir = os.getcwd()

screentShotDir = os.path.join(base_dir, "ScreenShot", current_date)
os.makedirs(screentShotDir, exist_ok=True)

usaStateDictionary = { 'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR', 'California': 'CA', 'Colorado': 'CO', 'Connecticut': 'CT', 'Delaware': 'DE', 'District of Columbia': 'DC', 'Florida': 'FL', 'Georgia': 'GA', 'Hawaii': 'HI', 'Idaho': 'ID', 'Illinois': 'IL', 'Indiana': 'IN', 'Iowa': 'IA', 'Kansas': 'KS', 'Kentucky': 'KY', 'Louisiana': 'LA', 'Maine': 'ME', 'Maryland': 'MD', 'Massachusetts': 'MA', 'Michigan': 'MI', 'Minnesota': 'MN', 'Mississippi': 'MS', 'Missouri': 'MO', 'Montana': 'MT', 'Nebraska': 'NE', 'Nevada': 'NV', 'New Hampshire': 'NH', 'New Jersey': 'NJ', 'New Mexico': 'NM', 'New York': 'NY', 'North Carolina': 'NC', 'North Dakota': 'ND', 'Ohio': 'OH', 'Oklahoma': 'OK', 'Oregon': 'OR', 'Pennsylvania': 'PA', 'Rhode Island': 'RI', 'South Carolina': 'SC', 'South Dakota': 'SD', 'Tennessee': 'TN', 'Texas': 'TX', 'Utah': 'UT', 'Vermont': 'VT', 'Virginia': 'VA', 'Washington': 'WA', 'West Virginia': 'WV', 'Wisconsin': 'WI', 'Wyoming': 'WY' }

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

def fastbackgroundcheckcom(dataRow, website_name, in_user_email, run_mode):
    page = None
    
    try :
        fName = dataRow["Name"].split()[0] # split string based on space to get first name
        lName = dataRow["Name"].split()[-1]# split string based on space to get last name
        sucessConfirmationApi = f"https://privacypros.com/web/dashboard/appendapi.php?website={website_name}&status=1&api=true&email={in_user_email}"
        errorConfirmationApi = f"https://privacypros.com/web/dashboard/appendapi.php?website={website_name}&status=2&api=true&email={in_user_email}"
        screenshot_save_path = screentShotDir + "\FastbackgroundcheckCom_" + fName + "-" + lName + ".png"

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
        options.add_extension("adblock")
        options.auto_port()

        if run_mode == 'headless':
            options.headless()
            
        page = ChromiumPage(addr_or_opts=options)
        url="https://www.fastbackgroundcheck.com/opt-out"
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

        page.wait.ele_displayed("tag:input@@id=email")
        email_input = page.ele("tag:input@@id=email")
        email_input.click()
        sleep(0.5)
        email_input.input(generate_email(dataRow["Name"]))
        
        agree_checkbox = page.ele("tag:input@@id=agreement-checkbox")
        agree_checkbox.click()

        apiKey = os.getenv("TWOCAPTCHA_API_KEY", "")
        solver = TwoCaptcha(apiKey)
        print("Captcha is solving...")
        try :
            site_key = "6LdTeZYeAAAAAG_xtOv3t8EA2MGJiGVr6xKwo15c"
            site_url = "https://www.fastbackgroundcheck.com/opt-out"
            result = solver.recaptcha(site_key, site_url)
            print("Captcha is solved.")
            print(result["code"])
            Code = result["code"]
        except Exception as e:
            print("Error: ", str(e))


        page.wait.ele_displayed("tag:iframe@@title=reCAPTCHA")
        sleep(1)
        iframe_container = page.ele("tag:iframe@@title=reCAPTCHA")
        recaptcha_input_token = iframe_container.ele("tag:input@@id=recaptcha-token")
        recaptcha_input_token.set.attr("value", Code)

        textarea_token = page.ele("tag:textarea@@id=g-recaptcha-response")
        textarea_token.set.innerHTML(Code)

        iframe_container1 = page.ele("tag:iframe@@title=recaptcha challenge expires in two minutes")
        recaptcha_input_token1 = iframe_container1.ele("tag:input@@id=recaptcha-token")
        recaptcha_input_token1.set.attr("value", Code)

        sleep(2)

        begin_btn = page.ele("tag:button@@text()=Begin Removal Process")
        begin_btn.click()      

        sleep(2)
        
        fullName_input = page.ele("tag:input@@id=search-input-name")
        fullName_input.click()
        sleep(random.uniform(0.1, 0.5))
        _human_type2(fullName_input, dataRow["Name"])
        fullName_input.input(Keys.TAB)

        city_state = dataRow["City"] + ", " + __import__("lib.broker_helpers", fromlist=["state_abbrev"]).state_abbrev(dataRow["State"])
        city_state_input = page.ele("tag:input@@id=search-input-name-address2")

        sleep(random.uniform(0.1, 0.5))
        _human_type2(city_state_input, city_state)

        sleep(1)
        free_search_btn = page.ele("tag:button@@id=search-submit-btn")
        free_search_btn.click()   
        
        sleep(5)

        ol_container = page.ele("tag:ol@@class=people-list-container")
        print(ol_container)
        people_list_container = ol_container.eles("tag:li@@class:person-container")

        print(len(people_list_container))
        if len(people_list_container) > 0 :
            free_public_records_btn = people_list_container[0].ele("tag:a@@text()=Free Public Records")
            print(free_public_records_btn)
            free_public_records_btn.click()
          
            sleep(1)
            remove_btn = page.ele("tag:a@@id=record-removal-link")
            print(remove_btn)
            remove_btn.click()

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
