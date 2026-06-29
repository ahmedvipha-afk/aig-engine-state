import sys, json
from pathlib import Path
ROOT = Path("C:/aig_engine")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
STEP = sys.argv[1] if len(sys.argv) > 1 else "div"
if STEP == "div":
    state = json.loads((ROOT / "paper_forward_positions.json").read_text())
    open_tickers = list(state["open_positions"].keys())
    print("Div scan on", len(open_tickers), "open positions")
    from scripts.paper_forward_divergence import detect
    r = detect(watch_list=open_tickers)
    print("DIV_SUMMARY=" + r["summary"])
    if r["new_entries"]: print("ENTRIES:", [e[0] for e in r["new_entries"]])
    if r["new_exits"]: print("EXITS:", [e["ticker"] for e in r["new_exits"]])
    if r["errors"]:
        for e in r["errors"][:5]: print("ERR:", e)
    print("DIV_DONE=true")
elif STEP == "trb50":
    from scripts.paper_forward_trb50 import detect, STATE_FILE
    state = json.loads(STATE_FILE.read_text())
    open_tickers = list(state["open_positions"].keys())
    print("TRB50 scan on", len(open_tickers), "open positions")
    r = detect(watch_list=open_tickers)
    print("TRB50_SUMMARY=" + r.get("summary", "error"))
    if r.get("new_entries"): print("ENTRIES:", [e[0] for e in r["new_entries"]])
    if r.get("new_exits"): print("EXITS:", [c["ticker"] for c in r["new_exits"]])
    print("TRB50_DONE=true")
elif STEP == "dashboard":
    from scripts.generate_dashboard import main as gen_dashboard
    gen_dashboard()
    print("DASHBOARD_DONE=true")
