import sublime
import sublime_plugin
import subprocess
import os
import pprint


state = {}


def get_state():
    window_id = sublime.active_window().id()
    if not window_id in state:
        state[window_id] = {}
    return state[window_id]


def get_active_session():
    window_state = get_state()
    if "active_session" in window_state:
        return window_state["active_session"]
    else:
        load_config(show_error=False)
        if "active_session" in window_state:
            return window_state["active_session"]
        else:
            sublime.error_message("No active Zellij session.")
            raise RuntimeError("No active Zellij session.")


def set_active_session(session):
    window_state = get_state()
    window_state["active_session"] = session


def cli(cmd):
    cmd = ["zellij"] + cmd
    proc = subprocess.Popen(cmd,
                            shell=False,
                            universal_newlines=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    stdout, stderr = proc.communicate()
    if stderr:
        print(stderr)
        sublime.error_message(
            "Zellij command failed. See console for details.")
        sublime.status_message(
            "Zellij command failed. See console for details.")
    return stdout


def cli_with_session(cmd):
    session = get_active_session()
    return cli(["--session", session] + cmd)


def cli_focus_tab(tab):
    cli_with_session(["action", "go-to-tab-name", tab])


def cli_close_current_tab():
    cli_with_session(["action", "close-tab"])


def cli_close_current_pane():
    cli_with_session(["action", "close-pane"])


def cli_send_text(text):
    cli_with_session(["action", "write-chars", text])


def cli_stop_current_process():
    cli_with_session(["action", "write", "3"])


def cli_list_tabs():
    result = cli_with_session(["action", "query-tab-names"])
    return result.splitlines()


def cli_list_sessions():
    result = cli(["list-sessions", "-s"])
    return result.splitlines()


def cli_run(cmd):
    cli_with_session(["run", "--", cmd])


def cli_new_tab(name):
    cli_with_session(["action", "new-tab", "--name", name])


def target_tab():
    view = sublime.active_window().active_view()
    window_state = get_state()

    if "send_bindings" in window_state:
        target = window_state["send_bindings"].get(view.buffer_id())
        if target:
            return target

    if "config" in window_state:
        config = window_state["config"]
        if "send" in config:
            send_config = config["send"]
            syntax = view.syntax().name
            if syntax in send_config:
                return send_config[syntax]


def send_text(text):
    tab = target_tab()
    if tab:
        cli_focus_tab(tab)

    cli_send_text(text)
    cli_send_text("\n")


def select_session():
    tabs = cli_list_sessions()

    def switch(idx):
        if idx > -1:
            set_active_session(tabs[idx])

    sublime.active_window().show_quick_panel(tabs, lambda i: switch(i))


def focus_tab():
    tabs = cli_list_tabs()

    def switch(idx):
        if idx > -1:
            cli_focus_tab(tabs[idx])

    sublime.active_window().show_quick_panel(tabs, lambda i: switch(i))


def send_selected():
    view = sublime.active_window().active_view()
    selection = view.sel()
    selectedText = view.substr(selection[0])
    if not selectedText.strip():
        sublime.status_message("Nothing selected")
        return

    encoded = selectedText.encode('utf-8')
    send_text(encoded)


def curr_dir():
    window = sublime.active_window()
    view = window.active_view()
    file = view.file_name()
    if file:
        return os.path.dirname(file)
    else:
        folders = window.folders()
        return folders[0]


def search_config_file(path):
    f = os.path.join(path, ".subl-zellij")
    if os.path.exists(f):
        return f
    else:
        if os.path.ismount(path):
            return None
        else:
            return search_config_file(os.path.dirname(path))


def config_path():
    return search_config_file(curr_dir())


def load_config(show_error=True):
    window_state = get_state()
    path = config_path()
    if path:
        with open(path) as f:
            window_state["config"] = eval(f.read())
        session = window_state["config"]["session"]
        set_active_session(session)
        dir = os.path.dirname(path)
        cwd = dir
        config = window_state["config"]
        if "cwd" in config:
            cwd = os.path.join(cwd, config["cwd"])
        window_state["cwd"] = cwd
        pprint.pprint(window_state)
        sublime.status_message("Zellij config has been loaded.")
    elif show_error:
        sublime.error_message("Sublime Zellij config not found.")


def run_selected_tab(name, cmd):
    tabs = cli_list_tabs()
    tabs = set(tabs)
    if name in tabs:
        cli_focus_tab(name)
        # Closing pane does not stop running process,
        # so we send ^C to stop it.
        # TODO: find a better solution
        cli_stop_current_process()
        cli_close_current_tab()
    cli_new_tab(name)
    window_state = get_state()
    # This approach allows to trigger shell hooks.
    if "cwd" in window_state:
        cli_send_text("cd " + window_state["cwd"])
        cli_send_text("\n")
    for c in cmd["cmd"]:
        cli_send_text(c)
        cli_send_text("\n")


def run_tab():
    window_state = get_state()
    if not "config" in window_state:
        load_config()
    if not "config" in window_state:
        return

    config = window_state["config"]
    if "tabs" in config:
        names = []
        commands = []

        for name, cmd in config["tabs"].items():
            names.append(name)
            commands.append(cmd)
        w = sublime.active_window()
        w.show_quick_panel(
            names, lambda i: run_selected_tab(names[i], commands[i]))


def bind_buffer():
    window = sublime.active_window()
    view = window.active_view()
    tabs = cli_list_tabs()
    window_state = get_state()

    def bind(idx):
        if idx > -1:
            if not "send_bindings" in window_state:
                window_state["send_bindings"] = {}
            key = view.buffer_id()
            window_state["send_bindings"].update({key: tabs[idx]})

    window.show_quick_panel(tabs, lambda i: bind(i))


def unbind_buffer():
    window = sublime.active_window()
    view = window.active_view()
    window_state = get_state()
    if "send_bindings" in window_state:
        key = view.buffer_id()
        bindings = window_state["send_bindings"]
        if key in bindings:
            del bindings[key]
    else:
        window_state["send_bindings"] = {}


class ZellijLinkSendSelectedCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        send_selected()


class ZellijLinkFocusTabCommand(sublime_plugin.WindowCommand):
    def run(self):
        focus_tab()


class ZellijLinkSelectSessionCommand(sublime_plugin.WindowCommand):
    def run(self):
        select_session()


class ZellijLinkLoadConfigCommand(sublime_plugin.WindowCommand):
    def run(self):
        load_config()


class ZellijLinkRunTabCommand(sublime_plugin.WindowCommand):
    def run(self):
        run_tab()


class ZellijLinkBindBufferCommand(sublime_plugin.WindowCommand):
    def run(self):
        bind_buffer()


class ZellijLinkUnbindBufferCommand(sublime_plugin.WindowCommand):
    def run(self):
        unbind_buffer()
