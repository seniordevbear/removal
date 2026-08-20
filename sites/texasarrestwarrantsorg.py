from DrissionPage import ChromiumPage, ChromiumOptions
from time import sleep
import json
import random
import os, datetime, pyautogui, requests
from lib.common import generate_email
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

    fName_input = page.ele("tag:input@@id=dynamicmodel-field_31")
    fName_input.click()
    print("typing the first name...")
    sleep(random.uniform(0.1,0.5))
    _human_type2(fName_input, fName)

    lName_input = page.ele("tag:input@@id=dynamicmodel-field_32")
    lName_input.click()
    print("typing the last name...")
    sleep(random.uniform(0.1,0.5))
    _human_type2(lName_input, lName)

    email_input = page.ele("tag:input@@id=dynamicmodel-field_33")
    email_input.click()
    print("typing the email...")
    sleep(random.uniform(0.1,0.5))
    _human_type2(email_input, generate_email(dataRow["Name"]))

    comment_textarea = page.ele("tag:textarea@@id=dynamicmodel-field_36")

    comment_textarea.click()
    print("typing the email...")
    sleep(random.uniform(0.1,0.5))
    _human_type2(comment_textarea, "I want to remove my information.")


def texasarrestwarrantsorg(dataRow, website_name, in_user_email, run_mode) : 
    page = None
    try : 
        fName = dataRow["Name"].split()[0] # split string based on space to get first name
        lName = dataRow["Name"].split()[-1]# split string based on space to get last name
        screenshot_save_path = screentShotDir + "\TexasarrestWarrantsOrg_" + fName + "-" + lName + ".png"
        
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


        print(endpoint + ":" + port)
        proxy_extension = proxies(username, password, endpoint, port)

        options = get_chromium_options(arguments).auto_port().add_extension("extension")

        if run_mode == "headless" :
            options.headless()
        
        
        #Launch Website
        page = ChromiumPage(addr_or_opts=options)
        page.get("https://www.texasarrestwarrants.org/contact")

        sleep(random.uniform(1, 2))

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

        submit_button = page.ele("tag:button@@text()=Send")
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