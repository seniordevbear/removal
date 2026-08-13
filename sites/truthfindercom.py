# truthfindercom.py - REWRITTEN 2026-05-28
# Old: 0/107 prod success. Current form at /privacy-center/ is a React
# SPA, fields use name= not id=. Flow:
#   1. Click "Delete My User Data" tab/button
#   2. Fill firstName / middleInitial / lastName / city / email / deletionEmail
#   3. Click Submit
# Recon shows fields exist visibly. Validate captcha or post-submit
# behavior post-deploy via the saved screenshots.
import os, datetime
from time import sleep
from lib.broker_helpers import (
    safe_chromium_for_broker, dismiss_common_consents,
    find_input, find_button, screenshot_step, log_step,
)
from lib.common import generate_email


def truthfindercom(dataRow, website_name, in_user_email, run_mode):
    broker = "truthfindercom"
    fName = dataRow["Name"].split()[0]
    lName = dataRow["Name"].split()[-1]
    base_dir = os.getcwd()
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    out_dir = os.path.join(base_dir, "ScreenShot", today)
    os.makedirs(out_dir, exist_ok=True)
    screenshot_save_path = os.path.join(out_dir, f"{broker}_{fName}-{lName}.png")

    try:
        with safe_chromium_for_broker(
            broker, use_proxy=True,
            headless=(run_mode == "headless"),
            extra_extensions=["adblock"],
        ) as page:
            page.get("https://www.truthfinder.com/privacy-center/")
            sleep(4)
            screenshot_step(page, broker, "01_landed")
            dismiss_common_consents(page, broker)
            sleep(0.5)

            # Click "Delete My User Data" to reveal the deletion form
            try:
                find_button(
                    page,
                    "tag:button@@text()=Delete My User Data",
                    "tag:button@@text():Delete My User",
                ).click()
                log_step(broker, "clicked Delete My User Data tab")
                sleep(2)
                screenshot_step(page, broker, "02_deletion_tab")
            except Exception as e:
                log_step(broker, f"could not open deletion tab: {e}")

            email = generate_email(dataRow["Name"])
            find_input(page, "tag:input@@name=firstName").input(fName)
            try:
                # middle initial is optional
                mi = page.ele("tag:input@@name=middleInitial", timeout=1)
                if mi:
                    mi.input(fName[0] if fName else "A")
            except Exception:
                pass
            find_input(page, "tag:input@@name=lastName").input(lName)
            find_input(page, "tag:input@@name=city").input(dataRow.get("City", ""))
            # 'email' is generic; 'deletionEmail' is the confirmation address
            try:
                find_input(page, "tag:input@@name=email").input(email)
            except Exception:
                pass
            find_input(page, "tag:input@@name=deletionEmail").input(email)
            log_step(broker, "filled deletion form")
            screenshot_step(page, broker, "03_filled")

            find_button(
                page,
                "tag:button@@text()=Submit",
                "tag:button@@type=submit",
            ).click()
            log_step(broker, "submitted")
            sleep(4)
            screenshot_step(page, broker, "04_submitted")

            try:
                page.get_screenshot(screenshot_save_path)
            except Exception:
                pass
    except Exception as e:
        log_step(broker, f"OUTER FAILURE: {e}")

    return screenshot_save_path
