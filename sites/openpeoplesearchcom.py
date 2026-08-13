# openpeoplesearchcom.py - REWRITTEN 2026-05-28
# Old: 0/107 prod success. Landing at /Consumer/State shows only a
# CONTINUE button + "Remove My Info" link. Multi-step flow:
#   1. Click "Remove My Info" link (goes to /Consumer)
#   2. Fill form
#   3. Submit
# The recon didn't observe visible inputs because the search form is on
# the next page after the link click.
import os, datetime
from time import sleep
from lib.broker_helpers import (
    safe_chromium_for_broker, dismiss_common_consents,
    find_input, find_button, safe_select, screenshot_step, log_step,
)
from lib.common import generate_email


def openpeoplesearchcom(dataRow, website_name, in_user_email, run_mode):
    broker = "openpeoplesearchcom"
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
            page.get("https://openpeoplesearch.com/Consumer/State")
            sleep(3)
            screenshot_step(page, broker, "01_landed")
            dismiss_common_consents(page, broker)
            sleep(0.5)

            # Step 1: select state and continue
            state = dataRow.get("State", "")
            if state:
                safe_select(page, "tag:select", state)
            try:
                find_button(page, "tag:button@@text():CONTINUE",
                           "tag:button@@type=submit").click()
                log_step(broker, "advanced past state-select page")
                sleep(3)
                screenshot_step(page, broker, "02_form_page")
            except Exception:
                pass

            # Step 2: try to fill name fields (selectors unknown - try several
            # common patterns)
            try:
                find_input(page,
                          "tag:input@@name:first",
                          "tag:input@@id:first",
                          "tag:input@@placeholder:First").input(fName)
                find_input(page,
                          "tag:input@@name:last",
                          "tag:input@@id:last",
                          "tag:input@@placeholder:Last").input(lName)
                find_input(page,
                          "tag:input@@name:city",
                          "tag:input@@id:city",
                          "tag:input@@placeholder:City").input(dataRow.get("City", ""))
                screenshot_step(page, broker, "03_filled")
                find_button(page,
                           "tag:button@@type=submit").click()
                log_step(broker, "submitted")
                sleep(4)
                screenshot_step(page, broker, "04_submitted")
            except Exception as e:
                log_step(broker, f"form-fill stage: {e}")
                screenshot_step(page, broker, "99_form_fail")

            try:
                page.get_screenshot(screenshot_save_path)
            except Exception:
                pass
    except Exception as e:
        log_step(broker, f"OUTER FAILURE: {e}")

    return screenshot_save_path
