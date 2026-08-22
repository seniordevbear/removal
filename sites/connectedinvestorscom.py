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

def format_phone_number(phone):
    # Ensure the input is a string and has 10 digits
    if len(phone) == 10 and phone.isdigit():
        return f"{phone[:3]}-{phone[3:6]}-{phone[6:]}"
    else:
        raise ValueError("Phone number must be a 10-digit numeric string")

def fill_input_data(page, dataRow) : 
    
    fName = dataRow["Name"].split()[0] # split string based on space to get first name
    lName = dataRow["Name"].split()[-1]# split string based on space to get last name 

    state_element = page.ele("tag:select@@id=IO:487e72cedb3e3158665f18281396196a")
    state_element.select.by_text(__import__("lib.broker_helpers", fromlist=["state_abbrev"]).state_abbrev(dataRow["State"]))
    
    owner_element = page.ele("tag:select@@id=IO:c87e72cedb3e3158665f182813961952")
    owner_element.select.by_text("Self (Consumer)")

    fName_input = page.ele("tag:input@@name=IO:4e6e32cedb3e3158665f18281396191b")
    fName_input.click()
    print("typing the first name...")
    sleep(random.uniform(0.1,0.5))
    _human_type2(fName_input, fName)


    lName_input = page.ele("tag:input@@name=IO:197eb2cedb3e3158665f1828139619cb")
    lName_input.click()
    print("typing the last name...")
    sleep(random.uniform(0.1,0.5))
    _human_type2(lName_input, lName)

    email_input = page.ele("tag:input@@name=IO:31f7978edbfe3158665f1828139619f5")
    email_input.click()
    print("typing the email...")
    sleep(random.uniform(0.1,0.5))
    _human_type2(email_input, generate_email(dataRow["Name"]))
    
    address_input = page.ele("tag:input@@name=IO:3c7eb2cedb3e3158665f18281396193d")
    address_input.click()
    sleep(random.uniform(0.1,0.5))
    _human_type2(address_input, dataRow["Address"])

    city_input = page.ele("tag:input@@name=IO:0e6e32cedb3e3158665f182813961913")
    city_input.click()
    sleep(random.uniform(0.1,0.5))
    _human_type2(city_input, dataRow["City"])

    zip_input = page.ele("tag:input@@name=IO:926e32cedb3e3158665f182813961930")
    zip_input.click()
    sleep(random.uniform(0.1,0.5))
    _human_type2(zip_input, str(dataRow["Zipcode"]))

    phone_input = page.ele("tag:input@@name=IO:8e4685ee47f28a1011739f78536d431c")
    phone_input.click()
    sleep(random.uniform(0.1,0.5))
    _human_type2(phone_input, format_phone_number(generate_phone_number()))

    label_element = page.ele("tag:label@@id=ni.IO:d97eb2cedb3e3158665f18281396198b_label")
    label_element.click()
    
def connectedinvestorscom(dataRow, website_name, in_user_email, run_mode) : 
    page = None
    try : 
        sucessConfirmationApi = f"https://privacypros.com/web/dashboard/appendapi.php?website={website_name}&status=1&api=true&email={in_user_email}"
        errorConfirmationApi = f"https://privacypros.com/web/dashboard/appendapi.php?website={website_name}&status=2&api=true&email={in_user_email}"

        fName = dataRow["Name"].split()[0] # split string based on space to get first name
        lName = dataRow["Name"].split()[-1]# split string based on space to get last name 
        screenshot_save_path = screentShotDir + "\ConnectedInvestorsCom_" + fName + "-" + lName + ".png"
        
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
        page = ChromiumPage()
        page.get("https://firstam.service-now.com/x_farf2_dp_request_ci_opt_out.do?sysparm_id=6d6e7e8edb3e3158665f182813961985")

        sleep(random.uniform(3, 5))

        fill_input_data(page, dataRow)

        sleep(7)

        submit_button = page.ele("tag:button@@id=submit_button")
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