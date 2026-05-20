"""Quick aggregate analysis of TV Strategy Tester top-10 results."""
import json

d = json.load(open('tv_strategy_tester_ema200_1h_top10.json', encoding='utf-8'))
results = d['results']

print(f'{"Ticker":<6} {"P/L%":>8} {"DD%":>6} {"Trades":>7} {"WR%":>6} {"PF":>6} {"Sharpe":>7} {"AW/AL":>6}  Verdict')
print('-' * 84)
for r in results:
    pf = r['profit_factor']
    dd = r['max_dd_pct']
    pl = r['total_pl_pct']
    wr = r['win_rate_pct']
    awal = r['avg_win_pct'] / max(r['avg_loss_pct'], 0.01)
    sh = r['sharpe']
    sh_s = f'{sh:.3f}' if sh is not None else '  n/a'
    clean = pf >= 1.5 and dd <= 20.0
    losing = pf < 1.0
    near = pf >= 1.0 and dd <= 25.0
    v = 'CLEAN_EDGE' if clean else ('LOSER' if losing else ('NEAR_MISS' if near else 'MARGINAL'))
    print(f'{r["ticker"]:<6} {pl:>+8.2f} {dd:>6.2f} {r["total_trades"]:>7} {wr:>6.2f} {pf:>6.3f} {sh_s:>7} {awal:>5.2f}x  {v}')

print()
total_tr = sum(r['total_trades'] for r in results)
gross_pl_usd = sum(r['total_pl_pct'] / 100 * 100000 for r in results)
mean_pf = sum(r['profit_factor'] for r in results) / len(results)
mean_dd = sum(r['max_dd_pct'] for r in results) / len(results)
mean_wr = sum(r['win_rate_pct'] for r in results) / len(results)
clean = [r for r in results if r['profit_factor'] >= 1.5 and r['max_dd_pct'] <= 20]
near = [r for r in results if r['profit_factor'] >= 1.0 and r['max_dd_pct'] <= 25 and not (r['profit_factor'] >= 1.5 and r['max_dd_pct'] <= 20)]
losers = [r for r in results if r['profit_factor'] < 1.0]

print('Aggregate top-10 (equal-weighted, 6.5y avg horizon):')
print(f'  total trades: {total_tr}')
print(f'  mean profit factor: {mean_pf:.3f}')
print(f'  mean max DD: {mean_dd:.2f}%')
print(f'  mean win rate: {mean_wr:.2f}%')
print(f'  combined equal-weight P/L: ${gross_pl_usd:,.0f} on $1,000,000 (10x100k) -> {gross_pl_usd / 1e6 * 100:+.2f}%')
print()
print(f'CLEAN_EDGE (PF>=1.5 AND DD<=20%): {len(clean)} -> {[r["ticker"] for r in clean]}')
print(f'NEAR_MISS (1.0<=PF<1.5 OR 20%<DD<=25%): {len(near)} -> {[r["ticker"] for r in near]}')
print(f'LOSER    (PF<1.0): {len(losers)} -> {[r["ticker"] for r in losers]}')
