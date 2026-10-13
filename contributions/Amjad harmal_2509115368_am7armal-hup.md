## My role
I was responsible for `tests/test_organizer.py`: the automated tests that
prove the program works and that bad input cannot break it.

## What I built

### `tests/test_organizer.py` — 11 tests with `unittest`
Run with: `python -m unittest discover tests -v`

**`TestRules` — the sorting rules**
- `test_category`: extensions map to the right folder, including capitals
  (`lecture.PDF`), files without an extension and `archive.tar.gz`.
- `test_course`: finds `COE203`, `math-101` and `COE 203`, and correctly
  ignores `IMG_123.jpg`, `photo_2024.jpg` and `notes.txt`.

**`TestOrganizer` — the engine** (each test runs in a temporary folder made
in `setUp()` and deleted in `tearDown()`)
- `test_organize_and_undo`: files are moved to the right place, then undo
  puts every file back and removes the empty output folder.
- `test_duplicates_keep_shortest_name`: `lecture.pdf` is kept and
  `lecture (1).pdf` is marked as the duplicate.
- `test_name_clash_never_overwrites`: two `notes.txt` from different
  sub-folders become `notes.txt` and `notes_1.txt`.
- `test_skips_hidden_links_and_destination`: hidden files, symbolic links and
  the output folder are never moved.
- `test_bad_inputs`: missing folder, a file instead of a folder, empty input,
  `/`, and destination names like `..`, `../escape`, `a/b` and a 200-character
  name are all rejected.
- `test_damaged_log`: a broken `organizer_log.json` gives a clear error.
- `test_edited_log_cannot_move_files_outside`: a log edited to point outside
  the folder cannot move that file (security test).

**`TestCli` — the command line**
- `test_dry_run_changes_nothing`: `--dry-run` prints the plan and moves nothing.
- `test_errors_are_messages_not_crashes`: a missing folder and `--dest
  ../../etc` return exit code 1 with a message, not a crash.

## Other work
- Tried to break the program by hand with strange input (Arabic and very long
  file names, files without extensions, empty files, Ctrl+D at the prompt).

## What I learned
How to write unit tests with `unittest` (`setUp`, `tearDown`, `assertEqual`,
`assertRaises`), how to use temporary folders so tests never touch real
files, and how to think like an attacker to test robustness.

