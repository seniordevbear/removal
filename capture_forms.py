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

# Round 4 (2026-10-04 evening): every broker that crashed 5+ times on the new
# code, plus the confirmation-mailbox login page the e-mail-link brokers need.
#     Scripts\python.exe capture_forms.py round4
ROUND4 = {
    "mailbox-login": "https://mail1.privacypros.com/surgeweb",
    "brooksimcom": "https://www.brooksim.com/privacy-form",
    "myypcom": "https://www.myyp.com/optout",
    "ncsolutionscom": "https://ncsolutions.com/do-not-sell-my-information/",
    "numlookupcom": "https://www.numlookup.com/opt_out",
    "nuwbercom": "https://nuwber.com/",
    "oldphonebookcom": "https://www.oldphonebook.com/",
    "bytwocom": "https://privacyportal.onetrust.com/webform/e32c5e49-85c5-4969-bfa8-8cde49952e1f/6034339d-69de-41fc-829f-7b8b51d9fabe",
    "onlinepeoplesearchcom": "https://onlinepeoplesearch.com/optout",
    "aritotlecom": "https://www.aristotle.com/privacy/do-not-sell-my-personal-info/",
    "mediadirectcom": "https://360-media-direct.privacy.saymine.io/360_Media_Direct",
    "kidslivesafecom": "https://www.kidslivesafe.com/help-center/privacy-requests",
    "contacts411com": "https://contacts411.com/opt-out",
    "searchpeoplefreecom": "https://www.searchpeoplefree.com/opt-out",
    "peoplesearchnowcom": "https://www.peoplesearchnow.com/opt-out",
    "idcrawlcom": "https://www.idcrawl.com/remove-my-information",
    "kingmarketinggroupcom": "https://kingmarketinggroup.com/do-not-sell-my-personal-information/",
    "l2politicalcom": "https://www.l2-data.com/california-privacy-rights-for-california-residents-only/",
    "limeleadscom": "https://www.limeleads.com/do-not-sell-my-data-request/",
    "cognismcom": "https://www.cognism.com/data-opt-out",
    "idtruecom": "https://www.idtrue.com/optout",
    "i360com": "https://privacyportal.onetrust.com/webform/77dff651-9f08-40cd-99fe-a7c487b2504d/fd25e566-5931-4987-ae94-13ffd3306913",
    "inmarketcom": "https://inmarket.com/opt-out/",
    "jmrmediacom": "https://jmr-media.com/do-not-sell-my-personal",
    "mediawallahcom": "https://mediawallah.com/donotsell/",
    "internetbrandscom": "https://mynt-test-privacy.my.onetrust.com/webform/ebe19500-bc8d-487f-9d89-98fde8b270e2/6345c7af-b8c5-4ee6-a6f7-9418a3fe079b",
    "optoutprescreencom": "https://www.optoutprescreen.com/",
    "hirerightcom": "https://www.hireright.com/u-s-state-consumer-privacy-rights-request-form",
    "belardiwongcom": "https://privacyportal.onetrust.com/webform/3d2d5e0c-bd98-46b8-906c-ede68a6f6a80/400f54ed-fcbb-4749-ab5b-32f491c72390",
}

# Round 5: forms that round 4 showed living inside an <iframe> (the outer
# page was captured, the form was not). Open the iframe source directly.
#     Scripts\python.exe capture_forms.py round5
ROUND5 = {
    "mailbox-login": "https://mail1.privacypros.com/surgeweb",
    "brooksimcom-iframe": "https://dsr.trustsuperset.com/?orgId=2dc76d0a-78d2-4492-9fc1-39da892fc0d5",
    "hirerightcom-iframe": "https://info.hireright.com/l/650513/2024-10-08/561z6m",
    "mediawallahcom-iframe": "https://privacyportal-eu-cdn.onetrust.com/dsarwebform/e3df3040-c675-462f-99c4-15c05ac3bf5c/545897d5-7793-4317-921b-4efe187a2c02.html",
    "bytwocom-anteriad": "https://anteriad.com/privacy-policy#your-marketing-and-opt-out-choices",
    "inmarketcom-center": "https://preferences.inmarket.com/",
}

