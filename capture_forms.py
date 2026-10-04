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


# Round 2 (2026-10-04): pages Cloudflare or JS hide from the web server.
#     Scripts\python.exe capture_forms.py round2
ROUND2 = {
    "allpeoplecom-removal": "https://allpeople.com/removal",
    "advancedbackgroundcheckscom-optout": "https://www.advancedbackgroundchecks.com/opt-out",
    "advancedbackgroundcheckscom-dns": "https://www.advancedbackgroundchecks.com/do-not-sell",
    "alescodatacom-privacycenter": "https://alescodata.com/privacy-center/",
    "brandwatchcom-dsar": "https://www.brandwatch.com/legal/data-subject-access-request/",
    "courtrecordsus-optout": "https://courtrecords.us/optout/",
    "acbjcom-privacy": "https://www.acbj.com/privacy",
    "bizjournalscom-privacy": "https://www.bizjournals.com/privacy",
    "ohioarrestsorg-contact": "https://www.ohioarrests.org/contact-form",
    "careerbuildercom-onetrust": "https://privacyportal.onetrust.com/webform/a7e660bb-bfdf-4dd0-b65c-49ce834f786e/5edf5e8a-3d83-4e49-9d3a-cb2fb031f49f",
    "callersmartcom-data": "https://www.callersmart.com/data",
}

# Round 3: only what is still unseen.
#     Scripts\python.exe capture_forms.py round3
ROUND3 = {
    "callersmartcom-data": "https://www.callersmart.com/data",
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
    arg = sys.argv[1] if len(sys.argv) > 1 else ""
    targets = {"round2": ROUND2, "round3": ROUND3}.get(arg, TARGETS)
    for broker, url in targets.items():
        try:
            page.get(url, timeout=30)
            time.sleep(6)
            # Cloudflare "Just a moment" interstitial: give it time and nudge
            # the checkbox the way the broker scripts do (callersmart needed it).
            for _ in range(12):
                if "just a moment" not in (page.title or "").lower():
                    break
                try:
                    page.actions.click()
                    page.actions.key_down("TAB"); time.sleep(0.2); page.actions.key_up("TAB"); time.sleep(0.2)
                    page.actions.key_down("SPACE"); time.sleep(0.2); page.actions.key_up("SPACE")
                except Exception:
                    pass
                time.sleep(5)
            if "just a moment" in (page.title or "").lower():
                log("CF    %-28s still behind the Cloudflare challenge after 60s" % broker)
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
