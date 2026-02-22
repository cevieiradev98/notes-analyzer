from __future__ import annotations

import sqlite3
from datetime import date, datetime
from pathlib import Path

from src.models.schemas import NoteFile

ANTINOTE_DB_PATH = Path.home() / "Library/Containers/com.chabomakers.Antinote/Data/Documents/notes.sqlite3"


def get_antinote_db_path() -> Path:
    if not ANTINOTE_DB_PATH.exists():
        raise FileNotFoundError(f"Banco do Antinote não encontrado: {ANTINOTE_DB_PATH}")
    return ANTINOTE_DB_PATH


def _parse_antinote_datetime(value: str) -> datetime:
    raw = (value or "").strip()
    if not raw:
        return datetime.min

    normalized = raw.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
        if parsed.tzinfo is not None:
            return parsed.astimezone().replace(tzinfo=None)
        return parsed
    except ValueError:
        pass

    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue

    return datetime.min


def get_today_notes_from_antinote() -> list[NoteFile]:
    db_path = get_antinote_db_path()
    today = date.today()
    notes: list[NoteFile] = []

    connection = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT id, created, lastModified, content FROM notes")
        rows = cursor.fetchall()

        for row in rows:
            note_id = str(row[0] or "").strip()
            created_text = str(row[1] or "")
            modified_text = str(row[2] or "")
            content = str(row[3] or "")

            if not note_id or not content.strip():
                continue

            created_at = _parse_antinote_datetime(created_text)
            modified_at = _parse_antinote_datetime(modified_text)

            if created_at.date() != today and modified_at.date() != today:
                continue

            notes.append(
                NoteFile(
                    file_name=f"Antinote {note_id[:8]}",
                    file_path=f"antinote://{note_id}",
                    modified_at=modified_at if modified_at != datetime.min else created_at,
                    content=content,
                )
            )
    except sqlite3.Error as error:
        raise RuntimeError(f"Falha ao ler banco do Antinote: {error}") from error
    finally:
        connection.close()

    notes.sort(key=lambda item: item.modified_at, reverse=True)
    return notes
