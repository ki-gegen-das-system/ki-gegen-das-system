import time, os, sys
sys.path.insert(0, "forschung")
import daten
for tf, s, e in (("5Min", "2019-01-01T00:00:00Z", "2019-12-31T00:00:00Z"), ("1Day", "2018-01-01T00:00:00Z", "2026-01-01T00:00:00Z")):
    for i in range(2):
        t0 = time.time()
        r = daten.call(daten.DATA, "/v2/stocks/bars", {"symbols": "XLV", "timeframe": tf, "start": s, "end": e, "limit": 10000, "feed": "sip"})
        n = sum(len(v) for v in (r.get("bars") or {}).values())
        print(f"{tf}: {n} Kerzen in {time.time() - t0:.2f}s, weitere Seite: {bool(r.get('next_page_token'))}", flush=True)
