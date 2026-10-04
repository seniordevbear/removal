r"""
run_one.py -- run ONE broker for ONE customer right now, on the VPS.

    Scripts\python.exe run_one.py <user_id> <broker>
    Scripts\python.exe run_one.py 1808 oregonarrestorg
    Scripts\python.exe run_one.py 1808 oregonarrestorg --address "10225 SW Redwing Ter" --city Beaverton --state OR --zip 97007 --save

Uses the same code path as manage.py (removal_dispatch -> sites/<broker>.py),
so the result is a real submission with a real screenshot, uploaded to the
customer's evidence like any other removal. Useful when a customer or the
owner is waiting on one specific site and the queue would take hours.

--address/--city/--state/--zip override the row's stored profile for this
run; add --save to also write them into the customer's removal rows.
--dry-run prints what would be sent and exits.

manage.py can keep running; the row is claimed (step 1) first so the two
cannot collide.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import manage  # noqa: E402  (loads .env, DB config, dispatch, upload)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("user_id", type=int)
    ap.add_argument("broker")
    for f in ("address", "city", "state", "zip", "phone"):
        ap.add_argument("--" + f)
    ap.add_argument("--save", action="store_true", help="persist the overrides into the customer's removal rows")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    conn = manage._db_connect()
    cur = conn.cursor(dictionary=True)
    cur.execute(
        "SELECT id, user_id, target_domain, step, site_url, data FROM results "
        "WHERE user_id = %s AND target_domain = %s AND kind = 1 ORDER BY id LIMIT 1",
        (a.user_id, a.broker))
    row = cur.fetchone()
    if not row:
        print("no kind=1 row for user %s / %s" % (a.user_id, a.broker)); return 2
    d = json.loads(row["data"] or "{}")
    overrides = {k: getattr(a, k) for k in ("address", "city", "state", "zip", "phone") if getattr(a, k)}
    d.update(overrides)
    if overrides and "street" not in overrides and "address" in overrides:
        d["street"] = overrides["address"]

    shown = {k: d.get(k) for k in ("firstname", "lastname", "address", "city", "state", "zip", "phone", "birth_year")}
    print("row id=%s step=%s broker=%s" % (row["id"], row["step"], row["target_domain"]))
    print("profile sent:", json.dumps(shown))
    if a.dry_run:
        return 0

    if overrides and a.save:
        sets = ", ".join("'$.%s', %%s" % k for k in list(overrides) + (["street"] if "address" in overrides else []))
        vals = list(overrides.values()) + ([overrides["address"]] if "address" in overrides else [])
        cur.execute("UPDATE results SET data = JSON_SET(data, " + sets + ") WHERE user_id = %s AND kind = 1",
                    tuple(vals) + (a.user_id,))
        conn.commit()
        print("saved overrides into %d removal rows" % cur.rowcount)

    manage._set_step(conn, row["id"], 1, "run_one claim")
    try:
        path = manage.removal_dispatch(
            manage.socketio, row["target_domain"], row["site_url"],
            row["id"], row["user_id"],
            d.get("email"), d.get("firstname"), d.get("lastname"),
            d.get("city"), d.get("zip"), d.get("state"), d.get("age"),
            d.get("address"), d.get("phone"),
            d.get("birth_day"), d.get("birth_month"), d.get("birth_year"),
            d.get("area_code"), d.get("street") or d.get("address"), d.get("county"),
        )
    except Exception as e:
        manage._set_step(conn, row["id"], 3, "run_one: %s: %s" % (type(e).__name__, e))
        print("FAILED:", type(e).__name__, e)
        raise

    manage._set_step(conn, row["id"], 2)
    cur.execute("UPDATE results SET last_removed_at = NOW() WHERE id = %s", (row["id"],))
    conn.commit()
    print("screenshot:", path)
    if path and os.path.exists(path):
        res = manage.upload_file_to_server(
            manage.REMOVAL_UPLOAD_URL_TEMPLATE.format(domain=row["target_domain"], user_id=row["user_id"]), path)
        print("uploaded to customer evidence:", "ok" if res else "FAILED (file kept locally)")
    else:
        print("broker returned no screenshot file")
    cur.close(); conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
