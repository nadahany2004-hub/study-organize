# Contribution — Nada Hany (<2509115192>, @nadahany2004-hub)

## My role
I was responsible for the `organizer/` package: the core engine that decides
where each file goes, moves the files, detects duplicates and supports undo.
Both `cli.py` and `gui.py` are built on top of it. I also created the
repository and added the team as collaborators.

## What I built

### `organizer/categories.py` — the sorting rules
- **`CATEGORIES`:** a dictionary that maps each folder name to a set of file
  extensions (lectures, slides, assignments, code, media, archives).
- **`get_category(filename)`:** reads the extension (case-insensitive, so
  `.PDF` and `.pdf` are the same) and loops over the dictionary to find the
  matching folder, or returns `"Other"`.
- **`COURSE_PATTERN`:** a regular expression that finds course codes such as
  `COE203`, `coe-203` or `COE 203` (2–4 letters, an optional space / `_` /
  `-`, then 3 digits).
- **`get_course(filename)`:** returns the course code, and ignores camera
  names like `IMG_123` using the `NOT_COURSES` set.

### `organizer/core.py` — the engine
- **Input validation:** `validate_folder()` rejects missing paths, files, the
  drive root (`/`) and the home folder; `validate_dest_name()` rejects names
  like `../etc` or names with special characters. Problems are raised as
  `OrganizerError`, a custom exception the CLI and GUI turn into messages.
- **Scanning:** `find_files()` walks the folder with `os.walk` as a generator
  (`yield`) and skips hidden files, symbolic links and the output folder.
- **Duplicate detection:** `file_hash()` computes SHA-256 while reading the
  file in 64 KB chunks, so big videos never fill the memory.
  `find_duplicates()` only hashes files that share the same size, and keeps
  the file with the shortest name as the original (`lecture.pdf` is kept,
  `lecture (1).pdf` goes to `Duplicates`).
- **Planning:** `plan_moves()` builds a list of `Move` objects (a
  `dataclass`) without moving anything — this is what makes `--dry-run`
  possible. `unique_target()` adds `_1`, `_2` … so no file is overwritten.
- **Moving + undo log:** `execute()` moves the files with `shutil.move`,
  collects errors instead of crashing, and saves every move to
  `organizer_log.json`. `save_log()` writes to a temp file first and then
  replaces the log in one step, so it is never left half-written.
- **Undo:** `undo_last()` reads the log, uses `is_inside()` to check every
  path is still inside the chosen folder (so an edited log cannot move files
  elsewhere), moves the files back and removes empty folders with
  `remove_empty_folders()`.

### `organizer/__init__.py`
Marks the folder as a Python package so `cli.py` and `gui.py` can import it.

## Other work
- Created the public GitHub repository and added the team as collaborators.
- Uploaded the `organizer/` package.

## What I learned
How to split a program into reusable functions and modules, use loops and
generators to process many files, work safely with files and folders
(`pathlib`, `os`, `shutil`, `hashlib`, `json`), write regular expressions,
use dataclasses and custom exceptions, and validate user input so the
program fails safely instead of crashing.

