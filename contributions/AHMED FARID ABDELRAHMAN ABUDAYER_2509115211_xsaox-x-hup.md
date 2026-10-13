# Contribution — AHMED FARID ABDELRAHMAN ABUDAYER (<2509115211>, @Xsaox-x)

## My role
I was responsible for `cli.py`, the command-line interface, which is the main
way to use Study Organizer and the CLI required by the project brief.

## What I built

### `cli.py`
- **`build_parser()`:** uses `argparse` with three sub-commands:
  - `scan FOLDER` — summary of where the files would go,
  - `organize FOLDER` — lists the moves, asks for confirmation, moves files,
  - `undo FOLDER` — puts back the files from the last run.
- **Options:** `--dest NAME` (output folder name), `-r / --recursive`
  (include sub-folders), `--no-course` (sort by type only), `--dry-run`
  (show the moves without changing anything) and `-y / --yes` (skip the
  confirmation, useful for scripts). Shared options are added in loops so
  they are not repeated for each command.
- **`cmd_scan()`, `cmd_organize()`, `cmd_undo()`:** one function per command,
  chosen through a dictionary of handlers in `main()`.
- **`confirm()`:** asks `[y/N]`; Ctrl+D (`EOFError`) counts as "no", so
  nothing is moved by accident.
- **`main()`:** validates the folder and the destination name first, prints
  errors to `stderr` instead of showing a traceback, and returns clear exit
  codes: `0` success, `1` error, `2` wrong arguments, `130` Ctrl+C.

### Example
```
$ python cli.py scan Downloads
$ python cli.py organize Downloads --dry-run
$ python cli.py organize Downloads -y
$ python cli.py undo Downloads
```

## Other work
- Tested every command and option, including wrong arguments such as an
  unknown command, a missing folder and `--dest ../../etc`.

## What I learned
How to build a real command-line tool with `argparse` (sub-commands, flags,
help messages), how to use a dictionary to choose a function, and how exit
codes and `stderr` make a program easy to use from scripts.

