"""Scanning a folder, planning the moves, moving the files and undoing."""
import hashlib
import json
import os
import shutil
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .categories import get_category, get_course

DEFAULT_DEST = "Organized"
DUPLICATES = "Duplicates"
LOG_NAME = "organizer_log.json"
FORBIDDEN_CHARS = set('<>:"/\\|?*')


class OrganizerError(Exception):
    """A problem we can explain to the user (bad folder, broken log...)."""


@dataclass
class Move:
    source: Path
    target: Path
    is_duplicate: bool = False


# ---------- input checks ----------

def validate_folder(path):
    """Turn user input into a safe, absolute folder path."""
    if not str(path).strip():
        raise OrganizerError("Please give a folder.")
    folder = Path(path).expanduser()
    if not folder.exists():
        raise OrganizerError(f"Folder not found: {folder}")
    if not folder.is_dir():
        raise OrganizerError(f"Not a folder: {folder}")
    folder = folder.resolve()
    if folder == Path(folder.anchor):
        raise OrganizerError("Refusing to organize the root of a drive.")
    if folder == Path.home().resolve():
        raise OrganizerError("Refusing to organize the whole home folder.")
    if not os.access(folder, os.R_OK | os.W_OK | os.X_OK):
        raise OrganizerError(f"No permission to change files in: {folder}")
    return folder


def validate_dest_name(name):
    """The destination must be a plain folder name, never a path."""
    name = (name or "").strip()
    bad_chars = any(ch in FORBIDDEN_CHARS for ch in name)
    if not name or name in {".", ".."} or bad_chars:
        raise OrganizerError(f"Invalid destination name: {name!r}.")
    if len(name) > 100:
        raise OrganizerError("Destination name is too long.")
    return name


# ---------- scanning ----------

def find_files(folder, dest_name, recursive=False):
    """Yield the files to organize: no hidden files, links or output."""
    for root, dirs, files in os.walk(folder, followlinks=False):
        root = Path(root)
        # never enter hidden folders or our own destination folder
        dirs[:] = sorted(
            d for d in dirs
            if not d.startswith(".")
            and not (root == folder and d == dest_name)
        )
        for name in sorted(files):
            path = root / name
            if name.startswith(".") or name == LOG_NAME:
                continue
            if path.is_symlink() or not path.is_file():
                continue
            yield path
        if not recursive:
            break


def file_hash(path, chunk_size=65536):
    """SHA-256 of a file, read in 64 KB chunks to save memory."""
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def unique_target(path, reserved):
    """Return a free path: notes.pdf -> notes_1.pdf -> notes_2.pdf"""
    candidate, number = path, 1
    while candidate.exists() or candidate in reserved:
        candidate = path.with_name(f"{path.stem}_{number}{path.suffix}")
        number += 1
    return candidate


def find_duplicates(files, sizes):
    """Return the set of files whose content already exists in another."""
    # Only files with the same size can be identical, so hash just those.
    # Empty files are not counted as duplicates.
    size_count = Counter(sizes.values())
    hashes = {}
    for path in files:
        if sizes[path] > 0 and size_count[sizes[path]] > 1:
            try:
                hashes[path] = file_hash(path)
            except OSError:
                pass  # unreadable: treat it as a normal file

    # In each group of identical files the shortest name is the original:
    # "lecture.pdf" is kept, "lecture (1).pdf" is the copy.
    originals = {}
    for path in sorted(hashes, key=lambda p: (len(p.name), str(p))):
        originals.setdefault(hashes[path], path)
    return {p for p in hashes if originals[hashes[p]] != p}


