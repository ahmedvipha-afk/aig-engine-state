import time, os, sys
f = sys.argv[1]
final_markers = ['PAPER_FORWARD_DIVERGENCE_DONE', 'Total run time', 'Telegram sent', 'Run complete', 'positions now open', 'open positions', 'DONE', 'done.']
pos = 0
for i in range(300):
    if os.path.exists(f):
        try:
            with open(f, 'r', encoding='utf-8', errors='replace') as fh:
                content = fh.read()
            if len(content) > pos:
                new = content[pos:]
                for line in new.splitlines():
                    print(line, flush=True)
                pos = len(content)
            for m in final_markers:
                if m in content and pos > 50:
                    print('SCRIPT_COMPLETE_DETECTED', flush=True)
                    sys.exit(0)
        except Exception as e:
            print('READ_ERR:', str(e), flush=True)
    time.sleep(5)
print('TIMEOUT_300_POLLS')