# Round 6 (2026-10-09): the next band of brokers failing on every run.
#     Scripts\python.exe capture_forms.py round6
ROUND6 = {
    "golookupcom": "https://golookup.com/support/optout",
    "endatocom": "https://go.enformion.com/privacy-policy/opt-out/",
    "equifaxcom": "https://myprivacy.equifax.com/personal-info",
    "fastpeoplesearchinfo": "https://fastpeoplesearch.info/optout",
    "fetcherai": "https://app.fetcher.ai/opt-out",
    "giantpartnerscom": "https://giantpartners.com/do-not-sell-my-personal-info-all-other-states/",
    "freebackgroundcheckio": "https://freebackgroundcheck.io/optout",
    "freepeoplesearchio": "https://freepeoplesearch.io/optout",
    "getemailscom": "https://app.retention.com/optout/",
    "greatlakeslistscom": "https://greatlakeslists.com/opt_out_request.php",
    "gostratacom": "https://www.gostrata.com/do-not-sell-my-personal-information/",
    "herecom": "https://www.here.com/en-gb/privacy/here-data-subject-request",
    "idstrongcom": "https://www.idstrong.com/privacyform/",
    "idcrawlcom": "https://www.idcrawl.com/remove-my-information",
    "idtruecom": "https://www.idtrue.com/optout",
}

# Round 7 (2026-10-09): NEW brokers — the 60 people-search sites from the
# Phonetix gap list confirmed by 10+ sources. Nothing is scripted for these
# yet; the capture is the first step.
#     Scripts\python.exe capture_forms.py round7
ROUND7 = {
    "zoominfocom": "https://www.zoominfo.com/about-zoominfo/privacy-manage-profile",
    "transunioncom": "https://www.transunion.com/credit-freeze/place-credit-freeze",
    "lead411com": "https://lead411.com/your-privacy-choices/",
    "liverampcom": "https://submit-irm.trustarc.com/services/validation/697ea013-8e66-44aa-94c5-fa9d38dd439c",
    "melissacom": "https://apps.melissa.com/user/consumerprivacy.aspx",
    "peopledatalabscom": "https://www.peopledatalabs.com/opt-out-form",
    "peoplewhizcom": "https://www.peoplewhiz.com/remove-my-info",
    "thomsonreuterscom": "https://privacyportal-cdn.onetrust.com/dsarwebform/dbf5ae8a-0a6a-4f4b-b527-",
    "infopaycom": "https://www.infopay.com/contact",
    "peopleconnectus": "https://suppression.peopleconnect.us/login",
    "civisanalyticscom": "https://www.civisanalytics.com/privacy-policy/#ccpa",
    "enformioncom": "https://www.enformion.com/do-not-sell/",
    "nielsencom": "https://www.nielsen.com/legal/optout-page/",
    "peoplelookercom": "https://www.peoplelooker.com/f/optout/search",
    "propertyradarcom": "https://www.propertyradar.com/privacy-policy",
    "propertyreachcom": "https://www.propertyreach.com/privacy-rights",
    "oraclecom": "https://datacloudoptout.oracle.com/",
    "rrdcom": "https://www.rrd.com/do-not-sell",
    "thedatatrustcom": "https://thedatatrust.com/do-not-sell-my-personal-information/",
    "crunchbasecom": "https://preferences.crunchbase.com/form/opt_out",
    "firstorioncom": "https://privacy.firstorion.com/",
    "lotamecom": "https://www.lotame.com/about-lotame/privacy/lotames-opt-out/",
    "merklecom": "https://www.merkleinc.com/en/privacy-policy/data-product-privacy-notice/control-your-personal-information.html",
    "publicrecordsnowcom": "https://www.publicrecordsnow.com/static/view/optout/",
    "targetsmartcom": "https://privacy.targetsmart.com/",
    "uscom": "https://idm.us.com/do-not-sell-my-personal-information/",
    "clearviewai": "https://www.clearview.ai/privacy-and-requests",
    "edvisorscom": "https://www.edvisors.com/delete-request/",
    "freephonetracercom": "https://www.beenverified.com/app/optout/search",
    "nationalpublicdatacom": "https://nationalpublicdata.com/optout.html",
    "reholdcom": "https://rehold.com/control/privacy",
    "sterlingai": "https://sterling.ai/privacy-policy/",
    "tapadcom": "https://crportal.tapad.com",
    "telephonelistsbiz": "https://www.evs7.com/personal-information-request",
    "uspeoplesearchcom": "https://uspeoplesearch.com/purge-my-data/",
    "innoviscom": "https://www.innovis.com/personal/securityFreeze",
    "peoplefindercom": "https://peoplefinder.com/optout.php",
    "peoplefindersdaascom": "https://peoplefindersdaas.com/",
    "persopocom": "http://info.persopo.com/opt-out.html",
    "reversephonelookupcom": "https://www.intelius.com/privacy-center",
    "unitedstatesphonebookcom": "http://www.unitedstatesphonebook.com/contact.php",
    "voterrecordscom": "https://voterrecords.com/faq",
    "attomdatacom": "https://ccpa.attomdata.com/",
    "dobsearchcom": "https://www.dobsearch.com/people-finder/block-record-request.php",
    "easybackgroundcheckscom": "https://www.intelius.com/suppression-center/",
    "forewarncom": "https://www.forewarn.com/privacy-policy/",
    "locatesmartercom": "https://forms.locatesmarter.com/optoutform",
    "northcarolinaresidentdatabasecom": "https://northcarolinaresidentdatabase.com/opt-out",
    "peoplesearchexpertcom": "https://www.peoplesearchexpert.com/",
    "phonebookscom": "https://www.phonebooks.com/opt-out",
    "ufindname": "https://ufind.name/opt-out",
    "ancestrycom": "https://support.ancestry.com/s/reportissue?language=en_US",
    "confidentialphonelookupcom": "https://www.confidentialphonelookup.com/removals/",
    "corporationwikicom": "https://www.corporationwiki.com/profiles/public",
    "familysearchorg": "https://www.familysearch.org/en/help/helpcenter/article/how-do-i-remove-vitals-information-in-family-tree",
    "floridaresidentsdirectorycom": "https://www.floridaresidentsdirectory.com/opt-out",
    "ohioresidentdatabasecom": "https://www.ohioresidentdatabase.com/opt-out",
    "peoplesearchorg": "https://people-search.org",
    "reonomycom": "https://joindeleteme.com/opt-out-guides/reonomy-opt-out-guide/",
    "searchusapeoplecom": "https://www.searchusapeople.com/data-removal-request/",
}

