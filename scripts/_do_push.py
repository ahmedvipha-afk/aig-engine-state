import subprocess, sys
r = subprocess.run(['git', 'push', 'origin', 'main'], timeout=180, cwd=r'C:\aig_engine')
sys.exit(r.returncode)
