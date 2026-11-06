# Exact Claude session restore

Enable explicitly in tmux.conf:

```tmux
set -g @resurrect-processes 'claude'
set -g @resurrect-strategy-claude 'session'
```

This optional feature requires Linux, Python 3, and a Claude build publishing
`<CLAUDE_CONFIG_DIR>/sessions/*.json` (default `~/.claude/sessions`).
`CLAUDE_SESSIONS_DIR` overrides the registry directory. Each row must contain
`pid`, `procStart` (Linux process start ticks), and `sessionId` (UUID).
The fleet's Claude build already publishes these records and updates them on
session changes. Stock versions without this registry need manual recovery.

A save reads the registry once. It accepts only a live process with the same
birth ticks, in its terminal's foreground process group, descended from that
pane's process (or the pane process itself). Exactly one match is required.
The command becomes `claude <original arguments> --resume <exact UUID>`;
conversation selectors are replaced and shell argument boundaries preserved.
Print-mode commands and arguments containing tabs/newlines cannot be captured.
No hook or tmux-specific session database is installed. No transcript is read.

If a foreground Claude pane has no unique valid mapping, its layout and
scrollback are saved, its process command is replaced with `true`, and a warning
names the pane. Older snapshots containing plain Claude or `--continue` also
warn and skip that process. There is no newest-in-directory fallback. This
prevents parallel panes from resuming one another's conversation.

The existing tab-separated snapshot format is unchanged. Other processes keep
the selected command strategy, including the default batched process snapshot.
Disabling the option stops capture; keep it enabled when restoring these saves.
The prior plugin can read the new snapshots because explicit resume commands
are ordinary command fields. No saved data is removed during installation.

Run `PYTHONDONTWRITEBYTECODE=1 python3 tests/test_claude_sessions.py` for a real
private-server save/kill/restore test using stub CLIs and scratch HOME, runtime,
registry and save directories. It never starts a real Claude conversation.

Related proposals: upstream #571 established the importance of per-pane IDs,
but its PID sidecars and latest-directory fallback are not used here. #558's
`--continue` approach cannot distinguish simultaneous same-directory panes.