# Round 8 (2026-10-11): SEARCH-RESULT pages for the free-exposure scan.
# Only 7 of 416 sites_scan modules are real, so the lead magnet can check 5
# sites and tells people they appear on 0-4. These are people-search sites we
# can already REMOVE from, so anything found is actionable. Each capture is a
# search for a common name; what matters is the shape of the results list.
#     Scripts\python.exe capture_forms.py round8
ROUND8 = {
    "scan-truepeoplesearchcom": "https://www.truepeoplesearch.com/results?name=John%20Smith&citystatezip=Texas",
    "scan-radariscom": "https://radaris.com/p/John/Smith/",
    "scan-mylifecom": "https://www.mylife.com/search?searchTerm=John+Smith",
    "scan-beenverifiedcom": "https://www.beenverified.com/people/john-smith/",
    "scan-inteliuscom": "https://www.intelius.com/people-search/John-Smith/",
    "scan-peoplefinderscom": "https://www.peoplefinders.com/name/john-smith",
    "scan-nuwbercom": "https://nuwber.com/search?name=John+Smith",
    "scan-cyberbackgroundcheckscom": "https://www.cyberbackgroundchecks.com/people/john-smith",
    "scan-searchpeoplefreecom": "https://www.searchpeoplefree.com/find/john-smith",
    "scan-anywhocom": "https://www.anywho.com/people/John+Smith/",
    "scan-zabasearchcom": "https://www.zabasearch.com/people/john+smith/",
    "scan-clustrmapscom": "https://clustrmaps.com/persons/John-Smith",
    "scan-ussearchcom": "https://www.ussearch.com/people-search/john-smith/",
    "scan-instantcheckmatecom": "https://www.instantcheckmate.com/people/john-smith/",
    "scan-smartbackgroundcheckscom": "https://www.smartbackgroundchecks.com/people/john-smith",
}

# Round 9 (2026-10-19). The ElementNotFoundError cohort: between 17 and 19
# Oct these 18 brokers produced 2,045 of the pipeline's failures, every one
# recorded as "No element found." with no clue which selector died. Two are
# already known to have moved - completemailinglists 404s on the path the
# script uses and its form is now a HubSpot embed at
# /consumer-privacy-request, and lexisnexis only links to /optrequest from
# the page the script opens - and the rest need their live DOM before
# anything can be written honestly.
ROUND9 = {
    "clustrmapscom": "https://clustrmaps.com/bl/opt-out",
    "clearbitcom": "https://preferences.clearbit.com",
    "completemailinglistscom": "https://www.completemailinglists.com/consumer-privacy-request",
    "peoplesearchnowcom": "https://www.peoplesearchnow.com/opt-out",
    "optoutprescreencom": "https://www.optoutprescreen.com/",
    "contacts411com": "https://contacts411.com/opt-out",
    "conversantmediacom": "https://legal.epsilon.com/dsr/",
    "corelogiccom": "https://www.corelogic.com/employee-applicant-privacy-form/",
    "costarcom": "https://privacyportal.onetrust.com/webform/69fc85af-b1e4-4eae-966b-cf91a3cca94c/5f1a45b9-bb79-49dc-ad4d-064548192246",
    "optoutlexisnexiscom": "https://optout.lexisnexis.com/optrequest",
    "leadcrunchcom": "https://getrev.ai/privacy-request/",
    "advancedbackgroundcheckscom": "https://www.advancedbackgroundchecks.com/opt-out",
    "idstrongcom": "https://www.idstrong.com/remove-my-information/",
    "nuwbercom": "https://nuwber.com/removal/link",
    "deepsynccom": "https://privacy.deepsync.com/",
    "datatrustcom": "https://thedatatrust.com/do-not-sell-my-personal-information/",
    "datastreamgroupcom": "https://www.godaddy.com/legal/agreements/do-not-share",
    "cowencom": "https://forian.com/privacy-do-not-sell-share/",
}

