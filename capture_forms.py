r"""
capture_forms.py — run ON THE VPS from C:\wonderful\removal:
    python capture_forms.py
Opens each listed broker's opt-out page with the pipeline's browser and saves
    capture_forms\<broker>.html   (full page source)
    capture_forms\<broker>.png    (screenshot)
Zip the capture_forms folder and upload it to /root/privacyduck/ on the web
server. That is everything needed to repair the broker scripts without
guessing. Takes ~5 minutes; no customer data is entered.
"""
import os, sys, time, mysql.connector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from DrissionPage import ChromiumPage, ChromiumOptions

# brokers that crashed most 24 Sep-2 Oct, plus the one that never succeeded
BROKERS = ["acbjcom","accudatacom","advancedpeoplesearchcom","affinitysolutionscom","acxiomcom",
           "allpeoplecom","archivescom","advancedbackgroundcheckscom","alescodatacom","americaphonebookcom",
           "findpeoplesearchcom","brandwatchcom","completemedicallistscom","fmadatacom","contactoutcom",
           "demystcom","beenverifiedcom","bumpercom","faradayio","backgroundcheckco",
           "arkansascourtrecordsus","ohioarrestsorg"]

def env(k, d=""):
    v = os.getenv(k)
    if v is None:
        try:
            for line in open(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")):
                if line.startswith(k + "="):
                    v = line.split("=", 1)[1].strip().strip("'\"")
        except OSError:
            pass
    return v or d

conn = mysql.connector.connect(host=env("DB_HOST"), port=int(env("DB_PORT", "25060")), user=env("DB_USER"),
                               password=env("DB_PASSWORD"), database=env("DB_NAME"))
cur = conn.cursor()
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "capture_forms")
os.makedirs(out, exist_ok=True)
opts = ChromiumOptions(); opts.set_argument("--start-maximized"); opts = opts.auto_port()
page = ChromiumPage(addr_or_opts=opts)
for b in BROKERS:
    cur.execute("SELECT COALESCE(NULLIF(removal_url,''), site_url) FROM results WHERE target_domain=%s AND kind=1 LIMIT 1", (b,))
    row = cur.fetchone()
    url = row[0] if row and row[0] else "https://" + b
    try:
        page.get(url, timeout=30); time.sleep(6)
        open(os.path.join(out, b + ".html"), "w", encoding="utf-8").write(page.html)
        page.get_screenshot(os.path.join(out, b + ".png"), full_page=True)
        print("ok  ", b, page.url)
    except Exception as e:
        print("FAIL", b, url, type(e).__name__, str(e)[:80])
page.quit(); cur.close(); conn.close()
print("done ->", out)
