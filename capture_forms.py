r"""
capture_forms.py -- run ON THE VPS from C:\wonderful\removal:

    Scripts\python.exe capture_forms.py

Needs nothing but the pipeline's own Python environment (DrissionPage).
No database, no .env, no customer data. Opens each broker's opt-out page
in a visible Chrome window and saves, next to this file:

    capture_forms\<broker>.html   full page source
    capture_forms\<broker>.png    full-page screenshot
    capture_forms\_log.txt        what happened, including any error

Takes about 5 minutes. Then zip the capture_forms folder and upload it to
/root/privacyduck/ on the web server.
"""
import os
import sys
import time
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "capture_forms")

# broker key -> the page the removal script navigates to
TARGETS = {
    "acbjcom": "https://privacyportal.onetrust.com/webform/161633e1-9ffa-4774-8e22-ae77c29e0c70/a87fe61a-39f8-4b0a-a43f-779d6774c3c5",
    "accudatacom": "https://privacy.deepsync.com/",
    "advancedpeoplesearchcom": "https://www.afternic.com/legal/agreements/do-not-share",
    "affinitysolutionscom": "https://affinitysolutions-privacy.my.onetrust.com/webform/a564cfa1-53bf-4c10-bf95-cd907432d7e8/7e4e6bf3-6562-454e-8c73-6a7bd1f4b336",
    "acxiomcom": "https://privacyportal.onetrust.com/webform/342ca6ac-4177-4827-b61e-19070296cbd3/7229a09c-578f-4ac6-a987-e0428a7b877e",
    "allpeoplecom": "https://allpeople.com",
    "archivescom": "https://www.archives.com/optout",
    "advancedbackgroundcheckscom": "https://www.advancedbackgroundchecks.com/removal",
    "alescodatacom": "https://alescodata.com/do-not-sell-my-personal-information/",
    "americaphonebookcom": "http://americaphonebook.com/contact.php",
    "findpeoplesearchcom": "https://www.findpeoplesearch.com/customerservice/",
    "brandwatchcom": "https://www.brandwatch.com/p/legal-data/",
    "completemedicallistscom": "http://completemedicallists.com/ccpa.php",
    "fmadatacom": "https://www.fmadata.com/opt-out-requests/new",
    "contactoutcom": "https://contactout.com/optout",
    "demystcom": "https://demyst.com/personal-information-request-california",
    "beenverifiedcom": "https://www.beenverified.com/svc/optout/search/comprehensive_optouts",
    "bumpercom": "https://www.bumper.com/svc/optout/search/comprehensive_optouts",
    "faradayio": "https://docs.google.com/forms/d/e/1FAIpQLSd4h_G6XcXXpHq8FGeYgHH9CkQ3s4_qdIE-ZBKlNtdzKSXPfA/viewform",
    "backgroundcheckco": "https://backgroundcheck.co/optout",
    "arkansascourtrecordsus": "https://arkansascourtrecords.us/request-portal",
    "ohioarrestsorg": "https://ohioarrests.org/request-portal",
}


def log(msg):
    line = time.strftime("%H:%M:%S ") + msg
    print(line, flush=True)
    with open(os.path.join(OUT, "_log.txt"), "a", encoding="utf-8") as f:
        f.write(line + "\n")


def main():
    os.makedirs(OUT, exist_ok=True)
    log("capture_forms starting; python %s; output -> %s" % (sys.version.split()[0], OUT))

    try:
        from DrissionPage import ChromiumPage, ChromiumOptions
    except Exception:
        log("DrissionPage import failed:\n" + traceback.format_exc())
        return 1

    opts = ChromiumOptions()
    opts.set_argument("--start-maximized")
    opts = opts.auto_port()
    page = ChromiumPage(addr_or_opts=opts)
    log("browser open")

    ok = fail = 0
    for broker, url in TARGETS.items():
        try:
            page.get(url, timeout=30)
            time.sleep(6)
            with open(os.path.join(OUT, broker + ".html"), "w", encoding="utf-8") as f:
                f.write(page.html)
            page.get_screenshot(os.path.join(OUT, broker + ".png"), full_page=True)
            log("ok    %-28s %s" % (broker, page.url))
            ok += 1
        except Exception as e:
            log("FAIL  %-28s %s  %s: %s" % (broker, url, type(e).__name__, str(e)[:120]))
            fail += 1

    try:
        page.quit()
    except Exception:
        pass
    log("done: %d ok, %d failed. Zip the capture_forms folder and upload it." % (ok, fail))
    return 0


if __name__ == "__main__":
    try:
        code = main()
    except Exception:
        os.makedirs(OUT, exist_ok=True)
        log("crashed:\n" + traceback.format_exc())
        code = 1
    sys.exit(code)
