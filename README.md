# Zellij Link
Sublime Text 4 plugin for [Zellij](https://zellij.dev]) interaction.

Inspired by [SendText](https://github.com/wch/SendText).

## Features
- simple Zellij session configuration
- start/restart configured Zellij tabs
- send any selected text to a target Zellij tab
  - file type -> zellij tab configuration in `.subl-zellij`
  - buffer -> zellij tab binding with "Bind Buffer to Zellij Tab" command
 
[All supported commands](./Default.sublime-commands)

## Configuration file
Config file format is Python dictionary.
ZellijLink tries to find `.subl-zellij` file starting from current location up to filesystem root.
Current location is either directory of file from active buffer, or directory, currently opened with ST.

Sample:
```Python
{
    "session": "test-session",
    "cwd": "some_subdir",
    "tabs": {
        "clj-repl": {
            "cmd": ["clj"],
        },
    },
    "send": {
        "Clojure (Sublimed)": "clj-repl",
    },
}

```
## Demo
### Run preconfigured tab
![run_tab](https://github.com/andriidemus/ZellijLink/assets/2218567/d1f1d061-66fb-4a09-bcf3-2df5a5554223)


### Send selected
![send_selected](https://github.com/andriidemus/ZellijLink/assets/2218567/6d528326-5b31-420a-a08f-aa857ee71af8)

### Bind buffer to Zellij tab
![send_to_bound](https://github.com/andriidemus/ZellijLink/assets/2218567/9b7abca2-29cf-4d95-a1f7-c36ef896c805)

## Custom commands
Plugin code may be reused for custom commands, like reloading clojure file in REPL:
```Python
import os
import ZellijLink.zellij as zellij

class ReloadCljFileInRepl(sublime_plugin.TextCommand):
    def run(self, edit):
        file = self.view.file_name()
        if file:
            (_, ext) = os.path.splitext(file)
            if ext.startswith(".clj"):
                path = os.path.realpath(file)
                repl_str = '(load-file "' + path + '")'
                zellij.send_text(repl_str)
```
![load_file](https://github.com/andriidemus/ZellijLink/assets/2218567/858c1442-849b-45ca-ac78-ced32ad2e9ed)

