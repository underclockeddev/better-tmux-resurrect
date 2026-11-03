#!/usr/bin/env bash

CURRENT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

source "$CURRENT_DIR/variables.sh"
source "$CURRENT_DIR/helpers.sh"
source "$CURRENT_DIR/spinner_helpers.sh"

# delimiters
d=$'\t'
delimiter=$'\t'

# if "quiet" script produces no output
SCRIPT_OUTPUT="$1"

grouped_sessions_format() {
	local format
	format+="#{session_grouped}"
	format+="${delimiter}"
	format+="#{session_group}"
	format+="${delimiter}"
	format+="#{session_id}"
	format+="${delimiter}"
	format+="#{session_name}"
	echo "$format"
}

pane_format() {
	local format
	format+="pane"
	format+="${delimiter}"
	format+="#{session_name}"
	format+="${delimiter}"
	format+="#{window_index}"
	format+="${delimiter}"
	format+="#{window_active}"
	format+="${delimiter}"
	format+=":#{window_flags}"
	format+="${delimiter}"
	format+="#{pane_index}"
	format+="${delimiter}"
	format+="#{pane_title}"
	format+="${delimiter}"
	format+=":#{pane_current_path}"
	format+="${delimiter}"
	format+="#{pane_active}"
	format+="${delimiter}"
	format+="#{pane_current_command}"
	format+="${delimiter}"
	format+="#{pane_pid}"
	format+="${delimiter}"
	format+="#{history_size}"
	echo "$format"
}

window_format() {
	local format
	format+="window"
	format+="${delimiter}"
	format+="#{session_name}"
	format+="${delimiter}"
	format+="#{window_index}"
	format+="${delimiter}"
	format+=":#{window_name}"
	format+="${delimiter}"
	format+="#{window_active}"
	format+="${delimiter}"
	format+=":#{window_flags}"
	format+="${delimiter}"
	format+="#{window_layout}"
	echo "$format"
}

state_format() {
	local format
	format+="state"
	format+="${delimiter}"
	format+="#{client_session}"
	format+="${delimiter}"
	format+="#{client_last_session}"
	echo "$format"
}

dump_panes_raw() {
	tmux list-panes -a -F "$(pane_format)"
}

dump_windows_raw(){
	tmux list-windows -a -F "$(window_format)"
}

toggle_window_zoom() {
	local target="$1"
	tmux resize-pane -Z -t "$target"
}

_save_command_strategy_file() {
	local save_command_strategy="$(get_tmux_option "$save_command_strategy_option" "$default_save_command_strategy")"
	local strategy_file="$CURRENT_DIR/../save_command_strategies/${save_command_strategy}.sh"
	local default_strategy_file="$CURRENT_DIR/../save_command_strategies/${default_save_command_strategy}.sh"
	if [ -e "$strategy_file" ]; then # strategy file exists?
		echo "$strategy_file"
	else
		echo "$default_strategy_file"
	fi
}

pane_full_command() {
	local pane_pid="$1"
	local strategy_file="$(_save_command_strategy_file)"
	# execute strategy script to get pane full command
	$strategy_file "$pane_pid"
}

number_nonempty_lines_on_screen() {
	local pane_id="$1"
	tmux capture-pane -pJ -t "$pane_id" |
		sed '/^$/d' |
		wc -l |
		sed 's/ //g'
}

# tests if there was any command output in the current pane
pane_has_any_content() {
	local pane_id="$1"
	local history_size="$(tmux display -p -t "$pane_id" -F "#{history_size}")"
	local cursor_y="$(tmux display -p -t "$pane_id" -F "#{cursor_y}")"
	# doing "cheap" tests first
	[ "$history_size" -gt 0 ] || # history has any content?
		[ "$cursor_y" -gt 0 ] || # cursor not in first line?
		[ "$(number_nonempty_lines_on_screen "$pane_id")" -gt 1 ]
}

capture_pane_contents() {
	local pane_id="$1"
	local start_line="-$2"
	local pane_contents_area="$3"
	if pane_has_any_content "$pane_id"; then
		if [ "$pane_contents_area" = "visible" ]; then
			start_line="0"
		fi
		# the printf hack below removes *trailing* empty lines
		printf '%s\n' "$(tmux capture-pane -epJ -S "$start_line" -t "$pane_id")" > "$(pane_contents_file "save" "$pane_id")"
	fi
}

