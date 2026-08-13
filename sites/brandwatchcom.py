from DrissionPage import ChromiumPage, ChromiumOptions
from time import sleep
from DrissionPage.common import Keys
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

def fill_input_data(page, dataRow) : 
    
    request_type = page.ele("tag:div@@data-test=portal-input-0")
    request_type.click()

    react_select_input_2 = page.ele("tag:input@@id=react-select-2-input")
    print(react_select_input_2)
    _human_type2(react_select_input_2, "Erasure")
    react_select_input_2.input(Keys.ENTER)

    name_input = page.ele("tag:input@@data-test=portal-input-1")
    name_input.click()
    print("typing the last name...")
    sleep(random.uniform(0.1,0.5))
    _human_type2(name_input, dataRow["Name"])

    email_input = page.ele("tag:input@@data-test=portal-input-2")
    email_input.click()
    print("typing the email...")
    sleep(random.uniform(0.1,0.5))
    _human_type2(email_input, generate_email(dataRow["Name"]))

    phone_input = page.ele("tag:input@@name=phone")
    phone_input.clear()
    phone_input.click()
    sleep(random.uniform(0.1,0.5))
    _human_type2(phone_input, f"1{dataRow["Phone Number"]}")

    country_select = page.ele("tag:div@@data-test=portal-input-4")
    country_select.click()

    react_select_input_3 = page.ele("tag:input@@id=react-select-3-input")
    print(react_select_input_3)
    _human_type2(react_select_input_3, "United States")
    react_select_input_3.input(Keys.ENTER)
    
    relation_div = page.ele("tag:div@@data-test=portal-input-5")
    relation_div.click()

    react_select_input_4 = page.ele("tag:input@@id=react-select-4-input")
    print(react_select_input_4)
    _human_type2(react_select_input_4, "Customer")
    react_select_input_4.input(Keys.ENTER)

    page.actions.click()

    sleep(random.uniform(1, 2))

    while True :
        regenerate_btn = page.ele("tag:button@@text()=Regenerate captcha image")
        regenerate_btn.click()
        sleep(2)

        api_key = os.getenv("TWOCAPTCHA_API_KEY", "")
        solver = TwoCaptcha(api_key)
        
        Image = page.ele("tag:img@@class=captcha__image")
        Image.get_screenshot("captcha.png")

        # Captcha solver part
        print('Captcha is solving....')
        try:
            result = solver.normal('captcha.png')
        #   print(result)
            Code=result['code']
            print('Captcha is solve. Code:',Code)

        except Exception as e:
            pass

        #Input code
        code=page.ele('tag:input@@data-test=captchaInput')
        code.click()
        sleep(random.uniform(0.1,0.3))
        _human_type2(code,Code)
        # code.input(Keys.ENTER)

        sleep(1)
        
        submit_button = page.ele("tag:button@@text()=Submit request")
        submit_button.click()

        sleep(3)

        error_msg = page.ele("tag:h4@@text()=Captcha error")
        if error_msg == None :
            break
       
            
        
def brandwatchcom(dataRow, website_name, in_user_email, run_mode) : 
    try : 
        sucessConfirmationApi = f"https://privacypros.com/web/dashboard/appendapi.php?website={website_name}&status=1&api=true&email={in_user_email}"
        errorConfirmationApi = f"https://privacypros.com/web/dashboard/appendapi.php?website={website_name}&status=2&api=true&email={in_user_email}"

        fName = dataRow["Name"].split()[0] # split string based on space to get first name
        lName = dataRow["Name"].split()[-1]# split string based on space to get last name
        screenshot_save_path = screentShotDir + "\BrandwatchCom_" + fName + "-" + lName + ".png"
        
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
        page.get("https://www.brandwatch.com/p/legal-data/")

        fill_input_data(page, dataRow)

        sleep(random.uniform(0.5, 1))


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