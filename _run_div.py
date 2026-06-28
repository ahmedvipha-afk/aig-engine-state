import sys, json, os
os.chdir('C:/aig_engine')
sys.path.insert(0, 'C:/aig_engine')
sys.path.insert(0, 'C:/aig_engine/scripts')
state = json.loads(open('paper_forward_positions.json').read())
open_tickers = list(state['open_positions'].keys())
print('Div scan on', len(open_tickers), 'open positions only')
from scripts.paper_forward_divergence import detect
r = detect(watch_list=open_tickers)
print('Result:', r['summary'])
if r['new_entries']: print('ENTRIES:', [e[0] for e in r['new_entries']])
if r['new_exits']: print('EXITS:', [e['ticker'] for e in r['new_exits']])
errs = r.get('errors', [])
if errs:
    for e in errs[:3]:
        print('ERR:', e)
print('DIV_DONE=true')