get_active_window_index() {
	local session_name="$1"
	tmux list-windows -t "$session_name" -F "#{window_flags} #{window_index}" |
		awk '$1 ~ /\*/ { print $2; }'
}

get_alternate_window_index() {
	local session_name="$1"
	tmux list-windows -t "$session_name" -F "#{window_flags} #{window_index}" |
		awk '$1 ~ /-/ { print $2; }'
}

dump_grouped_sessions() {
	local current_session_group=""
	local original_session
	tmux list-sessions -F "$(grouped_sessions_format)" |
		grep "^1" |
		cut -c 3- |
		sort |
		while IFS=$d read session_group session_id session_name; do
			if [ "$session_group" != "$current_session_group" ]; then
				# this session is the original/first session in the group
				original_session="$session_name"
				current_session_group="$session_group"
			else
				# this session "points" to the original session
				active_window_index="$(get_active_window_index "$session_name")"
				alternate_window_index="$(get_alternate_window_index "$session_name")"
				echo "grouped_session${d}${session_name}${d}${original_session}${d}:${alternate_window_index}${d}:${active_window_index}"
			fi
		done
}

fetch_and_dump_grouped_sessions(){
	local grouped_sessions_dump="$(dump_grouped_sessions)"
	get_grouped_sessions "$grouped_sessions_dump"
	if [ -n "$grouped_sessions_dump" ]; then
		echo "$grouped_sessions_dump"
	fi
}

# Upstream finds each pane's command by forking the strategy script (bash, ps,
# sed, grep, cut) plus a show-option, per pane: ~10s at 111 panes. The default
# "ps" strategy now reads one ps snapshot, keyed on the exact parent pid
# (upstream's grep "^$pid" also matched pid 12 against 123's children). Any
# other strategy still runs per pane.
declare -A _pane_children
_snapshot_pane_children() {
	local ppid args
	while read -r ppid args; do
		_pane_children[$ppid]+="${_pane_children[$ppid]:+$'\n'}$args"
	done < <(ps -ao "ppid=,args=")
}

dump_panes() {
	local full_command
	local strategy="$(get_tmux_option "$save_command_strategy_option" "$default_save_command_strategy")"
	[ "$strategy" = "$default_save_command_strategy" ] && _snapshot_pane_children
	dump_panes_raw |
		while IFS=$d read line_type session_name window_number window_active window_flags pane_index pane_title dir pane_active pane_command pane_pid history_size; do
			# not saving panes from grouped sessions
			if is_session_grouped "$session_name"; then
				continue
			fi
			if [ "$strategy" = "$default_save_command_strategy" ]; then
				full_command="${_pane_children[$pane_pid]}"
			else
				full_command="$(pane_full_command $pane_pid)"
			fi
			dir="${dir/ /\\ }" # escape the first space, as upstream's sed did
			echo "${line_type}${d}${session_name}${d}${window_number}${d}${window_active}${d}${window_flags}${d}${pane_index}${d}${pane_title}${d}${dir}${d}${pane_active}${d}${pane_command}${d}:${full_command}"
		done
}

dump_windows() {
	dump_windows_raw |
		while IFS=$d read line_type session_name window_index window_name window_active window_flags window_layout; do
			# not saving windows from grouped sessions
			if is_session_grouped "$session_name"; then
				continue
			fi
			automatic_rename="$(tmux show-window-options -vt "${session_name}:${window_index}" automatic-rename)"
			# If the option was unset, use ":" as a placeholder.
			[ -z "${automatic_rename}" ] && automatic_rename=":"
			echo "${line_type}${d}${session_name}${d}${window_index}${d}${window_name}${d}${window_active}${d}${window_flags}${d}${window_layout}${d}${automatic_rename}"
		done
}

dump_state() {
	tmux display-message -p "$(state_format)"
}

# A tmux config-file double-quoted string: escape \ " and $.
_tmux_quote() {
	local s="${1//\\/\\\\}"
	s="${s//\"/\\\"}"
	printf '"%s"' "${s//\$/\\\$}"
}

