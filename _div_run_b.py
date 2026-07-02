import sys
from pathlib import Path
ROOT = Path("C:/aig_engine")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
wl_file = ROOT / "universe" / "divergence_us_paperforward_watchlist.txt"
full_wl = [ln.strip() for ln in wl_file.read_text().splitlines() if ln.strip() and not ln.strip().startswith("#")]
chunk = full_wl[220:440]
label = "B"
print(f"Div chunk B: {{len(chunk)}} tickers ({{chunk[0]}}..{{chunk[-1]}})", flush=True)
from scripts.paper_forward_divergence import detect
r = detect(watch_list=chunk)
print("DIV_B_SUMMARY=" + r["summary"])
if r["new_entries"]: print("ENTRIES:", [e[0] for e in r["new_entries"]])
if r["new_exits"]: print("EXITS:", [e["ticker"] for e in r["new_exits"]])
if r.get("errors"): [print("ERR:", e) for e in r["errors"][:5]]
print("DIV_CHUNK_B_DONE=true")
