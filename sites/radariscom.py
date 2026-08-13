from time import sleep
import logging
import os, datetime, pyautogui, requests, sys, random
from cloudsolver.CloudflareBypasser import CloudflareBypasser
from DrissionPage import ChromiumPage, ChromiumOptions
from cloudsolver.extension import proxies
from twocaptcha import TwoCaptcha
from lib.common import generate_email, generate_phone_number
from DrissionPage.common import Keys
from lib.email_verification import do_email_verification

now = datetime.datetime.now()
current_date = now.strftime("%Y-%m-%d")
base_dir = os.getcwd()

screentShotDir = os.path.join(base_dir, "ScreenShot", current_date)
os.makedirs(screentShotDir, exist_ok=True)

usaStateDictionary = { 'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR', 'California': 'CA', 'Colorado': 'CO', 'Connecticut': 'CT', 'Delaware': 'DE', 'District of Columbia': 'DC', 'Florida': 'FL', 'Georgia': 'GA', 'Hawaii': 'HI', 'Idaho': 'ID', 'Illinois': 'IL', 'Indiana': 'IN', 'Iowa': 'IA', 'Kansas': 'KS', 'Kentucky': 'KY', 'Louisiana': 'LA', 'Maine': 'ME', 'Maryland': 'MD', 'Massachusetts': 'MA', 'Michigan': 'MI', 'Minnesota': 'MN', 'Mississippi': 'MS', 'Missouri': 'MO', 'Montana': 'MT', 'Nebraska': 'NE', 'Nevada': 'NV', 'New Hampshire': 'NH', 'New Jersey': 'NJ', 'New Mexico': 'NM', 'New York': 'NY', 'North Carolina': 'NC', 'North Dakota': 'ND', 'Ohio': 'OH', 'Oklahoma': 'OK', 'Oregon': 'OR', 'Pennsylvania': 'PA', 'Rhode Island': 'RI', 'South Carolina': 'SC', 'South Dakota': 'SD', 'Tennessee': 'TN', 'Texas': 'TX', 'Utah': 'UT', 'Vermont': 'VT', 'Virginia': 'VA', 'Washington': 'WA', 'West Virginia': 'WV', 'Wisconsin': 'WI', 'Wyoming': 'WY' }

def _human_type2(element , text: str) -> None:
    """
    Types in a way reminiscent of a human, with a random delay in between 50ms to 100ms for every character
    :param element: Input element to type text to
    :param text: Input to be typed
    """

    for c in text:
        element.input(c)

        sleep(random.uniform(0.05, 0.1))

def get_chromium_options(arguments: list) -> ChromiumOptions:
    """
    Configures and returns Chromium options.
    
    :param browser_path: Path to the Chromium browser executable.
    :param arguments: List of arguments for the Chromium browser.
    :return: Configured ChromiumOptions instance.
    """
    options = ChromiumOptions()
    # options.set_argument('--auto-open-devtools-for-tabs', 'true') # we don't need this anymore
    for argument in arguments:
        options.set_argument(argument)
    return options

def make_standard_num(num) :
    ret = str(num)
    if len(ret) < 2 : ret = "0" + ret

    return ret

def fill_input_data(page, dataRow) : 
    fName = dataRow["Name"].split()[0] # split string based on space to get first name
    lName = dataRow["Name"].split()[-1]# split string based on space to get last name

    sleep(1)
    email_str = generate_email(dataRow["Name"])
    email_input = page.ele("tag:input@@name=user_email")
    email_input.click()
    print("typing the email...")
    sleep(random.uniform(0.1,0.5))
    _human_type2(email_input, email_str)


