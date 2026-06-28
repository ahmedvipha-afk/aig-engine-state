import sys, os
os.chdir('C:/aig_engine')
sys.path.insert(0, 'C:/aig_engine')
sys.path.insert(0, 'C:/aig_engine/scripts')
from scripts.paper_forward_trb50 import detect
r = detect()
print('TRB50 Result:', r.get('summary', r))
if r.get('new_entries'): print('ENTRIES:', r['new_entries'])
if r.get('new_exits'): print('EXITS:', [e['ticker'] for e in r['new_exits']])
errs = r.get('errors', [])
if errs:
    for e in errs[:3]:
        print('ERR:', e)
print('TRB50_DONE=true')
