from DrissionPage import ChromiumPage, ChromiumOptions
from time import sleep
import json
import random
import os, datetime, pyautogui, requests
from lib.common import generate_email, generate_phone_number
from twocaptcha import TwoCaptcha
from cloudsolver.extension import proxies

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

    fName = dataRow["Name"].split()[0] # split string based on space to get first name
    lName = dataRow["Name"].split()[-1]# split string based on space to get last name

    iframes = page.eles('tag:iframe')
    print(f"Found {len(iframes)} iframes")

    main_container = page.ele("tag:main@@id=main")
    iframe_container = main_container.ele("tag:iframe")

    dsar_name = iframe_container.ele("tag:div@@aria-label=Customer")
    dsar_name.click()
    sleep(random.uniform(0.1,0.5))

    requests_type = iframe_container.ele("tag:div@@aria-label=Do Not Sell or Share My Information")
    requests_type.click()
    sleep(random.uniform(0.1,0.5))

    email_input = iframe_container.ele("tag:input@@id=emailDSARElement")
    email_input.click()
    sleep(random.uniform(0.1,0.5))
    email = generate_email(dataRow["Name"])
    _human_type2(email_input, email)

    confirmemail_input = iframe_container.ele("tag:input@@id=confirmEmailInputDSARElement")
    confirmemail_input.click()
    sleep(random.uniform(0.1,0.5))
    _human_type2(confirmemail_input, email)

    iframe_container1 = iframe_container.ele("tag:iframe@@title=reCAPTCHA")
    rc_anchor_container = iframe_container1("tag:div@@id=rc-anchor-container")
    rc_anchor_container.click()

    sleep(2)
    page.wait.ele_displayed("tag:iframe@@title=recaptcha challenge expires in two minutes")
    sleep(1)
    iframe_container2 = iframe_container.ele("tag:iframe@@title=recaptcha challenge expires in two minutes")
    audio_button = iframe_container2.ele("tag:button@@id=recaptcha-audio-button")

    audio_button.click()
    audio_source = iframe_container2.ele("tag:audio@@id=audio-source").attr("src")
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
        audio_reponse_input = iframe_container2.ele("tag:input@@id=audio-response")
        _human_type2(audio_reponse_input, Code)
        sleep(random.uniform(0.1,0.5))
        verify_btn = iframe_container2.ele("tag:button@@id=recaptcha-verify-button")
        verify_btn.click()
        sleep(5)
        submit_button = iframe_container.ele("tag:button@@id=dsar-webform-submit-button")
        submit_button.click()
    except Exception as e:
        print("Error: ", str(e))
    
def adastradatacom(dataRow, website_name, in_user_email, run_mode) : 
    try : 
        sucessConfirmationApi = f"https://privacypros.com/web/dashboard/appendapi.php?website={website_name}&status=1&api=true&email={in_user_email}"
        errorConfirmationApi = f"https://privacypros.com/web/dashboard/appendapi.php?website={website_name}&status=2&api=true&email={in_user_email}"
        
        fName = dataRow["Name"].split()[0] # split string based on space to get first name
        lName = dataRow["Name"].split()[-1]# split string based on space to get last name
        screenshot_save_path = screentShotDir + "\AdastradataCom_" + fName + "-" + lName + ".png"
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

        proxies(username, password, endpoint, port)
        arguments = [
            "--no-first-run",
            "--start-maximized",
            # "--incognito",
            "--disable-javascript",
            "--disable-gpu",
            "--disable-sensors",
        ]

        options = get_chromium_options(arguments).auto_port().add_extension("extension")
        if run_mode == "headless" : 
            options.headless()
        #Launch Website
        page = ChromiumPage(addr_or_opts=options)
        page.get("https://www.godaddy.com/legal/agreements/do-not-share")

        sleep(5)

        fill_input_data(page, dataRow)
        # response = requests.get(sucessConfirmationApi, timeout=10)
        print("Success Confirmation API is sent successfully!")
        sleep(5)
        page.get_screenshot(screenshot_save_path)
        
    except Exception as e:
        try :
            # response = requests.get(errorConfirmationApi, timeout=10)
            print("Error Confirmation API is sent successfully!",str(e))
            sleep(5)
            page.get_screenshot(screenshot_save_path)
        except Exception as e:
            print("Error Confirmation API is failed: ", str(e))

    page.quit()

    return screenshot_save_path