dump_pane_contents() {
	# Upstream spends four tmux forks a pane (history_size, cursor_y, a screen
	# capture to count lines, the capture) and drops trailing empty lines by
	# pushing each capture, megabytes for a long scrollback, through a bash
	# $(...): ~5.6s at 112 panes. Now one list-panes carries both values, one
	# source-file captures every pane to its file, and one sed strips the
	# trailing empty lines. The screen is still counted, but only for a pane
	# with no history and the cursor on line 0.
	local pane_contents_area="$(get_tmux_option "$pane_contents_area_option" "$default_pane_contents_area")"
	local dir="$(pane_contents_dir "save")" conf="$(mktemp)" buffer="grape-resurrect-$$"
	local pane pane_id history_size cursor_y start_line file
	local -a files
	while IFS=$d read pane pane_id history_size cursor_y; do
		[ "$history_size" -gt 0 ] || [ "$cursor_y" -gt 0 ] ||
			[ "$(number_nonempty_lines_on_screen "$pane_id")" -gt 1 ] ||
			continue
		start_line="-$history_size"
		[ "$pane_contents_area" = "visible" ] && start_line="0"
		file="${dir}/pane-${pane}"
		files+=("$file")
		printf 'capture-pane -eJ -S %s -t %s -b %s\nsave-buffer -b %s %s\ndelete-buffer -b %s\n' \
			"$start_line" "$pane_id" "$buffer" "$buffer" "$(_tmux_quote "$file")" "$buffer" >> "$conf"
	done < <(tmux list-panes -a -F "#{session_name}:#{window_index}.#{pane_index}${d}#{pane_id}${d}#{history_size}${d}#{cursor_y}")
	tmux source-file "$conf" 2>/dev/null
	rm -f "$conf"
	# delete trailing empty lines; -i edits each file on its own, so $ is per file
	[ ${#files[@]} -gt 0 ] && sed -i -e :a -e '/^\n*$/{$d;N;ba' -e '}' "${files[@]}" 2>/dev/null
	return 0
}

remove_old_backups() {
	# remove resurrect files older than 30 days (default), but keep at least 5 copies of backup.
	local delete_after="$(get_tmux_option "$delete_backup_after_option" "$default_delete_backup_after")"
	local -a files
	files=($(ls -t $(resurrect_dir)/${RESURRECT_FILE_PREFIX}_*.${RESURRECT_FILE_EXTENSION} | tail -n +6))
	[[ ${#files[@]} -eq 0 ]] ||
		find "${files[@]}" -type f -mtime "+${delete_after}" -exec rm -v "{}" \; > /dev/null
}

save_all() {
	local resurrect_file_path="$(resurrect_file_path)"
	local last_resurrect_file="$(last_resurrect_file)"
	mkdir -p "$(resurrect_dir)"
	fetch_and_dump_grouped_sessions > "$resurrect_file_path"
	dump_panes   >> "$resurrect_file_path"
	dump_windows >> "$resurrect_file_path"
	dump_state   >> "$resurrect_file_path"
	execute_hook "post-save-layout" "$resurrect_file_path"
	# A valid dump always contains at least one `window` line. Anything smaller
	# is an interrupted save (e.g. tmux killed mid-write on shutdown) and must
	# NOT overwrite `last`, or auto-restore has nothing to load next boot.
	if ! grep -q '^window	' "$resurrect_file_path" 2>/dev/null; then
		rm -f "$resurrect_file_path"
	elif files_differ "$resurrect_file_path" "$last_resurrect_file"; then
		ln -fs "$(basename "$resurrect_file_path")" "$last_resurrect_file"
	else
		rm "$resurrect_file_path"
	fi
	if capture_pane_contents_option_on; then
		mkdir -p "$(pane_contents_dir "save")"
		dump_pane_contents
		pane_contents_create_archive
		rm "$(pane_contents_dir "save")"/*
	fi
	remove_old_backups
	execute_hook "post-save-all"
}

show_output() {
	[ "$SCRIPT_OUTPUT" != "quiet" ]
}

main() {
	if supported_tmux_version_ok; then
		if show_output; then
			start_spinner "Saving..." "Tmux environment saved!"
		fi
		save_all
		if show_output; then
			stop_spinner
			display_message "Tmux environment saved!"
		fi
	fi
}
main
