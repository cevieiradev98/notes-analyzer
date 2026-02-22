from __future__ import annotations

import json
from pathlib import Path

import flet as ft

from src.models.schemas import AppConfig


class ConfigManager:
    _PREFIX = "notesanalyzer."

    def __init__(self, page: ft.Page) -> None:
        self.page = page
        self._config_file = Path(__file__).resolve().parents[2] / ".notes_analyzer_config.json"

    async def load(self) -> AppConfig:
        if hasattr(self.page, "client_storage"):
            api_key = await self.page.client_storage.get_async(f"{self._PREFIX}api_key")
            notes_directory = await self.page.client_storage.get_async(f"{self._PREFIX}notes_directory")
            notes_source = await self.page.client_storage.get_async(f"{self._PREFIX}notes_source")
            base_prompt = await self.page.client_storage.get_async(f"{self._PREFIX}base_prompt")
            categories = await self.page.client_storage.get_async(f"{self._PREFIX}categories")

            raw_data = {
                "api_key": api_key or "",
                "notes_directory": notes_directory or "",
                "notes_source": notes_source or "local",
                "base_prompt": base_prompt or AppConfig().base_prompt,
                "categories": categories if isinstance(categories, list) else AppConfig().categories,
            }
            return AppConfig.from_dict(raw_data)

        if not self._config_file.exists():
            return AppConfig()

        try:
            data = json.loads(self._config_file.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                return AppConfig()
            return AppConfig.from_dict(data)
        except (json.JSONDecodeError, OSError):
            return AppConfig()

    async def save(self, config: AppConfig) -> None:
        payload = config.to_dict()
        if hasattr(self.page, "client_storage"):
            await self.page.client_storage.set_async(f"{self._PREFIX}api_key", payload["api_key"])
            await self.page.client_storage.set_async(
                f"{self._PREFIX}notes_directory", payload["notes_directory"]
            )
            await self.page.client_storage.set_async(
                f"{self._PREFIX}notes_source", payload["notes_source"]
            )
            await self.page.client_storage.set_async(
                f"{self._PREFIX}base_prompt", payload["base_prompt"]
            )
            await self.page.client_storage.set_async(
                f"{self._PREFIX}categories", payload["categories"]
            )
            return

        self._config_file.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
