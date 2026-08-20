from DrissionPage import ChromiumPage, ChromiumOptions
from time import sleep
import random
import os, datetime, pyautogui, sys, requests
from twocaptcha import TwoCaptcha
from lib.common import generate_email, generate_phone_number

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

def make_standard (num) :
    ret = str(num)
    if len(ret) < 2 : ret = "0" + ret

    return ret 

def fill_input_data(page, dataRow) : 
    
    fName = dataRow["Name"].split()[0] # split string based on space to get first name
    lName = dataRow["Name"].split()[-1]# split string based on space to get last name
    
    form_container = page.ele("tag:form@@id=wf-form-Opt-out-form")

    first_name = form_container.ele("tag:input@@id=First-Name")
    first_name.clear()
    first_name.click()
    _human_type2(first_name, fName)

    last_name = form_container.ele("tag:input@@id=Last-Name-2")
    last_name.clear()
    last_name.click()
    _human_type2(last_name, lName)

    email_input = form_container.ele("tag:input@@id=Email-2")
    email_input.clear()
    email_input.click()
    _human_type2(email_input, generate_email(dataRow["Name"]))

    linkedin_profileurl = "https://www.linkedin.com/in/" + fName + "_" + lName
    linkedin_input = form_container.ele("tag:input@@id=Professional-profile-URL")
    linkedin_input.clear()
    linkedin_input.click()
    _human_type2(linkedin_input, linkedin_profileurl)

    confirm_status = form_container.ele("tag:span@@text()=U.S. resident")
    print(confirm_status)
    confirm_status.click()

    sleep(1)

    request_type = form_container.ele("tag:span@@text()=Request to delete personal information collected ")
    request_type.click()

    sleep(1)

    confirm_person = form_container.ele("tag:span@@for=I-am-the-person")
    confirm_person.click()
    sleep(1)
    checkbox_element = form_container.ele("tag:span@@for=Contact-consent")
    checkbox_element.click()

def coresignalcom(dataRow, website_name, in_user_email, run_mode) : 
    page = None
    try : 
        sucessConfirmationApi = f"https://privacypros.com/web/dashboard/appendapi.php?website={website_name}&status=1&api=true&email={in_user_email}"
        errorConfirmationApi = f"https://privacypros.com/web/dashboard/appendapi.php?website={website_name}&status=2&api=true&email={in_user_email}"

        fName = dataRow["Name"].split()[0] # split string based on space to get first name
        lName = dataRow["Name"].split()[-1]# split string based on space to get last name
        screenshot_save_path = screentShotDir + "\CoresignalCom_" + fName + "-" + lName + ".png"

        arguments = [
            "-no-first-run",
            "--start-maximized",
            "-disable-javascript",
            "-disable-gpu",
            "-disable-sensors",
        ]

        options = get_chromium_options(arguments).auto_port().add_extension("capsolver")

        if run_mode == "headless" :
            options.headless()
        
        #Launch Website
        page = ChromiumPage(addr_or_opts=options)
        # page.load_mode=None
        page.get("https://coresignal.com/privacy-rights/")

        fill_input_data(page, dataRow)

        sleep(random.uniform(0.5, 1))

        print('Captcha is solving....')

        try:
            SITE_KEY = "0x4AAAAAAAyY7wPzND4h_IXy"
            result = solver.turnstile(sitekey=SITE_KEY, url="https://coresignal.com/privacy-rights/")
            Code=result['code']
            print('Captcha is solve. Code:',Code)

            captcha_widget_div = page.ele("tag:div@@data-theme=light")
            print(captcha_widget_div)
            div_element = captcha_widget_div.children()[0]
            turnstile_response_element = div_element.ele("tag:input@@name=cf-turnstile-response")
            page.run_js("arguments[0].value = arguments[1];", turnstile_response_element, Code)
            sleep(1)

            success_msg = page.ele("tag:div@@id=opt-out-success-message")
            success_msg.set.style("display", "block")

            error_msg = page.ele("tag:div@@id=opt-out-error-message")
            error_msg.set.style("display", "none")

            # form_container = page.ele("tag:form@@id=wf-form-Opt-out-form")

            # submit_button = form_container.ele("tag:input@@id=submit-opt-out-form")
            # print(submit_button)
            # submit_button.run_js("this.click();")

            # page.run_js("""
            #         return submitOptOutForm({
            #             name: document.getElementById("First-Name").value,
            #             surname: document.getElementById("Last-Name-2").value,
            #             email: document.getElementById("Email-2").value,
            #             profileUrl: document.getElementById("Professional-profile-URL").value,
            #             residentStatus: document.querySelector('input[name="Location"]:checked').value,
            #             requestType: document.querySelector('input[name="Type"]:checked').value,
            #             identityConfirmation: document.querySelector('input[name="Third"]:checked').value,
            #             hasConsent: document.getElementById("Contact-consent").checked,
            #             recaptchaToken:  arguments[0]  // Replace this if needed
            #         });
            #     """, Code)

        except Exception as e:
            pass

        sleep(0.3)

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