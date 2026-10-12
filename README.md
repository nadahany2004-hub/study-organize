# Study Organizer

A command-line automation tool that cleans up a messy folder of study files.
It sorts every file **by course code and by file type**, moves **duplicate downloads**
into their own folder, and can **undo** everything with one command.

```
Downloads/                              Downloads/Organized/
├── COE203_Lecture1.pdf                 ├── COE203/
├── COE203_Lecture1 (1).pdf      ──►    │   ├── Lectures_and_Notes/COE203_Lecture1.pdf
├── COE 203 slides.pptx                 │   └── Slides/COE 203 slides.pptx
├── math101-hw2.xlsx                    ├── MATH101/Assignments_and_Data/math101-hw2.xlsx
├── project.py                          ├── Code/project.py
└── notes.txt                           ├── Lectures_and_Notes/notes.txt
                                        └── Duplicates/COE203_Lecture1 (1).pdf
```

## The problem

Students download lecture slides, homework sheets and code from several courses into one
folder. After a few weeks the folder holds hundreds of files with no structure, and the same
lecture is often downloaded two or three times (`lecture.pdf`, `lecture (1).pdf`, ...).
Finding the right file wastes time, and the copies waste disk space.

## What it does

| Feature | How |
|---|---|
| Sort by **course** | Finds course codes such as `COE203`, `math-101` or `COE 203` in the file name with a regular expression |
| Sort by **file type** | Maps extensions to folders: lectures, slides, assignments, code, media, archives, other |
| Find **duplicates** | Compares file contents with SHA-256 (only for files with the same size, so it stays fast) |
| **Dry run** | Shows every planned move without touching anything |
| **Undo** | Every run is saved in `organizer_log.json`; `undo` puts the files back |
| **Never overwrites** | If a name is taken, it uses `notes_1.txt`, `notes_2.txt`, ... |
| **Safe by default** | Skips hidden files and symbolic links, refuses `/` and the home folder, validates every input |
| CLI **and** GUI | `cli.py` is the main tool; `gui.py` is an optional window that uses the same code |

## Requirements

- Python **3.9 or newer**
- No extra packages (only the standard library). `gui.py` needs `tkinter`, which ships with Python on Windows and macOS.

## Usage

```bash
# 1. See a summary of what would happen
python cli.py scan ~/Downloads

# 2. See every single move, without moving anything
python cli.py organize ~/Downloads --dry-run

# 3. Organize (asks for confirmation)
python cli.py organize ~/Downloads

# 4. Changed your mind? Put everything back
python cli.py undo ~/Downloads
```

Example output of `scan`:

```
6 file(s) in /home/student/Downloads

     1  ->  Organized/COE203/Lectures_and_Notes
     1  ->  Organized/COE203/Slides
     1  ->  Organized/Code
     1  ->  Organized/Duplicates
     1  ->  Organized/Lectures_and_Notes
     1  ->  Organized/MATH101/Assignments_and_Data

1 duplicate file(s) found.
```

### Commands and options

| Command | What it does |
|---|---|
| `scan FOLDER` | Summary: how many files go to each folder, how many duplicates |
| `organize FOLDER` | Lists the moves, asks for confirmation, then moves the files |
| `undo FOLDER` | Restores the files from the last `organize` run |

| Option | Used with | Meaning |
|---|---|---|
| `--dest NAME` | all | Name of the output folder (default `Organized`). Must be a plain name, not a path |
| `-r`, `--recursive` | scan, organize | Also look inside sub-folders |
| `--no-course` | scan, organize | Sort by file type only |
| `--dry-run` | organize | Show the moves, change nothing |
| `-y`, `--yes` | organize | Skip the confirmation question |

Run `python cli.py --help` or `python cli.py organize --help` for the built-in help.

Exit codes: `0` success, `1` error (message printed to stderr), `2` wrong arguments, `130` stopped with Ctrl+C.

### Optional window

```bash
python gui.py
```

Choose a folder, tick the options, then use **Preview**, **Organize** or **Undo**.

## Project structure

```
study-organizer/
├── cli.py                  Command-line interface (argparse with scan / organize / undo)
├── gui.py                  Optional tkinter window, calls the same functions as cli.py
├── organizer/
│   ├── __init__.py         Marks the folder as a Python package
│   ├── categories.py       The rules: extension → category, and the course-code regex
│   └── core.py             The engine: input checks, scanning, duplicates, moving, undo log
├── tests/
│   └── test_organizer.py   Unit tests (normal use, duplicates, bad input, damaged logs)
├── contributions/          One file per team member describing their work
└── README.md
```

### How the code works

1. **`validate_folder` / `validate_dest_name`** (core.py) check the user input first. A missing
   folder, a file instead of a folder, `/`, the home folder, or a destination like `../x` are
   rejected with a clear message.
2. **`find_files`** walks the folder with `os.walk` and yields only real, visible files. It never
   follows symbolic links and never enters the output folder.
3. **`find_duplicates`** groups files by size and hashes (SHA-256) only files whose size
   appears more than once. In each group of identical files the shortest name is kept as
   the original (`lecture.pdf`), the others (`lecture (1).pdf`) are duplicates.
4. **`plan_moves`** builds a list of `Move(source, target, is_duplicate)` objects:
   - `get_course` and `get_category` (categories.py) decide the target folder;
   - `unique_target` picks a free name so nothing is ever overwritten.
5. **`execute`** creates the folders, moves each file with `shutil.move`, collects errors instead
   of crashing, and appends the run to `organizer_log.json` (written to a temp file first, then
   swapped in, so the log is never half-written).
6. **`undo_last`** reads the log, checks that every path is still inside the chosen folder
   (an edited log cannot move files elsewhere), moves the files back and removes empty folders.

## Robustness

The tool is designed to fail safely:

- Wrong or missing arguments → argparse usage message, exit code 2.
- Missing folder, file instead of folder, `/`, home folder, no permission → clear error, exit code 1.
- Destination names with `/`, `\`, `..` or other special characters → rejected.
- Hidden files, symbolic links (e.g. a link to `/etc/passwd`) and the tool's own log → never moved.
- Two files with the same name (also from different sub-folders) → renamed, never overwritten.
- A file that cannot be read or moved → reported, the rest continue.
- A damaged or hand-edited `organizer_log.json` → refused, or the unsafe entries are skipped.
- Ctrl+C or Ctrl+D at the confirmation prompt → stops cleanly without changing anything.

## Running the tests

```bash
python -m unittest discover tests -v
```

## Course topics used

| Topic | Where |
|---|---|
| Functions | Every step is its own function: `get_course`, `get_category`, `plan_moves`, `execute`, `undo_last`, ... |
| Loops | Walking the folder, grouping by size, building the plan, moving, undoing |
| File I/O | `os.walk`, `pathlib`, `shutil.move`, reading files in chunks for hashing, JSON log |
| Automation | One command organizes a whole folder; `--yes` makes it scriptable |
| Also | `argparse`, regular expressions, `dataclasses`, generators (`yield`), custom exceptions, `hashlib`, `json`, `unittest` |

## Team

See the [`contributions/`](contributions) folder.
