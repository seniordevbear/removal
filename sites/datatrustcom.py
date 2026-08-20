from DrissionPage import ChromiumPage, ChromiumOptions
from time import sleep
import json
import random
import os, datetime, pyautogui, sys, requests
from twocaptcha import TwoCaptcha
from lib.common import generate_email, generate_phone_number
from lib.email_verification import do_email_verification
from cloudsolver.extension import proxies

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

def fill_input_data(page, dataRow) : 
    
    fName = dataRow["Name"].split()[0] # split string based on space to get first name
    lName = dataRow["Name"].split()[-1]# split string based on space to get last name
    
    div_container = page.ele("#ajax-content-wrap")
    print(div_container)
    iframe_container = div_container.ele("tag:iframe")
    print(iframe_container)
    

    request_type = iframe_container.ele("tag:span@@text()= Right to Delete ")
    request_type.click()

    fName_input = iframe_container.ele("tag:input@@id=firstNameDSARElement")
    fName_input.click()
    print("typing the first name...")
    sleep(random.uniform(0.1,0.5))
    _human_type2(fName_input, fName)


    lName_input = iframe_container.ele("tag:input@@id=lastNameDSARElement")
    lName_input.click()
    print("typing the last name...")
    sleep(random.uniform(0.1,0.5))
    _human_type2(lName_input, lName)

    address_input = iframe_container.ele("tag:input@@id=addressDSARElement")
    address_input.click()
    sleep(random.uniform(0.1,0.5))
    _human_type2(address_input, dataRow["Address"])

    city_input = iframe_container.ele("tag:input@@id=cityDSARElement")
    city_input.click()
    sleep(random.uniform(0.1,0.5))
    _human_type2(city_input, dataRow["City"])

    state_select = iframe_container.ele("tag:input@@id=formField19DSARElement")
    state_select.click()
    sleep(random.uniform(0.1,0.5))
    if iframe_container.ele(f"tag:vt-option@@aria-label={usaStateDictionary[dataRow['State']]}") != None :
       iframe_container.ele(f"tag:vt-option@@aria-label={usaStateDictionary[dataRow['State']]}").click() 
    else :
        iframe_container.eles("tag:vt-option")[0].click()

    zip_input = iframe_container.ele("tag:input@@id=zipDSARElement")
    zip_input.click()
    sleep(random.uniform(0.1,0.5))
    _human_type2(zip_input, str(dataRow["Zipcode"]))

    email_str = generate_email(dataRow["Name"])
    email_input = iframe_container.ele("tag:input@@id=emailDSARElement")
    email_input.click()
    print("typing the email...")
    sleep(random.uniform(0.1,0.5))
    _human_type2(email_input, email_str)

    
    phone_input = iframe_container.ele("tag:input@@id=phoneNumberDSARElement")
    phone_input.click()
    sleep(random.uniform(0.1,0.5))
    _human_type2(phone_input, dataRow["Phone Number"])

    user_type = iframe_container.ele("tag:span@@text()= Yes ")
    user_type.click()

    detail_textarea = iframe_container.ele("tag:textarea@@id=requestDetailsDSARElement")
    detail_textarea.click()
    sleep(random.uniform(0.1,0.5))
    _human_type2(detail_textarea, "I want to remove my info.")

def datatrustcom(dataRow, website_name, in_user_email, run_mode) : 
    try : 
        sucessConfirmationApi = f"https://privacypros.com/web/dashboard/appendapi.php?website={website_name}&status=1&api=true&email={in_user_email}"
        errorConfirmationApi = f"https://privacypros.com/web/dashboard/appendapi.php?website={website_name}&status=2&api=true&email={in_user_email}"
        fName = dataRow["Name"].split()[0] # split string based on space to get first name
        lName = dataRow["Name"].split()[-1]# split string based on space to get last name

        screenshot_save_path = screentShotDir + "\DatatrustCom_" + fName + "-" + lName + ".png"

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
        page.get("https://thedatatrust.com/do-not-sell-my-personal-information/")

        sleep(random.uniform(1, 2))       

        fill_input_data(page, dataRow)

        sleep(1)

        page.wait.ele_displayed("#ajax-content-wrap")
        div_container = page.ele("#ajax-content-wrap")
        print(div_container)
        iframe_root_container = div_container.ele("tag:iframe")

        iframe_container = iframe_root_container.ele("tag:iframe@@title=reCAPTCHA")
        rc_anchor_container = iframe_container("tag:div@@id=rc-anchor-container")
        print(rc_anchor_container)
        rc_anchor_container.click()

        sleep(2)
        
        iframe_container1 = iframe_root_container.ele("tag:iframe@@title=recaptcha challenge expires in two minutes")
        audio_button = iframe_container1.ele("tag:button@@id=recaptcha-audio-button")

        print(audio_button)
        audio_button.click()
        audio_source = iframe_container1.ele("tag:audio@@id=audio-source").attr("src")
        print(audio_source)

        response = requests.get(audio_source)
        with open(("__downloaded_%d.mp3" % __import__("threading").get_ident()), "wb") as file:
            file.write(response.content)

        sleep(1)

        apiKey = os.getenv("TWOCAPTCHA_API_KEY", "")
        solver = TwoCaptcha(apiKey)
        print("Captcha is solving...")
        try :
            result = solver.audio(("__downloaded_%d.mp3" % __import__("threading").get_ident()), lang="en")
            print("Captcha is solved.")
            print(result["code"])
            Code = result["code"]
        except Exception as e:
            print("Error: ", str(e))
        audio_reponse_input = iframe_container1.ele("tag:input@@id=audio-response")
        _human_type2(audio_reponse_input, Code)

        verify_btn = iframe_container1.ele("tag:button@@id=recaptcha-verify-button")
        verify_btn.click()

        sleep(5)


        submit_button = iframe_root_container.ele("tag:button@@id=dsar-webform-submit-button")
        submit_button.run_js("this.click();")
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