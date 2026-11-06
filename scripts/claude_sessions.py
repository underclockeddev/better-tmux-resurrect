#!/usr/bin/env python3
"""Exact Claude identity from the live registry; never infer by cwd or mtime.

Linux /proc birth ticks fence PID reuse. Only the foreground process group
of a pane is eligible: a background agent in the same shell is not that pane.
The registry is produced by Claude, not maintained by tmux-resurrect.
"""
import json
import os
from pathlib import Path
import shlex
import sys
import uuid


def process(pid):
    root = Path(f"/proc/{pid}")
    stat = root.joinpath("stat").read_text().rsplit(")", 1)[1].split()
    argv = [os.fsdecode(a) for a in root.joinpath("cmdline").read_bytes().split(b"\0") if a]
    return int(stat[1]), int(stat[2]), int(stat[5]), stat[19], argv


def claude_argv(argv):
    if len(argv) > 1 and Path(argv[1]).name == "claude" and Path(argv[0]).name in ("node", "bun", "python3", "bash"):
        argv = argv[1:]
    if not argv or Path(argv[0]).name != "claude":
        raise ValueError("not an interactive Claude command")
    return argv


def explicit_command(argv, session_id):
    """Keep flags and their argument boundaries, replace conversation selectors."""
    argv = claude_argv(argv)
    if any(any(c in arg for c in "\n\r\t") for arg in argv):
        raise ValueError("argument cannot fit a snapshot record")
    args = []
    index = 1
    while index < len(argv):
        arg = argv[index]
        index += 1
        if arg in ("-p", "--print") or arg.startswith("--print="):
            raise ValueError("noninteractive command")
        if arg in ("--resume", "-r", "--session-id"):
            # --resume may open a picker without an argument. Do not eat the
            # next flag in that case. The live registry still provides the ID.
            if index < len(argv) and not argv[index].startswith("-"):
                index += 1
        elif arg in ("--continue", "-c", "--fork-session"):
            continue
        elif arg.startswith(("--resume=", "--session-id=")):
            continue
        else:
            args.append(arg)
    return shlex.join(["claude", *args, "--resume", str(uuid.UUID(session_id))])


def registry():
    directory = Path(os.environ.get("CLAUDE_SESSIONS_DIR", str(Path(os.environ.get("CLAUDE_CONFIG_DIR", str(Path.home() / ".claude"))) / "sessions")))
    entries = []
    for file in directory.glob("*.json"):
        try:
            row = json.loads(file.read_text())
            pid = int(row["pid"])
            parent, group, foreground, birth, argv = process(pid)
            if str(row["procStart"]) != birth or group != foreground:
                continue
            command = explicit_command(argv, row["sessionId"])
            entries.append((pid, birth, command))
        except (OSError, ValueError, KeyError, TypeError, IndexError, StopIteration):
            continue
    return entries


def belongs_to(pid, birth, pane_pid):
    seen = set()
    while pid > 1 and pid not in seen:
        seen.add(pid)
        parent, _, _, current_birth, _ = process(pid)
        if birth is not None and current_birth != birth:
            return False
        if pid == pane_pid:
            return True
        pid, birth = parent, None
    return False


def capture():
    entries = registry()
    for line in sys.stdin:
        fields = line.rstrip("\n").split("\t")
        command = ""
        try:
            pane_pid = int(fields[10])
            matches = []
            for pid, birth, cmd in entries:
                try:
                    if belongs_to(pid, birth, pane_pid):
                        matches.append(cmd)
                except (OSError, ValueError, IndexError):
                    continue
            foreground_claude = fields[9] == "claude"
            try:
                foreground = process(pane_pid)[2]
                claude_argv(process(foreground)[4])
                foreground_claude = belongs_to(foreground, None, pane_pid)
            except (OSError, ValueError, IndexError):
                pass
            if len(matches) == 1:
                command = matches[0]
            elif foreground_claude:
                # Keep the pane and scrollback, but do not open a new or guessed
                # conversation. This also handles pre-registry Claude versions.
                command = "true"
                print(f"tmux-resurrect: {fields[1]}:{fields[2]}.{fields[5]} has no unique live Claude session; process restore skipped", file=sys.stderr)
        except (OSError, ValueError, IndexError):
            pass
        print("\t".join([*fields, ":" + command]) if command else "\t".join(fields))


def restore(command):
    try:
        argv = shlex.split(command)
        index = argv.index("--resume")
        uuid.UUID(argv[index + 1])
        if any(a in argv for a in ("--continue", "-c", "--fork-session")):
            raise ValueError("ambiguous selector")
        print(command)
    except (ValueError, IndexError):
        print("tmux-resurrect: Claude snapshot has no explicit session UUID; process restore skipped", file=sys.stderr)
        print("true")


if __name__ == "__main__":
    if sys.argv[1] == "capture":
        capture()
    else:
        restore(sys.argv[2])
