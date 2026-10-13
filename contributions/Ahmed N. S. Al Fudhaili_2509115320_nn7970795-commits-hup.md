## My role
I was responsible for `gui.py`, the optional graphical window of Study Organizer.
It lets users who do not like the terminal use the same features as the CLI.

## What I built

### `gui.py` — the `OrganizerWindow` class
- **Layout (`__init__`):** built the window with tkinter: a title, a folder
  entry with a **Browse** button, two checkboxes (*Sort by course code* and
  *Include sub-folders*), a `Listbox` for the preview, a status label, and the
  **Preview / Organize / Undo** buttons. The buttons are created in a loop
  over a tuple of `(text, command)` pairs instead of repeating the same code.
- **`browse()`:** opens the folder picker (`filedialog.askdirectory`) and
  shows the preview straight away.
- **`get_moves()`:** validates the folder and calls `plan_moves()` from the
  `organizer` package with the options from the checkboxes.
- **`_preview()`:** fills the list with how many files go to each folder,
  using `summarize()`.
- **`_organize()`:** asks for confirmation with `messagebox.askyesno`, then
  calls `execute()` and shows how many files were moved and which failed.
- **`_undo()`:** calls `undo_last()` and shows how many files were restored.
- **`run_safely()`:** wraps every button action in `try / except
  OrganizerError`, so bad input shows an error box instead of crashing.

### Design decision
The GUI contains no sorting logic of its own. It only calls the same
functions as `cli.py`, so both interfaces always behave the same way and the
logic is written and tested in one place.

## Other work
- <ADD HERE if you made the improvement: "Added the number of duplicate files
  to the status bar of the preview (commit: Show duplicate count in GUI preview).">
- Tested the window on my computer (<Windows / macOS>).

## What I learned
How to build a GUI with tkinter (widgets, layout with `pack`, variables like
`StringVar` and `BooleanVar`, dialogs), how to organize a GUI as a class, and
why it is better to keep the logic separate from the interface.

