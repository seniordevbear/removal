from DrissionPage import ChromiumPage, ChromiumOptions
from time import sleep
import json
import random
import os, datetime, pyautogui, requests
from lib.common import generate_email, generate_phone_number

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
    if len(ret) < 2 : ret = "0" + ret

    return ret

def fill_input_data(page, dataRow) : 
    fName = dataRow["Name"].split()[0] # split string based on space to get first name
    lName = dataRow["Name"].split()[-1]# split string based on space to get last name

    iframe_container = page.ele("tag:iframe@@class=responsive-iframe")
    print(iframe_container)
    form_container = iframe_container.ele("tag:form@@id=test")
    print(form_container)
    fName_input = form_container.ele("tag:input@@complink=Name_First")
    print(fName_input)
    fName_input.click()
    print("typing the first name...")
    sleep(random.uniform(0.1,0.5))
    _human_type2(fName_input, fName)

    lName_input = form_container.ele("tag:input@@complink=Name_Last")
    lName_input.click()
    print("typing the last name...")
    sleep(random.uniform(0.1,0.5))
    _human_type2(lName_input, lName)

    email_input = form_container.ele("tag:input@@id=Email-arialabel")
    email_input.click()
    print("typing the email...")
    sleep(random.uniform(0.1,0.5))
    _human_type2(email_input, generate_email(dataRow["Name"]))

    phone_input = form_container.ele("tag:input@@id=PhoneNumber")
    phone_input.click()
    print("typing the email...")
    sleep(random.uniform(0.1,0.5))
    _human_type2(phone_input, generate_phone_number())

    address_input = form_container.ele("tag:input@@complink=Address_AddressLine1")
    address_input.click()
    sleep(random.uniform(0.1,0.5))
    _human_type2(address_input, dataRow["Address"])

    city_input = form_container.ele("tag:input@@complink=Address_City")
    city_input.click()
    sleep(random.uniform(0.1,0.5))
    _human_type2(city_input, dataRow["City"])

    state_select = form_container.ele("tag:input@@complink=Address_Region")
    state_select.click()
    sleep(random.uniform(0.1,0.5))
    _human_type2(state_select, dataRow["State"])

    zip_input = form_container.ele("tag:input@@complink=Address_ZipCode")
    zip_input.click()
    sleep(random.uniform(0.1,0.5))
    _human_type2(zip_input, str(dataRow["Zipcode"]))

    label_element1 = form_container.ele("tag:label@@for=DecisionBox")
    label_element1.click()

    label_element2 = form_container.ele("tag:label@@for=DecisionBox2")
    label_element2.click()

def usdatacorporationcom(dataRow, website_name, in_user_email, run_mode) : 
    page = None
    try : 
        fName = dataRow["Name"].split()[0] # split string based on space to get first name
        lName = dataRow["Name"].split()[-1]# split string based on space to get last name
        screenshot_save_path = screentShotDir + r"\UsdatacorporationCom_" + fName + "-" + lName + ".png"
        
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
        page.get("https://www.usdatacorporation.com/opt-out?utm_source=www.usdatacorporation.com&utm_medium=referral&utm_term=mailing&utm_content=101757033198&utm_campaign=Mailing_Lists&gclid=undefined")

        sleep(random.uniform(1, 2))

        fill_input_data(page, dataRow)

        iframe_container = page.ele("tag:iframe@@class=responsive-iframe")
        print(iframe_container)
        form_container = iframe_container.ele("tag:form@@id=test")

        submit_button = form_container.ele("tag:button@@value=submit")
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