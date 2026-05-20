"""Quick analyzer for the full-universe Divergence 1603 result."""
import json

d = json.load(open('validation_divergence_1d_full.json', encoding='utf-8'))
p = d['portfolio']
print('PORTFOLIO VERDICT:', p['verdict'])
print(f"  trades: {p['portfolio_trades']}  contributors: {p['contributing_tickers']}/{p['universe_size']}  coverage: {p['universe_coverage'] * 100:.2f}%")
print(f"  expectancy: {p['portfolio_expectancy']}  win_rate: {p['portfolio_win_rate']}")
print(f"  Sharpe raw: {p['portfolio_sharpe_raw']}  deflated: {p['portfolio_sharpe_deflated']}")
ci_lo = p.get('portfolio_ci_low')
ci_hi = p.get('portfolio_ci_high')
print(f"  95% CI: ({ci_lo}, {ci_hi})")
print(f"  reasons: {p['reasons']}")
print()
passed = [r for r in d['results'] if r.get('passed')]
print(f'Per-ticker PASSED: {len(passed)}')
for r in passed[:50]:
    print(f"  {r['ticker']:<10} OOS_n={r['oos_n']:>3}  exp={r['oos_expectancy']:>6.3f}  dSharpe={r['oos_sharpe_deflated']:>6.3f}")
near = sorted(
    [r for r in d['results'] if isinstance(r, dict) and not r.get('passed') and r.get('oos_n', 0) >= 30 and r.get('oos_expectancy', 0) >= 1.3],
    key=lambda x: -x['oos_expectancy']
)
print()
print(f'NEAR MISS (n>=30, exp>=1.3, failed gate): {len(near)}')
for r in near[:25]:
    reason = (r.get('reasons') or ['?'])[0]
    print(f"  {r['ticker']:<10} n={r['oos_n']:>3} exp={r['oos_expectancy']:>6.3f} dSh={r['oos_sharpe_deflated']:>6.3f} | {reason}")
print()
# data error / blocked counts
err = [r for r in d['results'] if r.get('verdict') in ('BLOCKED_DATA', 'DATA_ERROR')]
ok = [r for r in d['results'] if r.get('verdict') not in ('BLOCKED_DATA', 'DATA_ERROR')]
print(f'Universe size: {len(d["results"])}  ok: {len(ok)}  blocked/errored: {len(err)}')
