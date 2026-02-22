from __future__ import annotations

import asyncio
import sqlite3
from datetime import datetime
from pathlib import Path

from src.models.schemas import AnalysisResult, NoteFile


def _get_db_path() -> Path:
    base_dir = Path.home() / ".notes_analyzer"
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir / "historico_app.db"


def _connect() -> sqlite3.Connection:
    return sqlite3.connect(_get_db_path())


def _init_db_sync() -> None:
    connection = _connect()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS historico (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data TEXT NOT NULL,
                hora TEXT NOT NULL,
                titulo TEXT NOT NULL,
                categoria TEXT NOT NULL,
                destino TEXT,
                justificativa TEXT,
                fonte TEXT NOT NULL,
                conteudo TEXT,
                resumo TEXT
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS resumos_dia (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data TEXT NOT NULL UNIQUE,
                resumo_texto TEXT NOT NULL,
                gerado_em TEXT NOT NULL
            )
            """
        )
        _ensure_column(cursor, "historico", "conteudo", "TEXT")
        _ensure_column(cursor, "historico", "resumo", "TEXT")
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_historico_data
            ON historico (data)
            """
        )
        connection.commit()
    finally:
        connection.close()


def _ensure_column(
    cursor: sqlite3.Cursor,
    table_name: str,
    column_name: str,
    column_type: str,
) -> None:
    cursor.execute(f"PRAGMA table_info({table_name})")
    existing_columns = {str(row[1]) for row in cursor.fetchall()}
    if column_name in existing_columns:
        return
    cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")


async def init_db() -> None:
    await asyncio.to_thread(_init_db_sync)


def _build_snippet(text: str, max_length: int = 80) -> str:
    collapsed = " ".join(text.split())
    if len(collapsed) <= max_length:
        return collapsed
    return f"{collapsed[:max_length].rstrip()}..."


def _save_results_batch_sync(
    results: list[AnalysisResult],
    source: str,
    notes: list[NoteFile] | None = None,
) -> None:
    if not results:
        return

    now = datetime.now()
    current_date = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M")

    rows: list[tuple[str, str, str, str, str, str, str, str, str]] = []
    if notes and len(notes) == len(results):
        for note, result in zip(notes, results):
            if result.error:
                continue
            content = note.content or ""
            rows.append(
                (
                    current_date,
                    current_time,
                    result.file_name,
                    result.category,
                    result.destination,
                    result.justification,
                    source,
                    content,
                    _build_snippet(content),
                )
            )
    else:
        for result in results:
            if result.error:
                continue
            rows.append(
                (
                    current_date,
                    current_time,
                    result.file_name,
                    result.category,
                    result.destination,
                    result.justification,
                    source,
                    "",
                    "",
                )
            )

    if not rows:
        return

    connection = _connect()
    try:
        cursor = connection.cursor()
        cursor.executemany(
            """
            INSERT INTO historico (
                data,
                hora,
                titulo,
                categoria,
                destino,
                justificativa,
                fonte,
                conteudo,
                resumo
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        connection.commit()
    finally:
        connection.close()


async def save_result(result: AnalysisResult, source: str) -> None:
    await save_results_batch([result], source)


async def save_results_batch(
    results: list[AnalysisResult],
    source: str,
    notes: list[NoteFile] | None = None,
) -> None:
    await asyncio.to_thread(_save_results_batch_sync, results, source, notes)


async def get_month_counts(year: int, month: int) -> dict[int, int]:
    return await asyncio.to_thread(_get_month_counts_sync, year, month)


def _get_month_counts_sync(year: int, month: int) -> dict[int, int]:
    year_str = f"{year:04d}"
    month_str = f"{month:02d}"

    connection = _connect()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT CAST(strftime('%d', data) AS INTEGER) AS dia, COUNT(*)
            FROM historico
            WHERE strftime('%Y', data) = ?
              AND strftime('%m', data) = ?
            GROUP BY dia
            """,
            (year_str, month_str),
        )
        rows = cursor.fetchall()
    finally:
        connection.close()

    return {int(day): int(total) for day, total in rows}


async def get_month_entries(year: int, month: int) -> list[dict[str, str]]:
    return await asyncio.to_thread(_get_month_entries_sync, year, month)


