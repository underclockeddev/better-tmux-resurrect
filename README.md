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
