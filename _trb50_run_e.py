import sys
from pathlib import Path
ROOT = Path("C:/aig_engine")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
wl_file = ROOT / "universe" / "trb50_us_paperforward_watchlist.txt"
full_wl = [ln.strip() for ln in wl_file.read_text().splitlines() if ln.strip() and not ln.strip().startswith("#")]
chunk = full_wl[892:]
label = "E"
print(f"TRB50 chunk E: {{len(chunk)}} tickers", flush=True)
from scripts.paper_forward_trb50 import detect
r = detect(watch_list=chunk)
print("TRB50_E_SUMMARY=" + r["summary"])
if r.get("new_entries"): print("ENTRIES:", [e[0] for e in r["new_entries"]])
if r.get("new_exits"): print("EXITS:", [e["ticker"] for e in r["new_exits"]])
if r.get("errors"): [print("ERR:", e) for e in r["errors"][:5]]
print("TRB50_CHUNK_E_DONE=true")
