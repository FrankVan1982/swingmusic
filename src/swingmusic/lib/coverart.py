"""
Filesystem cover art discovery and ranking.
"""

import re
from pathlib import Path

from PIL import Image

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

# name token -> score. Positive tokens mark front covers,
# negative tokens mark scans, booklets and other non-cover art.
TOKEN_SCORES = {
    "front": 8,
    "cover": 7,
    "folder": 6,
    "album": 5,
    "box": 2,
    "cd": -3,
    "small": -4,
    "back": -6,
    "spine": -6,
    "inlay": -6,
    "inside": -6,
    "disc": -8,
    "tray": -8,
    "booklet": -8,
    "matrix": -8,
}


def list_candidate_images(folder: Path) -> list[Path]:
    """
    Returns image files in the folder and its immediate subfolders.
    Hidden files and folders are skipped.
    """
    images: list[Path] = []

    try:
        entries = sorted(folder.iterdir())
    except OSError:
        return images

    subfolders: list[Path] = []

    for entry in entries:
        if entry.name.startswith("."):
            continue

        if entry.is_dir():
            subfolders.append(entry)
        elif entry.suffix.lower() in IMAGE_EXTENSIONS:
            images.append(entry)

    for subfolder in subfolders:
        try:
            children = sorted(subfolder.iterdir())
        except OSError:
            continue

        for child in children:
            if child.name.startswith("."):
                continue

            if child.is_file() and child.suffix.lower() in IMAGE_EXTENSIONS:
                images.append(child)

    return images


def get_name_score(filename: str) -> int:
    """
    Scores a filename by summing the scores of known tokens in it.
    Trailing digits are stripped from tokens before matching (eg. "cd1" -> "cd").
    """
    tokens = re.split(r"[^a-z0-9]+", filename.lower())
    score = 0

    for token in tokens:
        token = token.rstrip("0123456789")
        score += TOKEN_SCORES.get(token, 0)

    return score


def get_dimension_score(filepath: Path) -> int:
    """
    Scores an image by aspect ratio and resolution.
    Near-square, reasonably sized images score highest.
    """
    try:
        with Image.open(filepath) as img:
            width, height = img.size
    except (OSError, ValueError):
        return -4

    if width == 0 or height == 0:
        return -4

    ratio = max(width, height) / min(width, height)

    if ratio <= 1.1:
        score = 5
    elif ratio <= 1.4:
        score = 2
    elif ratio <= 1.8:
        score = -2
    else:
        score = -8

    short_edge = min(width, height)

    if short_edge >= 500:
        score += 4
    elif short_edge >= 256:
        score += 2
    else:
        score -= 4

    return score


def score_cover_image(filepath: Path, folder: Path) -> int:
    """
    Scores an image as an album cover candidate.
    Images directly in the album folder rank above ones in subfolders.
    """
    score = get_name_score(filepath.stem)
    score += get_dimension_score(filepath)

    if filepath.parent == folder:
        score += 2

    return score


def rank_cover_images(folder: Path) -> list[Path]:
    """
    Returns candidate cover images in the folder, best first.
    """
    images = list_candidate_images(folder)
    return sorted(
        images,
        key=lambda i: score_cover_image(i, folder),
        reverse=True,
    )


def find_best_cover(folder: Path) -> Path | None:
    """
    Returns the best cover image in the folder, or None.
    """
    ranked = rank_cover_images(folder)
    return ranked[0] if ranked else None
