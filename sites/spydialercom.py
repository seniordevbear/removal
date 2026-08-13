from DrissionPage import ChromiumPage, ChromiumOptions
from time import sleep
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
    
    page.wait.ele_displayed("tag:select@@id=SttFltrDrpDwnLst")
    state_element = page.ele("tag:select@@id=SttFltrDrpDwnLst")
    state_element.select.by_text(dataRow["State"])

def spydialercom(dataRow, website_name, in_user_email, run_mode) : 
    try : 
        
        fName = dataRow["Name"].split()[0] # split string based on space to get first name
        lName = dataRow["Name"].split()[-1]# split string based on space to get last name
        screenshot_save_path = screentShotDir + "\SpydialerCom_" + fName + "-" + lName + ".png"

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
        options.add_extension("adblock")

        if run_mode == "headless" :
            options.headless()
        #Launch Website
        page = ChromiumPage(addr_or_opts=options)
        page.get("https://www.spydialer.com/Consumers/wizard.aspx")

        sleep(3)
        fill_input_data(page, dataRow)
        sleep(1)

        page.wait.ele_displayed("tag:iframe@@title=reCAPTCHA")
        sleep(1)
        iframe_container = page.ele("tag:iframe@@title=reCAPTCHA")
        rc_anchor_container = iframe_container("tag:div@@id=rc-anchor-container")
        print(rc_anchor_container)
        rc_anchor_container.click()

        sleep(2)
        page.wait.ele_displayed("tag:iframe@@title=recaptcha challenge expires in two minutes")
        sleep(1)
        iframe_container1 = page.ele("tag:iframe@@title=recaptcha challenge expires in two minutes")
        audio_button = iframe_container1.ele("tag:button@@id=recaptcha-audio-button")

        print(audio_button)
        audio_button.click()
        audio_source = iframe_container1.ele("tag:audio@@id=audio-source").attr("src")
        print(audio_source)

        response = requests.get(audio_source)
        with open("__downloaded.mp3", "wb") as file:
            file.write(response.content)

        sleep(1)

        apiKey = os.getenv("TWOCAPTCHA_API_KEY", "")
        solver = TwoCaptcha(apiKey)
        print("Captcha is solving...")
        try :
            result = solver.audio("__downloaded.mp3", lang="en")
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

        continue_button = page.ele("tag:input@@id=ctl00_ContentPlaceHolder1_StateSubmitButton")
        continue_button.click()

        sleep(random.uniform(1, 2))
        page.wait.ele_displayed("tag:input@@id=ctl00_ContentPlaceHolder1_PrivacyLawButton")
        got_it_button = page.ele("tag:input@@id=ctl00_ContentPlaceHolder1_PrivacyLawButton")
        got_it_button.click()

        sleep(random.uniform(1, 2))

        page.wait.eles_loaded("tag:i@@class=fa fa-plus pr-1")
        add_name_span = page.ele("tag:span@id=ctl00_ContentPlaceHolder1_AddNameBlockLabel")
        add_name_span.click()

        page.wait.ele_displayed("tag:input@@id=FrstNmTxtBx")
        first_name_input = page.ele("tag:input@@id=FrstNmTxtBx")
        first_name_input.click()
        print("typing first name...")
        _human_type2(first_name_input, fName)

        last_name_input = page.ele("tag:input@@id=z9a2_g4")
        last_name_input.click()
        print("typing last name...")
        _human_type2(last_name_input, lName)

        name_add_button = page.ele("tag:input@@id=ctl00_ContentPlaceHolder1_z9a2_g44")
        name_add_button.click()

        page.wait.eles_loaded("tag:i@@class=fa fa-plus pr-1")
        add_address_span = page.ele("tag:span@@id=ctl00_ContentPlaceHolder1_AddAddressBlockLabel")
        add_address_span.click()

        page.wait.ele_displayed("tag:input@@id=AddressTextBox")
        address_input = page.ele("tag:input@@id=AddressTextBox")
        address_input.click()
        print("typing address...")
        _human_type2(address_input, dataRow["Address"])

        city_input = page.ele("tag:input@@id=CityTextBox")
        city_input.click()
        print("typing city...")
        _human_type2(city_input, dataRow["City"])

        address_add_button = page.ele("tag:input@@id=ctl00_ContentPlaceHolder1_SaveAddressButton")
        address_add_button.click()

        page.wait.eles_loaded("tag:i@@class=fa fa-plus pr-1")
        add_phone_span = page.ele("tag:span@@id=ctl00_ContentPlaceHolder1_AddPhoneBlockLabel")
        add_phone_span.click()

        page.wait.ele_displayed("tag:input@@id=PhoneTextBox")
        phone_input = page.ele("tag:input@@id=PhoneTextBox")
        phone_input.click()
        print("typing phone number...")
        _human_type2(phone_input, generate_phone_number())

        phone_add_button = page.ele("tag:input@@id=ctl00_ContentPlaceHolder1_SavePhoneButton")
        phone_add_button.click()

        page.wait.eles_loaded("tag:i@@class=fa fa-plus pr-1")
        add_email_span = page.ele("tag:span@@id=ctl00_ContentPlaceHolder1_AddEmailBlockLabel")
        add_email_span.click()

        page.wait.ele_displayed("tag:input@@id=EmailTextBox")
        email_input = page.ele("tag:input@@id=EmailTextBox")
        email_input.click()
        print("typing email...")
        _human_type2(email_input, dataRow["User Email"])

        email_add_button = page.ele("tag:input@@id=ctl00_ContentPlaceHolder1_SaveEmailButton")
        email_add_button.click()

        page.wait.eles_loaded("tag:input@@id=SbmtM")
        OptOutMyInfo_button = page.ele("tag:input@@id=SbmtM")
        OptOutMyInfo_button.click()

        try :
            # response = requests.get(sucessConfirmationApi, timeout=10)
            print("Success Confirmation API is sent successfully!")
            sleep(10)
            page.get_screenshot(screenshot_save_path)
        except Exception as e:
            print("Success Confirmation API is failed: ", str(e))
        
    except Exception as e:
        try :
            # response = requests.get(errorConfirmationApi, timeout=10)
            print("Error Confirmation API is sent successfully!")
            sleep(10)
            page.get_screenshot(screenshot_save_path)
        except Exception as e:
            print("Error Confirmation API is failed: ", str(e))

    page.quit()

    return screenshot_save_path