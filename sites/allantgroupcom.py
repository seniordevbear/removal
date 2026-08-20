from DrissionPage import ChromiumPage, ChromiumOptions
from time import sleep
import random
import os, datetime, pyautogui, sys, requests
from twocaptcha import TwoCaptcha
from lib.common import generate_email, generate_phone_number
from lib.email_verification import do_email_verification
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

def make_standard_num(num) :
    ret = str(num)
    # if num < 10 : ret = "0" + ret
    if len(ret) < 2 : ret = "0" + ret
    return ret

def fill_input_data(page, dataRow) : 
    
    fName = dataRow["Name"].split()[0] # split string based on space to get first name
    lName = dataRow["Name"].split()[-1]# split string based on space to get last name

    email_str = generate_email(dataRow["Name"])
    email_input = page.ele("tag:input@@id=emailDSARElement")
    email_input.clear()
    email_input.click()
    print("typing the email...")
    sleep(random.uniform(0.1,0.5))
    _human_type2(email_input, email_str)

    fName_input = page.ele("tag:input@@id=firstNameDSARElement")
    fName_input.clear()
    fName_input.click()
    print("typing the first name...")
    sleep(random.uniform(0.1,0.5))
    _human_type2(fName_input, fName)

    lName_input = page.ele("tag:input@@id=lastNameDSARElement")
    lName_input.clear()
    lName_input.click()
    print("typing the last name...")
    sleep(random.uniform(0.1,0.5))
    _human_type2(lName_input, lName)

    street_input = page.ele("tag:input@@id=addressDSARElement")
    street_input.clear()
    street_input.click()
    sleep(random.uniform(0.1,0.5))
    _human_type2(street_input, dataRow["Address"])

    city_input = page.ele("tag:input@@id=cityDSARElement")
    city_input.clear()
    city_input.click()
    sleep(random.uniform(0.1,0.5))
    _human_type2(city_input, dataRow["City"])

    state_input = page.ele("tag:input@@id=formField17DSARElement")
    state_input.clear()
    state_input.click()
    sleep(random.uniform(0.1,0.5))
    _human_type2(state_input, dataRow["State"])

    zip_input = page.ele("tag:input@@id=zipDSARElement")
    zip_input.clear()
    zip_input.click()
    sleep(random.uniform(0.1,0.5))
    _human_type2(zip_input, str(dataRow["Zipcode"]))

    phone_input = page.ele("tag:input@@id=phoneNumberDSARElement")
    phone_input.clear()
    phone_input.click()
    sleep(random.uniform(0.1,0.5))
    _human_type2(phone_input, dataRow["Phone Number"])

    birthday = make_standard_num(dataRow["Birth Month"]) + "/" + make_standard_num(dataRow["Birth Day"]) + "/" + str(dataRow["Birth Year"])
    birth_input = page.ele("tag:input@@id=dateOfBirthDSARElement")
    birth_input.clear()
    birth_input.click()
    sleep(random.uniform(0.1,0.5))
    _human_type2(birth_input, birthday)

    sleep(1)

    
def allantgroupcom(dataRow, website_name, in_user_email, run_mode) : 
    page = None
    try : 
        fName = dataRow["Name"].split()[0] # split string based on space to get first name
        lName = dataRow["Name"].split()[-1]# split string based on space to get last name
        screenshot_save_path = screentShotDir + "\AllantGroupCom_" + fName + "-" + lName + ".png"
        
        sucessConfirmationApi = f"https://privacypros.com/web/dashboard/appendapi.php?website={website_name}&status=1&api=true&email={in_user_email}"
        errorConfirmationApi = f"https://privacypros.com/web/dashboard/appendapi.php?website={website_name}&status=2&api=true&email={in_user_email}"

        arguments = [
            "-no-first-run",
            "--start-maximized",
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

        
        #Launch Website
        username = os.getenv("SMARTPROXY_USER", "")
        password = os.getenv("SMARTPROXY_PASSWORD", "")
        endpoint = os.getenv("SMARTPROXY_ENDPOINT", "isp.smartproxy.com")
        port = port_arr[random_number]


        print(endpoint + ":" + port)
        proxy_extension = proxies(username, password, endpoint, port)

        options = get_chromium_options(arguments).auto_port().add_extension("extension")

        if run_mode == "headless" :
            options.headless()

        #Launch Website
        page = ChromiumPage(addr_or_opts=options)
        page.get("https://privacyportal.onetrust.com/webform/cbbe21b6-d675-445f-9c24-f625c01dafb3/bebf975c-f540-4f99-8b73-116ca8cb28be")

        fill_input_data(page, dataRow)

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

        photo_file = page.ele("tag:input@@id=dsar-webform-file-input")
        photo_file.click()

        sleep(1)

        photo_path = r"D:\avatar\other\1.jpg"
        pyautogui.write(photo_path)
        pyautogui.press("enter")

        sleep(10)

        submit_btn = page.ele("tag:button@@id=dsar-webform-submit-button")
        submit_btn.click()

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