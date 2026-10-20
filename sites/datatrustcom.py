from DrissionPage import ChromiumPage, ChromiumOptions
from time import sleep
import json
import random
import os, datetime, pyautogui, sys, requests
from twocaptcha import TwoCaptcha
from lib.common import generate_email, generate_phone_number
from lib.email_verification import do_email_verification
from cloudsolver.extension import proxies
from lib.broker_helpers import select_onetrust_state
from lib.broker_helpers import unique_shot_path, fill_field, submission_verdict

api_key = os.getenv("TWOCAPTCHA_API_KEY", "")
solver = TwoCaptcha(api_key)

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

def make_standard (num) :
    ret = str(num)
    if len(ret) < 2 : ret = "0" + ret

    return ret 

def fill_input_data(page, dataRow):
    """Fill Data Trust's privacy-rights form.

    Rebuilt from the 2026-10-19 capture plus a fetch of /your-privacy-choices/
    on 20 Oct. The script used to open /do-not-sell-my-personal-information/
    (now a redirect to the privacy policy) and look for a OneTrust iframe with
    *DSARElement ids; the site runs Gravity Forms now. Form gform_5 has three
    visible fields - input_5_2_3 (first name), input_5_2_6 (last name),
    input_5_1 (e-mail, required) - and an invisible reCAPTCHA Enterprise
    (sitekey 6Lc0uM4t..., token textarea g-recaptcha-response-100000).
    """
    fName = dataRow["Name"].split()[0]
    lName = dataRow["Name"].split()[-1]
    broker = "datatrustcom"
    form = page.ele("css:form#gform_5", timeout=20)
    if not form:
        raise RuntimeError("datatrustcom: gform_5 not on /your-privacy-choices/ (form changed); needs a capture")
    fill_field(form, "css:input#input_5_2_3", fName, broker=broker)
    fill_field(form, "css:input#input_5_2_6", lName, broker=broker)
    fill_field(form, "css:input#input_5_1", generate_email(dataRow["Name"]), broker=broker)
    return form


def datatrustcom(dataRow, website_name, in_user_email, run_mode) : 
    page = None
    try : 
        sucessConfirmationApi = f"https://privacypros.com/web/dashboard/appendapi.php?website={website_name}&status=1&api=true&email={in_user_email}"
        errorConfirmationApi = f"https://privacypros.com/web/dashboard/appendapi.php?website={website_name}&status=2&api=true&email={in_user_email}"
        fName = dataRow["Name"].split()[0] # split string based on space to get first name
        lName = dataRow["Name"].split()[-1]# split string based on space to get last name

        screenshot_save_path = unique_shot_path(screentShotDir, "DatatrustCom", fName, lName)

        arguments = [
            "-no-first-run",
            "--start-maximized",
            # "--incognito",
            "-disable-javascript",
            "-disable-gpu",
            "-disable-sensors",
        ]

        port_arr = [
            "10001",
            "10002",
            "10003",
            "10004",
            "10005",
            "10006",
            "10007",
            "10008",
            "10009",
            "10010"
        ]

        random_number = random.randint(0, 9)

        username = os.getenv("SMARTPROXY_USER", "")
        password = os.getenv("SMARTPROXY_PASSWORD", "")
        endpoint = os.getenv("SMARTPROXY_ENDPOINT", "isp.smartproxy.com")
        port = port_arr[random_number]

        proxy_extension = proxies(username, password, endpoint, port)

        options = get_chromium_options(arguments).auto_port().add_extension("extension")

        if run_mode == "headless" :
            options.headless()

        #Launch Website
        page = ChromiumPage(addr_or_opts=options)
        # page.load_mode=None
        # 20 Oct 2026: the do-not-sell path redirects to the privacy policy;
        # the rights form lives on /your-privacy-choices/.
        page.get("https://thedatatrust.com/your-privacy-choices/")
        sleep(random.uniform(2, 3))
        form = fill_input_data(page, dataRow)
        sleep(1)

        # Invisible reCAPTCHA Enterprise (Gravity Forms add-on). Solve it off-page
        # and drop the token into the hidden textarea the plugin reads.
        apiKey = os.getenv("TWOCAPTCHA_API_KEY", "")
        solver = TwoCaptcha(apiKey)
        print("Captcha is solving...")
        try:
            result = solver.recaptcha(sitekey="6Lc0uM4tAAAAAFFEy0tF8Z0YQN1dAZwmwIzZbuwd",
                                      url="https://thedatatrust.com/your-privacy-choices/",
                                      enterprise=1, invisible=1)
            Code = result["code"]
        except Exception as e:
            raise RuntimeError("datatrustcom: captcha not solved: %s" % e)
        page.run_js(
            "var t=arguments[0];"
            "document.querySelectorAll(\"textarea[name='g-recaptcha-response']\")"
            ".forEach(function(e){e.style.display='block';e.value=t;});", Code)
        sleep(random.uniform(0.5, 1))
        submit_button = form.ele("css:#gform_submit_button_5", timeout=6)
        if not submit_button:
            raise RuntimeError("datatrustcom: gform_submit_button_5 not found")
        submit_button.click()
        # Gravity Forms swaps the form for .gform_confirmation_message on success
        # and shows .gfield_error / .validation_error on rejection.
        submission_verdict(page, "datatrustcom", success_phrases=(
            "thank you", "received", "submitted"), timeout=20)
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