def plan_moves(folder, dest_name=DEFAULT_DEST, by_course=True,
               recursive=False):
    """Decide where every file should go, without moving anything."""
    destination = folder / dest_name
    if destination.exists() and not destination.is_dir():
        raise OrganizerError(f"'{dest_name}' exists and is not a folder.")

    sizes = {}
    for path in find_files(folder, dest_name, recursive):
        try:
            sizes[path] = path.stat().st_size
        except OSError:
            continue  # file vanished or cannot be read: leave it alone
    files = list(sizes)
    duplicates = find_duplicates(files, sizes)

    reserved = set()
    moves = []
    for path in files:
        if path in duplicates:
            target_folder = destination / DUPLICATES
        else:
            course = get_course(path.name) if by_course else None
            category = get_category(path.name)
            target_folder = destination / (course or "") / category

        target = unique_target(target_folder / path.name, reserved)
        reserved.add(target)
        moves.append(Move(path, target, path in duplicates))
    return moves


def summarize(moves, destination):
    """Count how many files go into each target folder."""
    return Counter(
        str(m.target.parent.relative_to(destination)) for m in moves
    )


# ---------- moving and undo ----------

def load_log(log_path):
    """Read the undo log and make sure it has the expected shape."""
    if not log_path.exists():
        return []
    try:
        runs = json.loads(log_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError, OSError) as error:
        raise OrganizerError(f"The undo log is damaged: {error}")
    valid = isinstance(runs, list) and all(
        isinstance(r, dict) and isinstance(r.get("moves"), list)
        for r in runs
    )
    if not valid:
        raise OrganizerError("The undo log has an unexpected format.")
    return runs


def save_log(log_path, runs):
    """Write the log to a temp file first, then swap it in one step."""
    if not runs:
        log_path.unlink(missing_ok=True)
        return
    temp = log_path.with_suffix(".tmp")
    temp.write_text(json.dumps(runs, indent=2), encoding="utf-8")
    temp.replace(log_path)


def execute(moves, folder, dest_name=DEFAULT_DEST):
    """Move the files and remember every move so it can be undone."""
    destination = folder / dest_name
    done, failed = [], []
    for move in moves:
        try:
            move.target.parent.mkdir(parents=True, exist_ok=True)
            # check again, in case a file appeared since planning
            target = unique_target(move.target, set())
            shutil.move(str(move.source), str(target))
            done.append({"from": str(move.source), "to": str(target)})
        except OSError as error:
            failed.append(f"{move.source.name}: {error.strerror or error}")

    if done:
        log_path = destination / LOG_NAME
        runs = load_log(log_path)
        now = datetime.now().isoformat(timespec="seconds")
        runs.append({"time": now, "moves": done})
        save_log(log_path, runs)
    return len(done), failed


def is_inside(path, folder):
    try:
        return path.resolve().is_relative_to(folder)
    except (OSError, ValueError):
        return False


def undo_last(folder, dest_name=DEFAULT_DEST):
    """Put back the files from the last organize run."""
    destination = folder / dest_name
    log_path = destination / LOG_NAME
    runs = load_log(log_path)
    if not runs:
        raise OrganizerError("Nothing to undo in this folder.")

    restored, skipped = 0, []
    for entry in reversed(runs[-1]["moves"]):
        try:
            current, original = Path(entry["to"]), Path(entry["from"])
        except (KeyError, TypeError):
            skipped.append("a broken log entry")
            continue
        # an edited log must never move files outside this folder
        if not (is_inside(current, folder) and is_inside(original, folder)):
            skipped.append(f"{current.name} (path outside the folder)")
            continue
        if not current.is_file():
            skipped.append(f"{current.name} (no longer there)")
            continue
        try:
            original.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(current), str(unique_target(original, set())))
            restored += 1
        except OSError as error:
            skipped.append(f"{current.name}: {error.strerror or error}")

    runs.pop()
    save_log(log_path, runs)
    remove_empty_folders(destination)
    return restored, skipped


def remove_empty_folders(folder):
    """Delete empty folders left behind after an undo (deepest first)."""
    if not folder.is_dir():
        return
    paths = sorted(folder.rglob("*"), key=lambda p: len(p.parts))
    for path in reversed(paths):
        if path.is_dir() and not path.is_symlink() and not any(
            path.iterdir()
        ):
            path.rmdir()
    if not any(folder.iterdir()):
        folder.rmdir()