def radariscom(dataRow, website_name, in_user_email, run_mode) : 
    try : 
        fName = dataRow["Name"].split()[0] # split string based on space to get first name
        lName = dataRow["Name"].split()[-1]# split string based on space to get last name
        sucessConfirmationApi = f"https://privacypros.com/web/dashboard/appendapi.php?website={website_name}&status=1&api=true&email={in_user_email}"
        errorConfirmationApi = f"https://privacypros.com/web/dashboard/appendapi.php?website={website_name}&status=2&api=true&email={in_user_email}"

        #Launch Website
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
        
            
        page = ChromiumPage(addr_or_opts=options)
        
        page.get("https://radaris.com/control/privacy")

        next_div = page.ele("tag:div@@class:js-funnel-next-btn")
        next_div.run_js("this.click();")
        
        page.wait.ele_displayed("tag:div@@class:c-green")
        sleep(1)
        next_div_1 = page.ele("tag:div@@class:c-green")
        next_div_1.click()

        page.wait.ele_displayed("tag:div@@class:c-orange@@text():Yes")
        sleep(1)
        yes_div = page.ele("tag:div@@class:c-orange@@text():Yes")
        yes_div.click()

        fullName_input = page.ele("tag:input@@id=topsearch")
        fullName_input.click()
        print("typing the full name...")
        sleep(random.uniform(0.1,0.5))
        _human_type2(fullName_input, dataRow["Name"])

        city_state_input = page.ele("tag:input@@id=name_city_state")
        city_state_input.click()
        print("typing the city name...")
        sleep(random.uniform(0.1,0.5))
        _human_type2(city_state_input, dataRow["City"]+", "+usaStateDictionary[dataRow["State"]])

        search_btn = page.ele("tag:button@@aria-label=Search")
        search_btn.click()

        current_year = now.year
        birth_year = dataRow["Birth Year"]
        age = current_year - birth_year 
        
        page.wait.ele_displayed("tag:div@@id=tbl_ps")
        sleep(2)
        profile_list_div = page.ele("tag:div@@id=tbl_ps")
        print(profile_list_div)
        
        rows = profile_list_div.eles("tag:div@@class:teaser-card-title-container")
        
        if len(rows) > 0 :
            select_btn = rows[0].ele("tag:a@@text()=Select")
            print(select_btn)
            select_btn.click()
            
            page.wait.ele_displayed("tag:div@@class:c-white")
            sleep(1)
            start_remove_btn = page.ele("tag:div@@class:c-white")
            start_remove_btn.click()

            section_5 = page.ele("tag:section@@id:step_@@style=display: block;")
            section_5.set.style("display", "none")

            section_13 = page.ele("tag:section@@id=step_13")
            section_13.set.style("display", "block")

            fill_input_data(page, dataRow)

            apiKey = os.getenv("TWOCAPTCHA_API_KEY", "")
            solver = TwoCaptcha(apiKey)
            print("Captcha is solving...")
            try :
                site_key = "6LfzVwUTAAAAAIwM66sPa3AXjkm9nsi2Vr7WZnqd"
                site_url = page.url
                result = solver.recaptcha(site_key, site_url)
                print("Captcha is solved.")
                print(result["code"])
                Code = result["code"]
            except Exception as e:
                print("Error: ", str(e))


            iframe_container = page.ele("tag:iframe@@title=reCAPTCHA")
            print(iframe_container)
            recaptcha_input_token = iframe_container.ele("tag:input@@id=recaptcha-token")
            # recaptcha_input_token.set.attr("value", Code)
            recaptcha_input_token.run_js("this.value=arguments[0]", Code)

            textarea_token = page.ele("tag:textarea@@id=g-recaptcha-response")
            
            textarea_token.run_js("this.value=arguments[0]", Code)
            print(textarea_token)


            iframe_container1 = page.ele("tag:iframe@@title=recaptcha challenge expires in two minutes")
            recaptcha_input_token1 = iframe_container1.ele("tag:input@@id=recaptcha-token")
            # recaptcha_input_token1.set.attr("value", Code)
            recaptcha_input_token1.run_js("this.value=arguments[0]", Code)
            print(recaptcha_input_token1)

            section_13 = page.ele("tag:section@@id=step_13")
            
            form_container = section_13.ele("tag:form")
            print(form_container)
            form_container.run_js("""
                this.action = 'https://radaris.com/ng/control/a.remove_request';                  
                this.submit();
            """)

            section_13.set.style("display", "none")

            section_14 = page.ele("tag:section@@id=step_14")
            section_14.set.style("display", "block")

        sleep(random.uniform(1, 2))       

        screenshot_save_path = screentShotDir + "\RadarisCom_" + fName + "-" + lName + ".png"
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