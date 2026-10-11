"""Rules that decide where a file belongs: its type and its course code."""
import re

# Each category and the file extensions that belong to it
CATEGORIES = {
    "Lectures_and_Notes": {".pdf", ".docx", ".doc", ".txt", ".md"},
    "Slides": {".pptx", ".ppt", ".key"},
    "Assignments_and_Data": {".xlsx", ".xls", ".csv"},
    "Code": {
        ".py", ".ipynb", ".java", ".cpp", ".c", ".h", ".html", ".css", ".js",
    },
    "Media": {".mp4", ".mp3", ".m4a", ".wav", ".png", ".jpg", ".jpeg"},
    "Archives": {".zip", ".rar", ".7z", ".tar", ".gz"},
}
OTHER = "Other"

# A course code is 2-4 letters + 3 digits: COE203, MATH101, coe-203
COURSE_PATTERN = re.compile(r"(?<![A-Za-z])([A-Za-z]{2,4})[ _-]?(\d{3})(?!\d)")

# Camera / phone file names that look like course codes but are not
NOT_COURSES = {"IMG", "DSC", "VID", "PXL", "SCAN", "PIC"}


def get_category(filename):
    """Return the category for a file name, based on its extension."""
    if "." not in filename:
        return OTHER
    extension = "." + filename.rsplit(".", 1)[-1].lower()
    for category, extensions in CATEGORIES.items():
        if extension in extensions:
            return category
    return OTHER


def get_course(filename):
    """Return the course code in a file name (e.g. 'COE203') or None."""
    for match in COURSE_PATTERN.finditer(filename):
        letters, digits = match.group(1).upper(), match.group(2)
        if letters not in NOT_COURSES:
            return letters + digits
    return None
