from DrissionPage import ChromiumPage, ChromiumOptions
from time import sleep
import random
import os, datetime, pyautogui, requests
from lib.common import generate_email, generate_phone_number

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

def format_phone_number(phone_number: str) -> str:
    """Formats a 10-digit phone number as XXX-XXX-XXXX."""
    if len(phone_number) == 10 and phone_number.isdigit():
        return f"{phone_number[:3]}-{phone_number[3:6]}-{phone_number[6:]}"
    else:
        return "Invalid phone number"

def fill_input_data(page, dataRow) : 
        
    fName = dataRow["Name"].split()[0] # split string based on space to get first name
    lName = dataRow["Name"].split()[-1]# split string based on space to get last name

    fName_input = page.ele("tag:input@@id=OptoutFirstName")
    fName_input.click()
    print("typing the first name...")
    sleep(random.uniform(0.1,0.5))
    _human_type2(fName_input, fName)

    lName_input = page.ele("tag:input@@id=OptoutLastName")
    lName_input.click()
    print("typing the last name...")
    sleep(random.uniform(0.1,0.5))
    _human_type2(lName_input, lName)
    
    address_input = page.ele("tag:input@@id=OptoutAddress")
    address_input.click()
    sleep(random.uniform(0.1,0.5))
    _human_type2(address_input, dataRow["Address"])

    city_input = page.ele("tag:input@@id=OptoutCity")
    city_input.click()
    sleep(random.uniform(0.1,0.5))
    _human_type2(city_input, dataRow["City"])
    
    state_select = page.ele("tag:select@@id=OptoutRegion")
    state_select.select.by_value(__import__("lib.broker_helpers", fromlist=["state_abbrev"]).state_abbrev(dataRow["State"]))
    
    zip_input = page.ele("tag:input@@id=OptoutPostalCode")
    zip_input.click()
    sleep(random.uniform(0.1,0.5))
    _human_type2(zip_input, str(dataRow["Zipcode"]))

    phone_input = page.ele("tag:input@@id=OptoutPhoneNumber")
    phone_input.click()
    sleep(random.uniform(0.1,0.5))
    _human_type2(phone_input, format_phone_number(dataRow["Phone Number"]))

    email_str = generate_email(dataRow["Name"])
    email_input = page.ele("tag:input@@id=OptoutEmail")
    email_input.click()
    sleep(random.uniform(0.1,0.5))
    _human_type2(email_input, email_str)

    your_fName_input = page.ele("tag:input@@id=FirstName")
    your_fName_input.click()
    print("typing the first name...")
    sleep(random.uniform(0.1,0.5))
    _human_type2(your_fName_input, fName)

    your_lName_input = page.ele("tag:input@@id=LastName")
    your_lName_input.click()
    print("typing the last name...")
    sleep(random.uniform(0.1,0.5))
    _human_type2(your_lName_input, lName)

    your_email_input = page.ele("tag:input@@id=Email")
    your_email_input.click()
    sleep(random.uniform(0.1,0.5))
    _human_type2(your_email_input, email_str)

    your_email_confirm_input = page.ele("tag:input@@id=EmailConfirm")
    your_email_confirm_input.click()
    sleep(random.uniform(0.1,0.5))
    _human_type2(your_email_confirm_input, email_str)

    addtional_textarea = page.ele("tag:textarea@@id=Reason")
    addtional_textarea.input("I want to remove my information.")

    checkbox = page.ele("tag:input@@id=AgreeToOptoutPolicy")
    checkbox.click()

def archivescom(dataRow, website_name, in_user_email, run_mode) : 
    page = None
    try : 
        sucessConfirmationApi = f"https://privacypros.com/web/dashboard/appendapi.php?website={website_name}&status=1&api=true&email={in_user_email}"
        errorConfirmationApi = f"https://privacypros.com/web/dashboard/appendapi.php?website={website_name}&status=2&api=true&email={in_user_email}"

        fName = dataRow["Name"].split()[0] # split string based on space to get first name
        lName = dataRow["Name"].split()[-1]# split string based on space to get last name

        screenshot_save_path = screentShotDir + "\AchivesCom_" + fName + "-" + lName + ".png"

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
        page.get("https://www.archives.com/optout")
        
        sleep(random.uniform(1, 2))

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

        fill_input_data(page, dataRow)
        
        submit_button = page.ele("tag:input@@id=submit_btn")
        submit_button.click()


        try :
            # response = requests.get(sucessConfirmationApi, timeout=10)
            print("Success Confirmation API is sent successfully!: ")
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