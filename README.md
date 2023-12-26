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
ZellijLink tries to find `.subl-zellij` file starting from current location up to filesystem root.
Current location is either directory of file from active buffer, or directory, currently opened with ST.

Sample:
```
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
