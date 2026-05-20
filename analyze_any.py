"""Generic analyzer for any validation JSON output."""
import json
import sys

paths = sys.argv[1:] if len(sys.argv) > 1 else ['validation_divergence_1d_full.json']
for path in paths:
    print('=' * 70)
    print(f'FILE: {path}')
    try:
        d = json.load(open(path, encoding='utf-8'))
    except FileNotFoundError:
        print('  NOT FOUND — skipping')
        continue
    p = d.get('portfolio')
    if p:
        print(f"  Portfolio: {p['verdict']}")
        print(f"    trades={p['portfolio_trades']}  contrib={p['contributing_tickers']}/{p['universe_size']}  cov={p['universe_coverage'] * 100:.2f}%")
        print(f"    exp={p['portfolio_expectancy']}  wr={p['portfolio_win_rate']}  sr_raw={p['portfolio_sharpe_raw']}  sr_def={p['portfolio_sharpe_deflated']}")
        if p['reasons']:
            print(f"    fails: {p['reasons']}")
    rs = d.get('results', [])
    blocked = [r for r in rs if r.get('verdict') in ('BLOCKED_DATA', 'DATA_ERROR')]
    ok = [r for r in rs if r.get('verdict') not in ('BLOCKED_DATA', 'DATA_ERROR')]
    passed = [r for r in rs if r.get('passed')]
    near = [r for r in rs if r.get('verdict') == 'FAIL' and r.get('oos_n', 0) >= 30 and r.get('oos_expectancy', 0) >= 1.3]
    relaxed = [r for r in rs if r.get('oos_n', 0) >= 30 and r.get('oos_expectancy', 0) >= 1.0]
    print(f'  total={len(rs)}  ok={len(ok)}  blocked={len(blocked)}  per-ticker-passed={len(passed)}  near-miss(n>=30,exp>=1.3)={len(near)}  relaxed(n>=30,exp>=1.0)={len(relaxed)}')
    if blocked:
        # show ONE blocked ticker as sample
        b = blocked[0]
        print(f'    sample block: {b["ticker"]} | {b.get("reasons", ["?"])[0]}')
    if near:
        near.sort(key=lambda r: -r['oos_expectancy'])
        for r in near[:10]:
            print(f'    near: {r["ticker"]:<10} n={r["oos_n"]:>3}  exp={r["oos_expectancy"]:>6.3f}  dSh={r["oos_sharpe_deflated"]:>6.3f}')
