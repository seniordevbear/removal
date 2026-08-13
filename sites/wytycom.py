from DrissionPage import ChromiumPage, ChromiumOptions
from time import sleep
import json
import random
import os, datetime, pyautogui, sys, requests
from twocaptcha import TwoCaptcha
from lib.common import generate_email, generate_phone_number

now = datetime.datetime.now()
current_date = now.strftime("%Y-%m-%d")
base_dir = os.getcwd()

screentShotDir = os.path.join(base_dir, "ScreenShot", current_date)

print(screentShotDir)

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
    fName = dataRow["Name"].split()[0] # split string based on space to get first name
    lName = dataRow["Name"].split()[-1]# split string based on space to get last name

    sleep(1)
    
    email_input = page.ele("tag:input@@id=content_txtEmailAddr")
    email_input.click()
    print("typing the email...")
    sleep(random.uniform(0.1,0.5))
    _human_type2(email_input, generate_email(dataRow["Name"]))

    fName_input = page.ele("tag:input@@id=content_txtFrstNm")
    fName_input.click()
    print("typing the first name...")
    sleep(random.uniform(0.1,0.5))
    _human_type2(fName_input, fName)


    lName_input = page.ele("tag:input@@id=content_tlastn")
    lName_input.click()
    print("typing the last name...")
    sleep(random.uniform(0.1,0.5))
    _human_type2(lName_input, lName)

    address_input = page.ele("tag:input@@id=content_txtStreetAddress")
    address_input.click()
    sleep(random.uniform(0.1,0.5))
    _human_type2(address_input, dataRow["Address"])

    city_input = page.ele("tag:input@@id=content_city")
    city_input.click()
    sleep(random.uniform(0.1,0.5))
    _human_type2(city_input, dataRow["City"])

    state_select = page.ele("tag:select@@id=ddlAddressState")
    state_select.select.by_text(usaStateDictionary[dataRow["State"]])

    phone_input = page.ele("tag:input@@id=content_txtPhoneNum")
    phone_input.click()
    sleep(random.uniform(0.1,0.5))
    _human_type2(phone_input, generate_phone_number())

def wytycom(dataRow, website_name, in_user_email, run_mode) : 
    try : 
        fName = dataRow["Name"].split()[0] # split string based on space to get first name
        lName = dataRow["Name"].split()[-1]# split string based on space to get last name
        screenshot_save_path = screentShotDir + "\WytyCom_" + fName + "-" + lName + ".png"
        
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
        #Launch Website
        page = ChromiumPage(addr_or_opts=options)
        page.get("https://www.wyty.com/remove/")

        fill_input_data(page, dataRow)

        apiKey = os.getenv("TWOCAPTCHA_API_KEY", "")
        site_key = "4ce16fe2-051d-47a7-9028-abd453e48b52"
        url = "https://www.wyty.com/remove/"

        solver = TwoCaptcha(apiKey)

        print("hCaptcha is solving.....")
        try:
            result = solver.hcaptcha(sitekey=site_key, url=url)
            Code = result['code']
            # print(result)
            print("Captcha is solved")
            print(result)
        except Exception as e:
            print(e)

        captcha_iframe = page.ele("tag:iframe@@title=Widget containing checkbox for hCaptcha security challenge")

        #captcha_iframe.set.attr("data-hcaptcha-response", Code)

        div_container = page.ele("tag:div@@class=h-captcha")

        #print(div_container)

        g_textarea = div_container.ele("tag:textarea@@name=g-recaptcha-response")

        #print(g_textarea)
        # g_textarea.set.attr("value", Code)
        g_textarea.set.innerHTML(Code)

        h_textarea = div_container.ele("tag:textarea@@name=h-captcha-response")
        # h_textarea.set.attr("value", Code)
        h_textarea.set.innerHTML(Code)


        Image = page.ele("tag:img@@id=content_ImageCaptcha")
        Image.get_screenshot("captcha.png")

        print('ImageCaptcha is solving....')
        try:
            result = solver.normal('captcha.png')
            #   print(result)
            Code1=result['code']
            print('Captcha is solve. Code:',Code1)

        except Exception as e:
            print(e)

        verify_input = page.ele("tag:input@@id=content_txtCaptchaValidateNumber")
        verify_input.click()
        _human_type2(verify_input, Code1)

        submit_button = page.ele("tag:input@@id=content_btnSave")

        sleep(random.uniform(0.1, 0.5))
        submit_button.run_js("this.click()")

        
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