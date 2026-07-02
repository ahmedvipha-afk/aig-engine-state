#!/usr/bin/env python3
"""verify_pushed.py -- assert the local branch actually LANDED on the remote.

The sprint worker (headless `claude -p`) must run this after any push and copy the
verdict verbatim into HANDOFF. NEVER record "pushed" unless this prints PUSH_VERIFIED.
This exists because a push can fail (GH001 oversized blob, sandbox-approval block,
credential dialog) while the worker still commits locally -- which once let origin lag
9 days silently. Honesty is now script-enforced, not left to model discretion.

Usage:  python scripts/verify_pushed.py [remote] [branch]   (defaults: origin main)

Verdict (machine-readable, copied verbatim into HANDOFF):
  PUSH_VERIFIED <sha>                              exit 0  -- HEAD == remote branch (landed)
  PUSH_FAILED_LOCAL_ONLY head=<h> remote=<r>       exit 1  -- diverged / did not land
  PUSH_UNVERIFIED_FETCH_FAILED <detail>            exit 2  -- could not reach remote (unknown)
Exit 0 ONLY when the remote ref provably equals local HEAD.
"""
import subprocess
import sys


def git(*args):
    return subprocess.run(['git', *args], capture_output=True, text=True, timeout=180)


def main():
    remote = sys.argv[1] if len(sys.argv) > 1 else 'origin'
    branch = sys.argv[2] if len(sys.argv) > 2 else 'main'

    fetched = git('fetch', remote, branch)
    if fetched.returncode != 0:
        detail = (fetched.stderr or fetched.stdout).strip().replace('\n', ' ')[:120]
        print(f"PUSH_UNVERIFIED_FETCH_FAILED {detail}")
        return 2

    head = git('rev-parse', 'HEAD').stdout.strip()
    remote_sha = git('rev-parse', 'FETCH_HEAD').stdout.strip()

    if head and remote_sha and head == remote_sha:
        print(f"PUSH_VERIFIED {head}")
        return 0

    print(f"PUSH_FAILED_LOCAL_ONLY head={head} remote={remote_sha}")
    return 1


if __name__ == '__main__':
    sys.exit(main())
