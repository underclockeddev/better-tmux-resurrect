#!/usr/bin/env python3
"""Private tmux save/kill/restore integration; no real sessions or snapshots."""
import importlib.util
import json
import os
from pathlib import Path
import shlex
import subprocess
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("sessions", ROOT / "scripts/claude_sessions.py")
sessions = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sessions)


class Sessions(unittest.TestCase):
    def test_flags_and_quoting(self):
        sid = "11111111-1111-4111-8111-111111111111"
        command = sessions.explicit_command(["claude", "--model", "a b", "--resume", "old", "--fork-session", "--continue"], sid)
        self.assertEqual(shlex.split(command), ["claude", "--model", "a b", "--resume", sid])
        self.assertEqual(shlex.split(sessions.explicit_command(["claude", "--model", "a b", "do the work"], sid)), ["claude", "--model", "a b", "--resume", sid])
        self.assertIn("--model", sessions.explicit_command(["claude", "--resume", "--model", "x"], sid))
        with self.assertRaises(ValueError):
            sessions.explicit_command(["claude", "--unknown", "value"], sid)
        with self.assertRaises(ValueError):
            sessions.explicit_command(["claude", "--print", "hello"], sid)

    def test_private_round_trip(self):
        scratch = ROOT / ".tmp"
        scratch.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="claude-", dir=scratch) as directory:
            work = Path(directory)
            home = work / "home"
            registry = home / ".claude/sessions"
            registry.mkdir(parents=True)
            binary = work / "bin"
            binary.mkdir()
            log = work / "restored.jsonl"
            stub = binary / "claude"
            stub.write_text(r"""#!/usr/bin/env python3
import json, os, pathlib, sys, time
if '--resume' in sys.argv:
    with open(os.environ['RESTORE_LOG'], 'a') as f: f.write(json.dumps(sys.argv[1:]) + '\n')
else:
    pid = os.getpid()
    birth = pathlib.Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()[19]
    row = {'pid': pid, 'procStart': birth, 'sessionId': sys.argv[1]}
    pathlib.Path(os.environ['CLAUDE_SESSIONS_DIR'], f'{pid}.json').write_text(json.dumps(row))
while True: time.sleep(1)
""")
            stub.chmod(0o755)
            env = {k: v for k, v in os.environ.items() if k not in ('TMUX', 'TMUX_PANE', 'XDG_CONFIG_HOME', 'XDG_DATA_HOME', 'CLAUDE_CONFIG_DIR')}
            env.update(HOME=str(home), XDG_RUNTIME_DIR=str(work), TMUX_TMPDIR=str(work), CLAUDE_SESSIONS_DIR=str(registry), RESTORE_LOG=str(log), PATH=str(binary) + ':' + os.environ['PATH'], SHELL='/bin/bash', BASH_ENV='/dev/null')
            socket = work / "socket"
            def tm(*args, check=True):
                return subprocess.run(['tmux', '-S', str(socket), *args], env=env, text=True, capture_output=True, check=check).stdout.strip()
            def wait(predicate):
                for _ in range(100):
                    if predicate(): return
                    time.sleep(.05)
                self.fail('private tmux condition timed out: ' + tm('capture-pane', '-p', '-t', 'parallel:0.0', check=False))
            def stop():
                # kill-server returns before the server and its pane shells
                # exit: a client connecting meanwhile gets "server exited
                # unexpectedly", and a shell writing .bash_history on hangup
                # races the temporary directory's removal. A backgrounded stub
                # survives the hangup, so every pane descendant is killed.
                def tree(pid):
                    kids = []
                    for task in Path(f'/proc/{pid}/task').glob('*'):
                        try: kids += (task / 'children').read_text().split()
                        except OSError: pass
                    return [pid] + [d for kid in kids for d in tree(kid)]
                panes = tm('list-panes', '-a', '-F', '#{pid}', check=False).split()
                pids = [d for pane in panes for d in tree(pane)]
                pids += tm('display', '-p', '#{pid}', check=False).split()
                tm('kill-server', check=False)
                for pid in pids:
                    try: os.kill(int(pid), 9)
                    except ProcessLookupError: pass
                for _ in range(100):
                    if not any(Path(f'/proc/{pid}').exists() for pid in pids): return
                    time.sleep(.05)
                self.fail('private tmux server did not exit: ' + ' '.join(pids))
            def save():
                tm('run-shell', shlex.join([str(ROOT / 'scripts/save.sh'), 'quiet']))
                return (home / '.local/share/tmux/resurrect/last').read_text()
            ids = ['11111111-1111-4111-8111-111111111111', '22222222-2222-4222-8222-222222222222']
            try:
                tm('-f', '/dev/null', 'new-session', '-d', '-s', 'parallel', '-c', str(work), '/bin/bash --noprofile --norc')
                tm('set', '-g', 'default-shell', '/bin/bash')
                tm('set', '-g', 'default-command', '/bin/bash --noprofile --norc')
                tm('set', '-g', '@resurrect-processes', 'claude')
                tm('set', '-g', '@resurrect-strategy-claude', 'session')
                pane0 = tm('display', '-p', '#{pane_id}')
                pane1 = tm('split-window', '-d', '-P', '-F', '#{pane_id}', '-c', str(work), '/bin/bash --noprofile --norc')
                for pane, sid in zip([pane0, pane1], ids):
                    tm('select-pane', '-t', pane, '-T', 'tracked')
                    tm('send-keys', '-t', pane, shlex.join([str(stub), sid, '--model', 'two words']), 'Enter')
                wait(lambda: len(list(registry.glob('*.json'))) == 2)
                text = save()
                for sid in ids: self.assertIn('--resume ' + sid, text)
                self.assertIn("'two words'", text)
                # /clear changes identity without restarting the same process.
                rowfile = next(registry.glob('*.json'))
                original = rowfile.read_text()
                row = json.loads(original)
                updated = '33333333-3333-4333-8333-333333333333'
                row['sessionId'] = updated
                rowfile.write_text(json.dumps(row))
                self.assertIn('--resume ' + updated, save())
                # A reused PID, malformed registry and disappeared process must
                # never reuse identity or fall back to newest in the directory.
                row['procStart'] = '0'
                rowfile.write_text(json.dumps(row))
                missing = save()
                self.assertNotIn('--resume ' + updated, missing)
                self.assertIn(':true', missing)
                rowfile.write_text('{malformed')
                missing = save()
                self.assertNotIn('--resume ' + updated, missing)
                self.assertIn(':true', missing)
                rowfile.write_text(original)
                text = save()
                stop()
                # Restore on a fresh private server with no registry producers.
                tm('-f', '/dev/null', 'new-session', '-d', '-s', 'placeholder', '/bin/bash --noprofile --norc')
                tm('set', '-g', 'default-shell', '/bin/bash')
                tm('set', '-g', 'default-command', '/bin/bash --noprofile --norc')
                tm('set', '-g', '@resurrect-processes', 'claude')
                tm('set', '-g', '@resurrect-strategy-claude', 'session')
                tm('run-shell', shlex.quote(str(ROOT / 'scripts/restore.sh')))
                wait(lambda: log.exists() and len(log.read_text().splitlines()) == 2)
                rows = [json.loads(line) for line in log.read_text().splitlines()]
                self.assertEqual(sorted(row[row.index('--resume') + 1] for row in rows), sorted(ids))
                self.assertTrue(all('two words' in row for row in rows))
                # Dead registry producers cannot identify replacement processes.
                replaced = save()
                for sid in ids: self.assertNotIn('--resume ' + sid, replaced)
                self.assertIn(':true', replaced)
                # Background sessions in this shell do not identify its foreground.
                tm('send-keys', '-t', 'parallel:0.0', 'C-c')
                time.sleep(.1)
                tm('send-keys', '-t', 'parallel:0.0', shlex.join([str(stub), ids[0]]) + ' &', 'Enter')
                time.sleep(.2)
                self.assertNotIn('--resume ' + ids[0], save())
                # Older snapshots naming plain Claude never guess a session.
                result = subprocess.run([str(ROOT / 'strategies/claude_session.sh'), 'claude --continue', str(work)], env=env, text=True, capture_output=True, check=True)
                self.assertEqual(result.stdout.strip(), 'true')
                self.assertIn('skipped', result.stderr)
                # Kill/recreate and stale registry: old identities are not live.
                self.assertEqual(sessions.explicit_command(['claude', '--resume', ids[0]], ids[1]), 'claude --resume ' + ids[1])
            finally:
                stop()


if __name__ == '__main__':
    unittest.main()
