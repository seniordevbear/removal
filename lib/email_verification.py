from DrissionPage import ChromiumPage, ChromiumOptions
from time import sleep


email_verification_url = "https://mail1.privacypros.com/surgeweb"

username = "confirmation"
password = "privacypros123"

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

def login(driver) : 
    driver.get(email_verification_url)
    username_input = driver.ele("tag:input@@name=username_ex")
    username_input.clear()
    username_input.input(username)

    password_input = driver.ele("tag:input@@name=password")
    password_input.clear()
    password_input.input(password)

    login_btn = driver.ele("tag:input@@id=cmd_login")
    login_btn.click()


def do_email_verification(site_name, screenshot_save_path) :

    arguments = [
        "-no-first-run",
        "--start-maximized",
        "-disable-javascript",
        "-disable-gpu",
        "-disable-sensors",
    ]

    options = get_chromium_options(arguments).auto_port()

    driver = ChromiumPage(addr_or_opts=options)

    login(driver)
    sleep(3)

    driver.refresh()
    sleep(2)

    driver.wait.ele_displayed("tag:li@@fld_id=INBOX")
    inbox_btn = driver.ele("tag:li@@fld_id=INBOX")
    inbox_btn.click()
    sleep(1)

    msg_table = driver.ele("tag:table@@id=x_msgs_table")
    msg_trs = msg_table.eles("tag:tr@@class:msg_unread")
    
    is_checked = False

    button_texts = [
        "Confirm Email",
        "click here",
        "Confirm my request",
        "Verify Email & Opt-Out",
        "Verify My Identity",
        "Click here to fill out the record removal form",
        "Click here to remove"
    ]

    # for index, row in enumerate(msg_trs) :

    #     cells = row.eles("tag:td")

    #     title = cells[1].eles("tag:div@@class=mi")[0].text
        
    #     if site_name.lower() in title.lower() : 
    #         row.click()
    #         sleep(1)
    #         confirm_email_btn = driver.ele("tag:a@@text()=Confirm Email")
    #         if confirm_email_btn : 
    #             confirm_email_btn.click()
    #             is_checked = True
    #             sleep(20)
    #             break
    #         else :
    #             click_here_btn = driver.ele("tag:a@@text()=click here")
    #             if click_here_btn :
    #                 click_here_btn.click()
    #                 is_checked = True
    #                 sleep(20)
    #                 break
    #             else :
    #                 confirm_my_request_btn = driver.ele("tag:a@@text()=Confirm my request")
    #                 if confirm_my_request_btn :
    #                     confirm_my_request_btn.click()
    #                     is_checked = True
    #                     sleep(20)
    #                     break
    #                 else : 
    #                     verify_email_btn = driver.ele("tag:a@@text()=Verify Email & Opt-Out")
    #                     if verify_email_btn :
    #                         verify_email_btn.click()
    #                         is_checked = True
    #                         sleep(20)
    #                         break
    #                     else :
    #                         verify_my_identity_btn = driver.ele("tag:a@@text()= Verify My Identity ")
    #                         if verify_my_identity_btn :
    #                             verify_my_identity_btn.click()
    #                             is_checked = True
    #                             sleep(20)
    #                             break
    #                         else :
    #                             click_here_to_fill_btn = driver.ele("tag:a@@text()=Click here to fill out the record removal form")
    #                             if click_here_to_fill_btn :
    #                                 click_here_to_fill_btn.click()
    #                                 is_checked = True
    #                                 sleep(20)
    #                                 break
    #                             else :
    #                                 click_here_to_remove = driver.ele("tag:a@@text():Click here to remove")
    #                                 if click_here_to_remove :
    #                                     click_here_to_remove.click()
    #                                     is_checked = True
    #                                     sleep(20)
    #                                     break
    #                                 else :
    #                                     continue
    

    # if is_checked == False :
    #     driver.wait.ele_displayed("tag:li@@fld_id=Spam")
    #     spam_btn = driver.ele("tag:li@@fld_id=Spam")
    #     spam_btn.click()
    #     sleep(1)

    #     msg_table_1 = driver.ele("tag:table@@id=x_msgs_table")
    #     msg_trs_1 = msg_table_1.eles("tag:tr@@class:msg_unread")

    #     for inex, row in enumerate(msg_trs_1) :

    #         cells = row.eles("tag:td")

    #         title = cells[1].eles("tag:div@@class=mi")[0].text
            
    #         if site_name.lower() in title.lower() : 
    #             row.click()
    #             sleep(1)
    #             confirm_email_btn = driver.ele("tag:a@@text()=Confirm my email address")
    #             if confirm_email_btn : 
    #                 confirm_email_btn.click()
    #                 is_checked = True
    #                 sleep(20)
    #                 break
    #             else :
    #                 click_here_btn = driver.ele("tag:a@@text()=click here")
    #                 if click_here_btn :
    #                     click_here_btn.click()
    #                     is_checked = True
    #                     sleep(20)
    #                     break
    #                 else :
    #                     continue

    # driver.quit()

    for row in msg_trs:
        cells = row.eles("tag:td")
        title = cells[1].eles("tag:div@@class=mi")[0].text
        
        if site_name.lower() in title.lower():
            row.click()
            sleep(1)
            for text in button_texts:
                button = driver.ele(f"tag:a@@text()={text}", timeout=0.5)
                if button:
                    button.click()
                    is_checked = True
                    sleep(30)
                    driver.latest_tab.get_screenshot(screenshot_save_path)
                    print("ScreenShot is correctly saved.")
                    break
            if is_checked:
                break

    if not is_checked:
        driver.wait.ele_displayed("tag:li@@fld_id=Spam")
        spam_btn = driver.ele("tag:li@@fld_id=Spam")
        spam_btn.click()
        sleep(1)

        msg_table_1 = driver.ele("tag:table@@id=x_msgs_table")
        msg_trs_1 = msg_table_1.eles("tag:tr@@class:msg_unread")

        for row in msg_trs_1:
            cells = row.eles("tag:td")
            title = cells[1].eles("tag:div@@class=mi")[0].text
            
            if site_name.lower() in title.lower():
                row.click()
                sleep(1)
                for text in button_texts:
                    button = driver.ele(f"tag:a@@text()={text}", timeout=0.5)
                    if button:
                        button.click()
                        is_checked = True
                        sleep(30)
                        driver.latest_tab.get_screenshot(screenshot_save_path)
                        print("ScreenShot is correctly saved.")
                        break
                if is_checked:
                    break

    driver.quit()

