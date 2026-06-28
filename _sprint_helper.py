import sys, json
from pathlib import Path
ROOT = Path("C:/aig_engine")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
state = json.loads((ROOT / "paper_forward_positions.json").read_text())
open_tickers = list(state["open_positions"].keys())
print(f"Div scan on {len(open_tickers)} open (weekend)")
from scripts.paper_forward_divergence import detect
r = detect(watch_list=open_tickers)
print(f"Result: {r[chr(39)]summary{chr(39)]}")
if r["new_exits"]: print("EXITS:", [e["ticker"] for e in r["new_exits"]])
if r["errors"]: [print("ERR:", e) for e in r["errors"][:3]]
print("DIV_DONE=true")