def _get_month_entries_sync(year: int, month: int) -> list[dict[str, str]]:
    year_str = f"{year:04d}"
    month_str = f"{month:02d}"

    connection = _connect()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
                        SELECT id, data, hora, titulo, categoria, destino, justificativa, fonte, conteudo, resumo
            FROM historico
            WHERE strftime('%Y', data) = ?
              AND strftime('%m', data) = ?
            ORDER BY data DESC, hora DESC, id DESC
            """,
            (year_str, month_str),
        )
        rows = cursor.fetchall()
    finally:
        connection.close()

    return [
        {
            "id": str(row[0]),
            "data": str(row[1]),
            "hora": str(row[2]),
            "titulo": str(row[3]),
            "categoria": str(row[4]),
            "destino": str(row[5] or ""),
            "justificativa": str(row[6] or ""),
            "fonte": str(row[7]),
            "conteudo": str(row[8] or ""),
            "resumo": str(row[9] or ""),
        }
        for row in rows
    ]


async def get_daily_summary(date_str: str) -> str | None:
    return await asyncio.to_thread(_get_daily_summary_sync, date_str)


def _get_daily_summary_sync(date_str: str) -> str | None:
    connection = _connect()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT resumo_texto
            FROM resumos_dia
            WHERE data = ?
            """,
            (date_str,),
        )
        row = cursor.fetchone()
    finally:
        connection.close()

    if row is None:
        return None
    return str(row[0] or "")


async def save_daily_summary(date_str: str, summary: str) -> None:
    await asyncio.to_thread(_save_daily_summary_sync, date_str, summary)


def _save_daily_summary_sync(date_str: str, summary: str) -> None:
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    connection = _connect()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO resumos_dia (data, resumo_texto, gerado_em)
            VALUES (?, ?, ?)
            """,
            (date_str, summary, generated_at),
        )
        connection.commit()
    finally:
        connection.close()


async def delete_daily_summary(date_str: str) -> None:
    await asyncio.to_thread(_delete_daily_summary_sync, date_str)


def _delete_daily_summary_sync(date_str: str) -> None:
    connection = _connect()
    try:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM resumos_dia WHERE data = ?", (date_str,))
        connection.commit()
    finally:
        connection.close()


async def update_entry_analysis(
    entry_id: int,
    category: str,
    destination: str,
    justification: str,
) -> None:
    await asyncio.to_thread(
        _update_entry_analysis_sync,
        entry_id,
        category,
        destination,
        justification,
    )


def _update_entry_analysis_sync(
    entry_id: int,
    category: str,
    destination: str,
    justification: str,
) -> None:
    now = datetime.now()
    current_date = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M")

    connection = _connect()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            UPDATE historico
            SET data = ?,
                hora = ?,
                categoria = ?,
                destino = ?,
                justificativa = ?
            WHERE id = ?
            """,
            (current_date, current_time, category, destination, justification, entry_id),
        )
        connection.commit()
    finally:
        connection.close()


async def delete_entry(entry_id: int) -> None:
    await asyncio.to_thread(_delete_entry_sync, entry_id)


def _delete_entry_sync(entry_id: int) -> None:
    connection = _connect()
    try:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM historico WHERE id = ?", (entry_id,))
        connection.commit()
    finally:
        connection.close()


async def clear_history() -> None:
    await asyncio.to_thread(_clear_history_sync)


def _clear_history_sync() -> None:
    connection = _connect()
    try:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM historico")
        cursor.execute("DELETE FROM resumos_dia")
        connection.commit()
    finally:
        connection.close()


async def restore_entry(entry: dict[str, str]) -> None:
    await asyncio.to_thread(_restore_entry_sync, entry)


def _restore_entry_sync(entry: dict[str, str]) -> None:
    content = str(entry.get("conteudo", "") or "")
    snippet = str(entry.get("resumo", "") or "")
    if not snippet and content:
        snippet = _build_snippet(content)

    connection = _connect()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO historico (
                data,
                hora,
                titulo,
                categoria,
                destino,
                justificativa,
                fonte,
                conteudo,
                resumo
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(entry.get("data", "")),
                str(entry.get("hora", "")),
                str(entry.get("titulo", "")),
                str(entry.get("categoria", "")),
                str(entry.get("destino", "")),
                str(entry.get("justificativa", "")),
                str(entry.get("fonte", "")),
                content,
                snippet,
            ),
        )
        connection.commit()
    finally:
        connection.close()