# Round 10 (2026-10-20). The round-9 pages that turned out to be the wrong
# page: the scripts' URLs now redirect to a policy page, a search funnel or
# a homepage, and the real form is elsewhere. These are the real forms,
# found from the captures and the sites' own privacy notices.
ROUND10 = {
    "idstrongcom": "https://submit-irm.trustarc.com/services/validation/8bec428f-079d-421f-8b6b-3ede6c5d5930/?brandId=beaae2c1-19bc-4369-9a5c-21ce0c61625c",
    "datastreamgroupcom": "https://privacyportal.onetrust.com/webform/9c7cf400-5967-40b4-9f91-7df7b5eff86b/e5068a23-1539-4b4a-978a-8d5320ab0de7",
    "datatrustcom": "https://thedatatrust.com/your-privacy-choices/",
    "cowencom": "https://forian.com/privacy-policy/",
    "optoutlexisnexiscom": "https://optout.lexisnexis.com/optrequest",
    "costarcom": "https://privacyportal.onetrust.com/webform/69fc85af-b1e4-4eae-966b-cf91a3cca94c/5f1a45b9-bb79-49dc-ad4d-064548192246",
}

# Round 11 (2026-10-20). From the round-10 log: forian's /privacy-policy/
# redirects to its homepage, whose footer links a dedicated consumer-requests
# page; costar's OneTrust webform id returned 135 bytes from the VPS as well
# as from the web server, so the id is dead and costar.com itself is behind
# an Akamai bot wall that 403s every fetch from the server - only a real
# browser on the VPS can read its privacy notice for the current form.
ROUND11 = {
    "cowencom": "https://forian.com/privacy-consumer-requests/",
    "costarcom": "https://www.costar.com/about/privacy-notice",
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

    # Chrome launch with a timeout and diagnostics. Rounds 6 and 7 on
    # 2026-10-10 sat at this line forever; earlier rounds took 2-3 minutes to
    # get past it. The launch runs in a thread so a hang is reported instead
    # of waited on, and it is retried once with a fresh temp profile.
    try:
        import psutil
        n_chrome = sum(1 for p in psutil.process_iter(["name"]) if (p.info["name"] or "").lower().startswith("chrome"))
        log("chrome processes already running: %d" % n_chrome)
    except Exception:
        pass
    import threading, tempfile

    def _launch(fresh_profile):
        opts = ChromiumOptions()
        opts.set_argument("--start-maximized")
        opts.set_argument("-no-first-run")
        opts = opts.auto_port()
        if fresh_profile:
            opts.set_user_data_path(tempfile.mkdtemp(prefix="pd-capture-"))
        box = {}

        def _go():
            try:
                box["page"] = ChromiumPage(addr_or_opts=opts)
            except Exception as e:
                box["err"] = e
        t = threading.Thread(target=_go, daemon=True)
        t.start()
        t.join(120)
        if t.is_alive():
            return None, "Chrome did not start within 120s"
        return box.get("page"), (str(box.get("err")) if box.get("err") else None)

    page, err = _launch(False)
    if page is None:
        log("browser launch failed (%s); retrying with a fresh temp profile" % err)
        page, err = _launch(True)
    if page is None:
        log("browser launch failed again (%s). Stop manage.py, close every Chrome window, "
            "then run this again. If it still hangs, run: taskkill /IM chrome.exe /F" % err)
        return 1
    log("browser open")

    ok = fail = 0
    arg = sys.argv[1] if len(sys.argv) > 1 else ""
    targets = {"round2": ROUND2, "round3": ROUND3, "round4": ROUND4, "round5": ROUND5, "round6": ROUND6, "round7": ROUND7, "round8": ROUND8, "round9": ROUND9, "round10": ROUND10, "round11": ROUND11}.get(arg, TARGETS)
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
