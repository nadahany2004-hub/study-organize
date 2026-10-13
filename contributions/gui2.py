"""Optional window for Study Organizer. Uses the same code as cli.py."""
import tkinter as tk
from tkinter import filedialog, messagebox

from organizer.core import (
    DEFAULT_DEST, OrganizerError, execute, plan_moves, summarize,
    undo_last, validate_folder,
)


class OrganizerWindow:
    def __init__(self, root):
        self.root = root
        root.title("Study Organizer")
        root.geometry("640x460")

        title = tk.Label(root, text="Study Organizer",
                         font=("Arial", 18, "bold"))
        title.pack(pady=10)

        row = tk.Frame(root)
        row.pack(fill="x", padx=20)
        self.folder_var = tk.StringVar()
        entry = tk.Entry(row, textvariable=self.folder_var)
        entry.pack(side="left", fill="x", expand=True)
        browse = tk.Button(row, text="Browse", command=self.browse)
        browse.pack(side="left", padx=(8, 0))

        self.by_course = tk.BooleanVar(value=True)
        self.recursive = tk.BooleanVar(value=False)
        for text, var in (("Sort by course code", self.by_course),
                          ("Include sub-folders", self.recursive)):
            box = tk.Checkbutton(root, text=text, variable=var)
            box.pack(anchor="w", padx=20)

        self.result_list = tk.Listbox(root, height=12)
        self.result_list.pack(fill="both", expand=True, padx=20, pady=10)
        self.status = tk.Label(root, text="Choose a folder to see a preview.")
        self.status.pack()

        buttons = tk.Frame(root)
        buttons.pack(pady=10)
        actions = (("Preview", self.preview), ("Organize", self.organize),
                   ("Undo", self.undo))
        for text, command in actions:
            button = tk.Button(buttons, text=text, width=12, command=command)
            button.pack(side="left", padx=6)

    def browse(self):
        folder = filedialog.askdirectory(title="Select a folder to organize")
        if folder:
            self.folder_var.set(folder)
            self.preview()

    def get_moves(self):
        folder = validate_folder(self.folder_var.get())
        moves = plan_moves(folder, DEFAULT_DEST, self.by_course.get(),
                           self.recursive.get())
        return folder, moves

    def preview(self):
        self.run_safely(self._preview)

    def _preview(self):
        folder, moves = self.get_moves()
        self.result_list.delete(0, tk.END)
        counts = summarize(moves, folder / DEFAULT_DEST)
        for target, count in sorted(counts.items()):
            self.result_list.insert(tk.END, f"{count:4d}  ->  {target}")
        self.status.config(text=f"{len(moves)} file(s) found.")

    def organize(self):
        self.run_safely(self._organize)

    def _organize(self):
        folder, moves = self.get_moves()
        if not moves:
            messagebox.showinfo("Nothing to do", "No files to organize.")
            return
        question = f"Move {len(moves)} file(s) into '{DEFAULT_DEST}'?"
        if messagebox.askyesno("Confirm", question):
            moved, failed = execute(moves, folder)
            self._preview()
            message = f"Moved {moved} file(s)."
            if failed:
                message += "\n\nCould not move:\n" + "\n".join(failed[:10])
            messagebox.showinfo("Done", message)

    def undo(self):
        self.run_safely(self._undo)

    def _undo(self):
        folder = validate_folder(self.folder_var.get())
        restored, skipped = undo_last(folder)
        self._preview()
        message = f"Restored {restored} file(s)."
        if skipped:
            message += f"\nSkipped {len(skipped)} file(s)."
        messagebox.showinfo("Undo", message)

    def run_safely(self, action):
        try:
            action()
        except OrganizerError as error:
            messagebox.showerror("Study Organizer", str(error))


if __name__ == "__main__":
    window = tk.Tk()
    OrganizerWindow(window)
    window.mainloop()
