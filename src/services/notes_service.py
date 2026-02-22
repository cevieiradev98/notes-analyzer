from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

from src.models.schemas import NoteFile

_ALLOWED_EXTENSIONS = {".txt", ".md"}


def _is_created_or_modified_today(file_path: Path, today: date) -> bool:
    stats = file_path.stat()
    modified_date = datetime.fromtimestamp(stats.st_mtime).date()

    created_date: date | None = None
    birth_time = getattr(stats, "st_birthtime", None)
    if isinstance(birth_time, (float, int)):
        created_date = datetime.fromtimestamp(birth_time).date()

    return modified_date == today or (created_date == today if created_date is not None else False)


def get_today_notes(directory: str) -> list[NoteFile]:
    notes_dir = Path(directory)
    if not notes_dir.exists() or not notes_dir.is_dir():
        raise FileNotFoundError(f"Pasta não encontrada: {directory}")

    today = date.today()
    notes: list[NoteFile] = []

    for file_path in notes_dir.iterdir():
        if not file_path.is_file() or file_path.suffix.lower() not in _ALLOWED_EXTENSIONS:
            continue

        try:
            if not _is_created_or_modified_today(file_path, today):
                continue

            content = file_path.read_text(encoding="utf-8")
            modified_at = datetime.fromtimestamp(file_path.stat().st_mtime)
            notes.append(
                NoteFile(
                    file_name=file_path.name,
                    file_path=str(file_path),
                    modified_at=modified_at,
                    content=content,
                )
            )
        except (PermissionError, UnicodeDecodeError, OSError):
            continue

    notes.sort(key=lambda item: item.modified_at, reverse=True)
    return notes
