"""Tests for Study Organizer. Run with:  python -m unittest discover tests"""
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import cli
from organizer.categories import get_category, get_course
from organizer.core import (
    LOG_NAME, OrganizerError, execute, plan_moves, undo_last,
    validate_dest_name, validate_folder,
)


def run_cli(*args):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = cli.main(list(args))
    return code, out.getvalue(), err.getvalue()


class TestRules(unittest.TestCase):
    def test_category(self):
        self.assertEqual(get_category("lecture.PDF"), "Lectures_and_Notes")
        self.assertEqual(get_category("main.py"), "Code")
        self.assertEqual(get_category("no_extension"), "Other")
        self.assertEqual(get_category("archive.tar.gz"), "Archives")

    def test_course(self):
        self.assertEqual(get_course("COE203_Lecture1.pdf"), "COE203")
        self.assertEqual(get_course("math-101 hw.xlsx"), "MATH101")
        self.assertEqual(get_course("COE 203 slides.pptx"), "COE203")
        self.assertIsNone(get_course("IMG_123.jpg"))
        self.assertIsNone(get_course("photo_2024.jpg"))
        self.assertIsNone(get_course("notes.txt"))


class TestOrganizer(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.folder = Path(self.temp.name).resolve()

    def tearDown(self):
        self.temp.cleanup()

    def make(self, name, content="x"):
        path = self.folder / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        return path

    def test_organize_and_undo(self):
        self.make("COE203_lecture.pdf", "a")
        self.make("notes.txt", "b")
        moves = plan_moves(self.folder)
        moved, failed = execute(moves, self.folder)
        self.assertEqual((moved, failed), (2, []))
        target = "Organized/COE203/Lectures_and_Notes/COE203_lecture.pdf"
        self.assertTrue((self.folder / target).exists())

        restored, skipped = undo_last(self.folder)
        self.assertEqual((restored, skipped), (2, []))
        self.assertTrue((self.folder / "notes.txt").exists())
        self.assertFalse((self.folder / "Organized").exists())

    def test_duplicates_keep_shortest_name(self):
        self.make("lecture.pdf", "same")
        self.make("lecture (1).pdf", "same")
        self.make("other.pdf", "diff")
        moves = plan_moves(self.folder)
        dupes = [m.source.name for m in moves if m.is_duplicate]
        self.assertEqual(dupes, ["lecture (1).pdf"])

    def test_name_clash_never_overwrites(self):
        self.make("a/notes.txt", "1")
        self.make("b/notes.txt", "2")
        moves = plan_moves(self.folder, recursive=True)
        targets = [m.target.name for m in moves]
        self.assertEqual(sorted(targets), ["notes.txt", "notes_1.txt"])

    def test_skips_hidden_links_and_destination(self):
        self.make(".secret", "x")
        self.make("Organized/old.pdf", "x")
        (self.folder / "link.txt").symlink_to("/etc/hosts")
        self.assertEqual(plan_moves(self.folder, recursive=True), [])

    def test_bad_inputs(self):
        with self.assertRaises(OrganizerError):
            validate_folder(self.folder / "missing")
        with self.assertRaises(OrganizerError):
            validate_folder(self.make("file.txt"))
        with self.assertRaises(OrganizerError):
            validate_folder("")
        with self.assertRaises(OrganizerError):
            validate_folder("/")
        for name in ["", "..", "../escape", "a/b", "a\\b", "x" * 200]:
            with self.assertRaises(OrganizerError):
                validate_dest_name(name)

    def test_damaged_log(self):
        log = self.folder / "Organized" / LOG_NAME
        log.parent.mkdir()
        log.write_text("{not json")
        with self.assertRaises(OrganizerError):
            undo_last(self.folder)

    def test_edited_log_cannot_move_files_outside(self):
        outside = tempfile.NamedTemporaryFile(delete=False)
        outside.close()
        log = self.folder / "Organized" / LOG_NAME
        log.parent.mkdir()
        entry = {"from": str(self.folder / "x"), "to": outside.name}
        log.write_text(json.dumps([{"moves": [entry]}]))
        restored, skipped = undo_last(self.folder)
        self.assertEqual(restored, 0)
        self.assertTrue(Path(outside.name).exists())
        os.unlink(outside.name)


class TestCli(unittest.TestCase):
    def test_dry_run_changes_nothing(self):
        with tempfile.TemporaryDirectory() as temp:
            Path(temp, "COE203.pdf").write_text("x")
            code, out, _ = run_cli("organize", temp, "--dry-run")
            self.assertEqual(code, 0)
            self.assertIn("Dry run", out)
            self.assertTrue(Path(temp, "COE203.pdf").exists())

    def test_errors_are_messages_not_crashes(self):
        code, _, err = run_cli("scan", "/no/such/folder")
        self.assertEqual(code, 1)
        self.assertIn("Folder not found", err)
        with tempfile.TemporaryDirectory() as temp:
            code, _, err = run_cli("organize", temp, "--dest", "../../etc")
            self.assertEqual(code, 1)
            self.assertIn("Invalid destination", err)


if __name__ == "__main__":
    unittest.main()


