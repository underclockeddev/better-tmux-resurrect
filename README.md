# Better Tmux Resurrect

A maintained fork of
[tmux-plugins/tmux-resurrect](https://github.com/tmux-plugins/tmux-resurrect),
which has had no commit since 2023 while fixes kept arriving as pull requests.
This fork carries those fixes, plus its own. Everything below the next section
is upstream's README, and still applies.

### What's better

- **Saves are fast.** About 3s at 112 panes instead of about 20s: pane
  commands come from one `ps` snapshot, and pane contents and window options
  are read in one tmux call each instead of several per pane.
- **Saves never collide.** Every save takes one lock, whoever started it
  (key binding, tmux-continuum, a shutdown hook), so two saves no longer delete
  each other's pane contents. A save that finds another running waits for it.
- **`last` is never left dangling.** Two saves in the same second used to
  delete the file `last` points to (upstream #598), and an interrupted save at
  shutdown could become `last` with nothing in it. Neither can happen now.

- Exact [Claude session restore](docs/restoring_claude_code_sessions.md) reads
  the live process registry; parallel panes never guess by directory.

### Merged from upstream pull requests

Each one was read and tested here before it went in, and keeps its author.

- One restore at a time, so a double auto-restore no longer squashes extra
  panes (#600, Andrew Boldi).
- A restore reads the snapshot `last` named when it started, even if a save
  moves `last` meanwhile (#584, kvoli).
- An empty `last` stops the restore with a message instead of half-running it
  (#579, Matt Van Horn).
- Restored pane contents are removed by each pane once printed, fixing the
  cleanup race on fish and slow shells (#580, Matt Van Horn).
- Dotted session names restore into the right session (#597, Angel J. Haro).
- A window whose name starts with a saved index no longer hides a missing
  pane (#575, Theodor Lundqvist).
- A command argument containing a comma restores intact (#587, Scott Moser).
- The pgrep strategy keeps multi-line commands on one line (#591, Tim
  Phillips).
- Without a locale set, saves no longer come out near-empty (#568, Vivek
  Reddy Chithari).
- No more fixed `/tmp` paths open to symlink attacks (#567, Pistos), and the
  save directory, which holds pane contents, is private to you (#562, Florian
  Burka).

### Upstream PR review — 2026-11-06

Reviewed all 75 open proposals returned by GitHub’s pulls API (state=open,
per_page=100) on this date. “Skipped” is a disposition, not a promise to take
the feature later. Previously merged PRs remain credited above.

| PR | Disposition and reason |
| --- | --- |
| [#600](https://github.com/tmux-plugins/tmux-resurrect/pull/600) | Merged in the first batch; retained and credited above. |
| [#599](https://github.com/tmux-plugins/tmux-resurrect/pull/599) | Skipped: existing save lock and unique timestamp allocation prevent reuse of the file last names; the proposed unlink guard is redundant. |
| [#597](https://github.com/tmux-plugins/tmux-resurrect/pull/597) | Merged in the first batch; retained and credited above. |
| [#595](https://github.com/tmux-plugins/tmux-resurrect/pull/595) | Skipped: save batching overlaps our existing implementation; the fallback calls capture_pane_contents with one quoted triplet instead of three arguments, and the restore rewrite is too broad to take with that regression. |
| [#594](https://github.com/tmux-plugins/tmux-resurrect/pull/594) | Merged: corrects both save-directory documents, including XDG and legacy-directory precedence. |
| [#591](https://github.com/tmux-plugins/tmux-resurrect/pull/591) | Merged in the first batch; retained and credited above. |
| [#587](https://github.com/tmux-plugins/tmux-resurrect/pull/587) | Merged in the first batch; retained and credited above. |
| [#584](https://github.com/tmux-plugins/tmux-resurrect/pull/584) | Merged in the first batch; retained and credited above. |
| [#583](https://github.com/tmux-plugins/tmux-resurrect/pull/583) | Skipped: unversioned colon prefix changes how old pane titles decode; bundles capture-depth, save guards and restore-file pinning (already present) into the title fix. |
| [#581](https://github.com/tmux-plugins/tmux-resurrect/pull/581) | Skipped: colon-prefixed titles have no legacy snapshot decoder; adds an entire Docker runner along with the format change. Retain the existing snapshot format. |
| [#580](https://github.com/tmux-plugins/tmux-resurrect/pull/580) | Merged in the first batch; retained and credited above. |
| [#579](https://github.com/tmux-plugins/tmux-resurrect/pull/579) | Merged in the first batch; retained and credited above. |
| [#578](https://github.com/tmux-plugins/tmux-resurrect/pull/578) | Skipped: overlaps existing incomplete-save guard and empty-restore check; its pane-presence guard is narrower than complete dump validation. |
| [#576](https://github.com/tmux-plugins/tmux-resurrect/pull/576) | Skipped: existing window-presence save guard already rejects an empty dump; do not stack overlapping guards. |
| [#575](https://github.com/tmux-plugins/tmux-resurrect/pull/575) | Merged in the first batch; retained and credited above. |
| [#574](https://github.com/tmux-plugins/tmux-resurrect/pull/574) | Skipped: a pre-save hook is an API extension with no current consumer; the documentation addition depends on taking that new hook. |
| [#573](https://github.com/tmux-plugins/tmux-resurrect/pull/573) | Skipped: treats window pane-border options as pane overrides, adds per-pane queries and new records; custom border restoration needs a separate coherent format design. |
| [#572](https://github.com/tmux-plugins/tmux-resurrect/pull/572) | Skipped: guesses sessions from cwd/title/text similarity and latest database rows; this cannot prove exact pane identity. |
| [#571](https://github.com/tmux-plugins/tmux-resurrect/pull/571) | Skipped: superseded here by the existing live Claude registry with process birth validation; no new PID sidecars, transcript scan or latest-directory fallback. |
| [#568](https://github.com/tmux-plugins/tmux-resurrect/pull/568) | Merged in the first batch; retained and credited above. |
| [#567](https://github.com/tmux-plugins/tmux-resurrect/pull/567) | Merged in the first batch; retained and credited above. |
| [#566](https://github.com/tmux-plugins/tmux-resurrect/pull/566) | Skipped: our default save already batches ps; this version overwrites multiple children under one PPID and still forks pane_full_command per pane. |
| [#564](https://github.com/tmux-plugins/tmux-resurrect/pull/564) | Skipped: substitutes an underscore for a genuinely empty title, losing the original value. Do not replace data to accommodate the parser. |
| [#562](https://github.com/tmux-plugins/tmux-resurrect/pull/562) | Merged in the first batch; retained and credited above. |
| [#560](https://github.com/tmux-plugins/tmux-resurrect/pull/560) | Skipped: removes support for existing literal $HOME/$HOSTNAME settings with no migration; preserve the public option contract. |
| [#558](https://github.com/tmux-plugins/tmux-resurrect/pull/558) | Skipped: --continue and resume --last choose by directory, not pane identity; also changes default process/strategy registration. |
| [#557](https://github.com/tmux-plugins/tmux-resurrect/pull/557) | Skipped: changes manual save from whole-server to per-session and installs ~/bin/attach on plugin load; overwrites a session file instead of retaining timestamped snapshots. |
| [#554](https://github.com/tmux-plugins/tmux-resurrect/pull/554) | Skipped: duplicate save-directory correction; #594 also updates the previous-environment guide. |
| [#551](https://github.com/tmux-plugins/tmux-resurrect/pull/551) | Skipped: history recipe recursively removes destination directories and binds persisted history to recycled pane IDs. Do not recommend it for existing data. |
| [#550](https://github.com/tmux-plugins/tmux-resurrect/pull/550) | Skipped: reverses XDG default-directory policy and creates directories from a read helper; save already creates its destination. |
| [#546](https://github.com/tmux-plugins/tmux-resurrect/pull/546) | Skipped: zsh preexec sidecar is a second command store with concurrent sed-in-place writers and no process-birth fence; no zsh raw-command requirement here. |
| [#541](https://github.com/tmux-plugins/tmux-resurrect/pull/541) | Skipped: renames the shared archive to -old but neither checks pipeline success nor rolls back before unlinking it; does not provide an atomic snapshot/archive publication. |
| [#536](https://github.com/tmux-plugins/tmux-resurrect/pull/536) | Skipped: changes all delimiters with no old-format reader; Bash IFS treats the proposed multi-character delimiter as a set of characters, not a sequence. |
| [#534](https://github.com/tmux-plugins/tmux-resurrect/pull/534) | Skipped: starts headless Neovim and loads the user configuration merely to detect a plugin on restore; no persistence.nvim requirement justifies that side effect. |
| [#533](https://github.com/tmux-plugins/tmux-resurrect/pull/533) | Skipped: deletes test-runner/helper symlinks instead of initializing their declared submodule, disabling the existing runner. |
| [#531](https://github.com/tmux-plugins/tmux-resurrect/pull/531) | Skipped: persists potentially sensitive paste buffers and clears all live buffers on restore; opt-in feature still has unsafe buffer-name/path handling. |
| [#529](https://github.com/tmux-plugins/tmux-resurrect/pull/529) | Skipped: adds more sed escaping for variables without escaping replacement values; not a sound path expansion primitive. |
| [#528](https://github.com/tmux-plugins/tmux-resurrect/pull/528) | Skipped: #580 already fixes the fish race with per-pane cleanup after consumption; this alternative leaves files until the next restore. |
| [#520](https://github.com/tmux-plugins/tmux-resurrect/pull/520) | Skipped: removes every colon from pane titles, not just a guard; also cannot decode legacy unguarded titles. |
| [#518](https://github.com/tmux-plugins/tmux-resurrect/pull/518) | Skipped: infers shell identity from formatted show-option output and retains the PID-prefix grep; direct-pane discovery needs exact process identity. |
| [#511](https://github.com/tmux-plugins/tmux-resurrect/pull/511) | Skipped: replaces binding defaults with popup UI, introduces an undeclared ts dependency and spinner/control-mode machinery unrelated to correctness. |
| [#506](https://github.com/tmux-plugins/tmux-resurrect/pull/506) | Skipped: less precise duplicate of merged #594; does not explain XDG or legacy precedence. |
| [#505](https://github.com/tmux-plugins/tmux-resurrect/pull/505) | Skipped: save-directory explanation is covered by #594, which also fixes the restore guide. |
| [#502](https://github.com/tmux-plugins/tmux-resurrect/pull/502) | Skipped: documentation and implementation use different option names (save-confirm versus confirm-save); quoted command construction also changes the binding path. |
| [#500](https://github.com/tmux-plugins/tmux-resurrect/pull/500) | Skipped: reconstructs vifm arguments by whitespace splitting and guessed quotes; loses argument boundaries and cannot follow in-app session changes. |
| [#496](https://github.com/tmux-plugins/tmux-resurrect/pull/496) | Skipped: changes restored zsh to login-shell startup globally; no demonstrated need outweighs changing startup semantics for existing users. |
| [#495](https://github.com/tmux-plugins/tmux-resurrect/pull/495) | Skipped: rewrites PROMPT_COMMAND as a scalar with sed/backticks, incompatible with Bash array-valued prompt hooks. |
| [#488](https://github.com/tmux-plugins/tmux-resurrect/pull/488) | Skipped: fixes some stale fixture columns but hardcodes localhost titles and XDG paths; the test suite must pin shell/title/state directories rather than encode one host. |
| [#481](https://github.com/tmux-plugins/tmux-resurrect/pull/481) | Skipped: changes every save directory by socket name without migrating existing snapshots; explicit @resurrect-dir already supports separate servers. |
| [#476](https://github.com/tmux-plugins/tmux-resurrect/pull/476) | Skipped: appends session IDs but sorts/removes the first field, while window records are not given the same prefix; corrupts record alignment. |
| [#464](https://github.com/tmux-plugins/tmux-resurrect/pull/464) | Skipped: adds placeholder nano ~/whatfilename instructions without a complete installation example. |
| [#454](https://github.com/tmux-plugins/tmux-resurrect/pull/454) | Skipped: adds bind-key -N calls without commands before the real bindings; no compatibility gate for older supported tmux. |
| [#447](https://github.com/tmux-plugins/tmux-resurrect/pull/447) | Skipped: adds a default save key and replaces the quiet positional argument with getopts, breaking existing quiet callers; per-session snapshots are not required here. |
| [#408](https://github.com/tmux-plugins/tmux-resurrect/pull/408) | Skipped: claims history is snapshotted even though that feature was removed; text also contradicts itself about obtaining latest history. |
| [#342](https://github.com/tmux-plugins/tmux-resurrect/pull/342) | Skipped: targets an obsolete record layout; current upstream already saves and sets pane titles. |
| [#327](https://github.com/tmux-plugins/tmux-resurrect/pull/327) | Skipped: hardcoded installation file list omits new files and assumes source under /usr/local/src; TPM/manual installation already supports this plugin. |
| [#318](https://github.com/tmux-plugins/tmux-resurrect/pull/318) | Skipped: recursive pane creation and cleanup can kill unrelated existing panes; adds eval alias on snapshot contents and obsolete record offsets. |
| [#314](https://github.com/tmux-plugins/tmux-resurrect/pull/314) | Skipped: unquoted test on command strings and comparison to literal tmux fail for full executable paths; does not correctly identify direct child processes. |
| [#300](https://github.com/tmux-plugins/tmux-resurrect/pull/300) | Skipped: linked-window extension uses obsolete field layout and needs independent linked/grouped-window compatibility coverage; do not merge an unverified schema rewrite. |
| [#297](https://github.com/tmux-plugins/tmux-resurrect/pull/297) | Skipped: emits debug paths during normal save/restore and uses nonportable readlink -f; current CURRENT_DIR already resolves an absolute script directory. |
| [#295](https://github.com/tmux-plugins/tmux-resurrect/pull/295) | Skipped: modifies removed shell-history implementation and injects M-z/M-Z keystrokes whose meaning depends on user bindings. |
| [#289](https://github.com/tmux-plugins/tmux-resurrect/pull/289) | Skipped: relative symlink resolution references undefined DIR instead of CURRENT_DIR; breaks the very path it intends to fix. |
| [#286](https://github.com/tmux-plugins/tmux-resurrect/pull/286) | Skipped: regex basename matching explicitly breaks escaped executable paths; it also adds a tmux option lookup for every process match. |
| [#279](https://github.com/tmux-plugins/tmux-resurrect/pull/279) | Skipped: #580 already defers restore cleanup until each pane consumes its file; retaining old save files can archive panes no longer present. |
| [#273](https://github.com/tmux-plugins/tmux-resurrect/pull/273) | Skipped: sends commands into existing or excluded panes before checking whether their processes should be restored; can overwrite live input. |
| [#257](https://github.com/tmux-plugins/tmux-resurrect/pull/257) | Skipped: WIP adds empty section headings without usable vim-session instructions. |
| [#256](https://github.com/tmux-plugins/tmux-resurrect/pull/256) | Skipped: selects the last process-list row rather than the foreground job; process order is not pane identity. |
| [#222](https://github.com/tmux-plugins/tmux-resurrect/pull/222) | Skipped: automatic-rename is already saved/restored in the current format, including inheritance; this targets an obsolete field layout. |
| [#202](https://github.com/tmux-plugins/tmux-resurrect/pull/202) | Skipped: filename timestamp spelling is cosmetic on supported hosts; do not change the established naming contract for a historical WSL workaround. |
| [#159](https://github.com/tmux-plugins/tmux-resurrect/pull/159) | Skipped: last ps row on a TTY is not necessarily the foreground process; filtering a few shell names cannot establish that relationship. |
| [#152](https://github.com/tmux-plugins/tmux-resurrect/pull/152) | Skipped: shell command substitution inside a tmux format invokes lsof/xargs per pane and interpolates a tty unquoted; current tmux supplies pane_current_path. |
| [#149](https://github.com/tmux-plugins/tmux-resurrect/pull/149) | Skipped: printf uses the command as its format string; basename matching also discards arguments during matching and unrelated completion output is removed. |
| [#133](https://github.com/tmux-plugins/tmux-resurrect/pull/133) | Skipped: targets shell-history save code removed upstream; there is no matching current execution path. |
| [#126](https://github.com/tmux-plugins/tmux-resurrect/pull/126) | Skipped: sets automatic-rename globally while restoring a pane, overriding unrelated windows; filename change duplicates #202. |
| [#59](https://github.com/tmux-plugins/tmux-resurrect/pull/59) | Skipped: invalid Bash if syntax (missing semicolon before then); automatic-rename behavior is already handled by current window-property restoration. |

### Install

With [tpm](https://github.com/tmux-plugins/tpm), in place of
`tmux-plugins/tmux-resurrect`:

    set -g @plugin 'underclockeddev/better-tmux-resurrect'

Saved environments and options are unchanged, so an existing setup keeps
working.

### Credit

The plugin is Bruno Sutic's and its contributors' (MIT, see `LICENSE.md`).
Merged pull requests keep their authors.

---

Restore `tmux` environment after system restart.

Tmux is great, except when you have to restart the computer. You lose all the
running programs, working directories, pane layouts etc.
There are helpful management tools out there, but they require initial
configuration and continuous updates as your workflow evolves or you start new
projects.

`tmux-resurrect` saves all the little details from your tmux environment so it
can be completely restored after a system restart (or when you feel like it).
No configuration is required. You should feel like you never quit tmux.

It even (optionally)
[restores vim and neovim sessions](docs/restoring_vim_and_neovim_sessions.md)!

Automatic restoring and continuous saving of tmux env is also possible with
[tmux-continuum](https://github.com/tmux-plugins/tmux-continuum) plugin.

### Screencast

[![screencast screenshot](/video/screencast_img.png)](https://vimeo.com/104763018)

### Key bindings

- `prefix + Ctrl-s` - save
- `prefix + Ctrl-r` - restore

### About

This plugin goes to great lengths to save and restore all the details from your
`tmux` environment. Here's what's been taken care of:

- all sessions, windows, panes and their order
- current working directory for each pane
- **exact pane layouts** within windows (even when zoomed)
- active and alternative session
- active and alternative window for each session
- windows with focus
- active pane for each window
- "grouped sessions" (useful feature when using tmux with multiple monitors)
- programs running within a pane! More details in the
  [restoring programs doc](docs/restoring_programs.md).

Optional:

- [restoring vim and neovim sessions](docs/restoring_vim_and_neovim_sessions.md)
- [restoring pane contents](docs/restoring_pane_contents.md)
- [restoring a previously saved environment](docs/restoring_previously_saved_environment.md)

Requirements / dependencies: `tmux 1.9` or higher, `bash`.

Tested and working on Linux, OSX and Cygwin.

`tmux-resurrect` is idempotent! It will not try to restore panes or windows that
already exist.<br/>
The single exception to this is when tmux is started with only 1 pane in order
to restore previous tmux env. Only in this case will this single pane be
overwritten.

### Installation with [Tmux Plugin Manager](https://github.com/tmux-plugins/tpm) (recommended)

Add plugin to the list of TPM plugins in `.tmux.conf`:

    set -g @plugin 'tmux-plugins/tmux-resurrect'

Hit `prefix + I` to fetch the plugin and source it. You should now be able to
use the plugin.

### Manual Installation

Clone the repo:

    $ git clone https://github.com/tmux-plugins/tmux-resurrect ~/clone/path

Add this line to the bottom of `.tmux.conf`:

    run-shell ~/clone/path/resurrect.tmux

Reload TMUX environment with: `$ tmux source-file ~/.tmux.conf`.
You should now be able to use the plugin.

### Docs

- [Guide for migrating from tmuxinator](docs/migrating_from_tmuxinator.md)

**Configuration**

- [Changing the default key bindings](docs/custom_key_bindings.md).
- [Setting up hooks on save & restore](docs/hooks.md).
- Only a conservative list of programs is restored by default:<br/>
  `vi vim nvim emacs man less more tail top htop irssi weechat mutt`.<br/>
  [Restoring programs doc](docs/restoring_programs.md) explains how to restore
  additional programs.
- [Change a directory](docs/save_dir.md) where `tmux-resurrect` saves tmux
  environment.

**Optional features**

- [Restoring vim and neovim sessions](docs/restoring_vim_and_neovim_sessions.md)
  is nice if you're a vim/neovim user.
- [Restoring pane contents](docs/restoring_pane_contents.md) feature.

### Other goodies

- [tmux-copycat](https://github.com/tmux-plugins/tmux-copycat) - a plugin for
  regex searches in tmux and fast match selection
- [tmux-yank](https://github.com/tmux-plugins/tmux-yank) - enables copying
  highlighted text to system clipboard
- [tmux-open](https://github.com/tmux-plugins/tmux-open) - a plugin for quickly
  opening highlighted file or a url
- [tmux-continuum](https://github.com/tmux-plugins/tmux-continuum) - automatic
  restoring and continuous saving of tmux env

### Reporting bugs and contributing

Both contributing and bug reports are welcome. Please check out
[contributing guidelines](CONTRIBUTING.md).

### Credits

[Mislav Marohnić](https://github.com/mislav) - the idea for the plugin came from his
[tmux-session script](https://github.com/mislav/dotfiles/blob/2036b5e03fb430bbcbc340689d63328abaa28876/bin/tmux-session).

### License
[MIT](LICENSE.md)
