from __future__ import annotations

import asyncio
import platform
import subprocess

import flet as ft

from src.models.schemas import AppConfig, CategoryRule
from src.services.antinote_service import get_antinote_db_path
from src.utils.config_manager import ConfigManager
from src.views import theme


class SettingsView:
    def __init__(self, page: ft.Page, config_manager: ConfigManager) -> None:
        self.page = page
        self.config_manager = config_manager
        self.categories: list[CategoryRule] = []
        self._editing_category_name: str | None = None
        self._is_picking_directory = False
        self._is_compact_mode = False

        self.title_text = theme.ios_title("Configurações")
        self.subtitle_text = theme.ios_subtitle("Personalize a IA e a pasta de notas.")

        self.api_key_field = ft.TextField(
            label="Chave da API",
            password=True,
            can_reveal_password=True,
            border=ft.InputBorder.NONE,
            color=theme.TEXT_PRIMARY,
            label_style=ft.TextStyle(color=theme.TEXT_SECONDARY, size=12),
            hint_style=ft.TextStyle(color=theme.TEXT_SECONDARY),
            cursor_color=theme.ACCENT,
            text_size=14,
            dense=True,
        )

        self._directory_loading_indicator = ft.ProgressRing(
            width=14,
            height=14,
            stroke_width=2,
            visible=False,
            color=theme.ACCENT,
        )
        self.notes_dir_field = ft.TextField(
            label="Pasta Base das Notas",
            border=ft.InputBorder.NONE,
            color=theme.TEXT_PRIMARY,
            label_style=ft.TextStyle(color=theme.TEXT_SECONDARY, size=12),
            hint_style=ft.TextStyle(color=theme.TEXT_SECONDARY),
            cursor_color=theme.ACCENT,
            text_size=14,
            dense=True,
            on_click=self._start_pick_directory,
            always_call_on_tap=True,
            suffix=self._directory_loading_indicator,
        )

        self.notes_hint_text = ft.Text(
            "Informe o caminho completo da pasta de notas.",
            size=12,
            color=theme.TEXT_SECONDARY,
        )

        self.notes_source_group = ft.RadioGroup(
            value="local",
            on_change=self._on_notes_source_changed,
            content=ft.Column(
                spacing=8,
                controls=[
                    ft.Radio(value="local", label="Buscar notas locais"),
                    ft.Radio(value="antinote", label="Buscar notas no Antinote"),
                ],
            ),
        )

        self.antinote_status_text = ft.Text(
            "",
            size=12,
            color=theme.TEXT_SECONDARY,
            visible=False,
        )

        self.local_source_container = ft.Column(
            spacing=10,
            controls=[
                ft.Row(
                    spacing=8,
                    controls=[
                        ft.Container(expand=True, content=theme.ios_input_container(self.notes_dir_field)),
                        ft.IconButton(
                            icon=ft.Icons.FOLDER_OPEN,
                            icon_color=theme.ACCENT,
                            tooltip="Selecionar pasta",
                            on_click=self._start_pick_directory,
                        ),
                    ],
                ),
                self.notes_hint_text,
            ],
        )

        self.base_prompt_field = ft.TextField(
            label="Prompt Base",
            border=ft.InputBorder.NONE,
            color=theme.TEXT_PRIMARY,
            label_style=ft.TextStyle(color=theme.TEXT_SECONDARY, size=12),
            hint_style=ft.TextStyle(color=theme.TEXT_SECONDARY),
            cursor_color=theme.ACCENT,
            text_size=14,
            multiline=True,
            min_lines=8,
            max_lines=12,
        )

        self.categories_column = ft.Column(spacing=8)

        self.dialog_name_field = ft.TextField(
            label="Nome da categoria",
            border=ft.InputBorder.NONE,
            color=theme.TEXT_PRIMARY,
            label_style=ft.TextStyle(color=theme.TEXT_SECONDARY, size=12),
            hint_style=ft.TextStyle(color=theme.TEXT_SECONDARY),
            cursor_color=theme.ACCENT,
            dense=True,
        )
        self.dialog_instruction_field = ft.TextField(
            label="O que a IA deve levar em consideração",
            border=ft.InputBorder.NONE,
            color=theme.TEXT_PRIMARY,
            label_style=ft.TextStyle(color=theme.TEXT_SECONDARY, size=12),
            hint_style=ft.TextStyle(color=theme.TEXT_SECONDARY),
            cursor_color=theme.ACCENT,
            multiline=True,
            min_lines=3,
            max_lines=6,
        )
        self.dialog_title_text = ft.Text("Nova categoria", weight=ft.FontWeight.W_700)
        self.dialog_save_button = ft.FilledButton(
            "Salvar",
            style=theme.ios_primary_button_style(),
            on_click=self._confirm_category_dialog,
        )

        self.new_category_dialog = ft.AlertDialog(
            modal=True,
            shape=ft.RoundedRectangleBorder(radius=theme.RADIUS_CARD),
            title=self.dialog_title_text,
            content=ft.Container(
                width=460,
                content=ft.Column(
                    tight=True,
                    spacing=12,
                    controls=[
                        theme.ios_input_container(self.dialog_name_field),
                        theme.ios_input_container(self.dialog_instruction_field),
                    ],
                ),
            ),
            actions=[
                ft.TextButton("Cancelar", style=theme.ios_secondary_button_style(), on_click=self._close_new_category_dialog),
                self.dialog_save_button,
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.api_section = ft.Column(
            spacing=8,
            controls=[
                theme.ios_section_title("INTEGRAÇÃO COM IA"),
                theme.ios_card(theme.ios_input_container(self.api_key_field)),
            ],
        )

        self.directory_section = ft.Column(
            spacing=8,
            controls=[
                theme.ios_section_title("FONTE DAS NOTAS"),
                theme.ios_card(
                    ft.Column(
                        spacing=10,
                        controls=[
                            self.notes_source_group,
                            self.local_source_container,
                            self.antinote_status_text,
                        ],
                    )
                ),
            ],
        )

        self.prompt_section = ft.Column(
            spacing=8,
            controls=[
                theme.ios_section_title("PROMPT BASE"),
                theme.ios_card(theme.ios_input_container(self.base_prompt_field)),
            ],
        )

        self.new_category_button = ft.TextButton(
            content="Nova categoria",
            icon=ft.Icons.ADD,
            style=theme.ios_secondary_button_style(),
            on_click=self._open_new_category_dialog,
        )

        self.categories_section = ft.Column(
            spacing=8,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        theme.ios_section_title("CATEGORIAS"),
                        self.new_category_button,
                    ],
                ),
                self.categories_column,
            ],
        )

        self.save_button = ft.FilledButton(
            content=ft.Text("Salvar Configurações", weight=ft.FontWeight.W_600),
            icon=ft.Icons.SAVE,
            style=theme.ios_primary_button_style(),
            on_click=self._save,
        )

        self.control = ft.Container(
            expand=True,
            bgcolor=theme.BG_PAGE,
            padding=24,
            content=ft.Column(
                expand=True,
                scroll=ft.ScrollMode.AUTO,
                spacing=18,
                controls=[
                    ft.Column(spacing=4, controls=[self.title_text, self.subtitle_text]),
                    self.api_section,
                    self.directory_section,
                    self.prompt_section,
                    self.categories_section,
                    ft.Container(padding=ft.Padding.only(top=8), content=self.save_button),
                ],
            ),
        )

    async def load(self) -> None:
        config = await self.config_manager.load()
        self.api_key_field.value = config.api_key
        self.notes_dir_field.value = config.notes_directory
        self.notes_source_group.value = config.notes_source if config.notes_source in {"local", "antinote"} else "local"
        self.base_prompt_field.value = config.base_prompt
        self.categories = list(config.categories)
        self._update_notes_source_ui()
        self._refresh_categories()
        self.page.update()

    def _open_new_category_dialog(self, _: ft.ControlEvent) -> None:
        self._editing_category_name = None
        self.dialog_title_text.value = "Nova categoria"
        self.dialog_save_button.text = "Salvar"
        self.dialog_name_field.value = ""
        self.dialog_instruction_field.value = ""
        if self.new_category_dialog not in self.page.overlay:
            self.page.overlay.append(self.new_category_dialog)
        self.new_category_dialog.open = True
        self.page.update()

    def _open_edit_category_dialog(self, category_name: str) -> None:
        category = next((item for item in self.categories if item.name == category_name), None)
        if category is None:
            self._show_snackbar("Categoria não encontrada para edição.")
            return

        self._editing_category_name = category.name
        self.dialog_title_text.value = "Editar categoria"
        self.dialog_save_button.text = "Atualizar"
        self.dialog_name_field.value = category.name
        self.dialog_instruction_field.value = category.instruction
        if self.new_category_dialog not in self.page.overlay:
            self.page.overlay.append(self.new_category_dialog)
        self.new_category_dialog.open = True
        self.page.update()

    def _close_new_category_dialog(self, _: ft.ControlEvent) -> None:
        self.new_category_dialog.open = False
        self.page.update()

    def _confirm_category_dialog(self, _: ft.ControlEvent) -> None:
        name = (self.dialog_name_field.value or "").strip()
        instruction = (self.dialog_instruction_field.value or "").strip()

        if not name:
            self._show_snackbar("Informe o nome da categoria.")
            return
        if not instruction:
            self._show_snackbar("Informe o que a IA deve levar em consideração para esta categoria.")
            return

        normalized = name.casefold()
        if any(
            item.name.casefold() == normalized
            and item.name != (self._editing_category_name or "")
            for item in self.categories
        ):
            self._show_snackbar("Categoria já existe.")
            return

        if self._editing_category_name is None:
            self.categories.append(CategoryRule(name=name, instruction=instruction))
        else:
            updated_categories: list[CategoryRule] = []
            for item in self.categories:
                if item.name == self._editing_category_name:
                    updated_categories.append(CategoryRule(name=name, instruction=instruction))
                else:
                    updated_categories.append(item)
            self.categories = updated_categories

        self._editing_category_name = None
        self.new_category_dialog.open = False
        self._refresh_categories()
        self.page.update()

    def _start_pick_directory(self, _: ft.ControlEvent) -> None:
        if self.notes_source_group.value != "local":
            return
        if self._is_picking_directory:
            return
        self.page.run_task(self._pick_directory_async)

    def _on_notes_source_changed(self, _: ft.ControlEvent) -> None:
        self._update_notes_source_ui()
        self.page.update()

    def _update_notes_source_ui(self) -> None:
        is_local = self.notes_source_group.value != "antinote"
        self.local_source_container.visible = is_local
        self.antinote_status_text.visible = not is_local
        if not is_local:
            try:
                db_path = get_antinote_db_path()
                self.antinote_status_text.value = f"✓ Banco do Antinote encontrado em {db_path}"
                self.antinote_status_text.color = theme.TAG_TEXT
            except FileNotFoundError:
                self.antinote_status_text.value = "✗ Banco do Antinote não encontrado neste Mac."
                self.antinote_status_text.color = theme.ERROR_TEXT

    async def _pick_directory_async(self) -> None:
        self._is_picking_directory = True
        self._directory_loading_indicator.visible = True
        self.page.update()

        selected_path: str = ""
        try:
            if platform.system() == "Darwin":
                script = 'POSIX path of (choose folder with prompt "Selecione a pasta de notas")'
                result = await asyncio.to_thread(
                    subprocess.run,
                    ["osascript", "-e", script],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if result.returncode == 0:
                    selected_path = result.stdout.strip()
                elif result.returncode != 1:
                    raise RuntimeError(result.stderr.strip() or "Falha ao abrir seletor de pasta")
            else:
                self._show_snackbar("Seletor nativo indisponível neste sistema. Informe o caminho manualmente.")
                return
        except Exception as error:
            self._show_snackbar(f"Falha ao abrir seletor de pasta: {error}")
        finally:
            self._is_picking_directory = False
            self._directory_loading_indicator.visible = False
            self.page.update()

        if selected_path:
            self.notes_dir_field.value = selected_path
            self.page.update()

    def set_compact_mode(self, is_compact: bool) -> None:
        self._is_compact_mode = is_compact
        self.control.padding = 14 if is_compact else 24
        self.title_text.size = 20 if is_compact else 30
        self.subtitle_text.size = 12 if is_compact else 14
        self.base_prompt_field.min_lines = 6 if is_compact else 8
        self.base_prompt_field.max_lines = 8 if is_compact else 12
        self.notes_hint_text.visible = not is_compact and self.notes_source_group.value == "local"

    def _remove_category(self, category_name: str) -> None:
        self.categories = [item for item in self.categories if item.name != category_name]
        self._refresh_categories()
        self.page.update()

    def _on_edit_category_click(self, event: ft.ControlEvent) -> None:
        category_name = str(getattr(event.control, "data", "") or "")
        if not category_name:
            self._show_snackbar("Não foi possível identificar a categoria para edição.")
            return
        self._open_edit_category_dialog(category_name)

    def _on_remove_category_click(self, event: ft.ControlEvent) -> None:
        category_name = str(getattr(event.control, "data", "") or "")
        if not category_name:
            self._show_snackbar("Não foi possível identificar a categoria para remoção.")
            return
        self._remove_category(category_name)

    def _refresh_categories(self) -> None:
        if not self.categories:
            self.categories_column.controls = [
                theme.ios_card(
                    ft.Text(
                        "Nenhuma categoria cadastrada.",
                        size=13,
                        color=theme.TEXT_SECONDARY,
                    )
                )
            ]
            return

        cards: list[ft.Control] = []
        for category in self.categories:
            cards.append(
                theme.ios_card(
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.START,
                        controls=[
                            ft.Column(
                                expand=True,
                                spacing=4,
                                controls=[
                                    ft.Text(
                                        category.name,
                                        weight=ft.FontWeight.W_600,
                                        color=theme.TEXT_PRIMARY,
                                    ),
                                    ft.Text(
                                        category.instruction,
                                        size=12,
                                        color=theme.TEXT_SECONDARY,
                                    ),
                                ],
                            ),
                            ft.IconButton(
                                icon=ft.Icons.EDIT_OUTLINED,
                                icon_color=theme.ACCENT,
                                tooltip="Editar categoria",
                                data=category.name,
                                on_click=self._on_edit_category_click,
                            ),
                            ft.IconButton(
                                icon=ft.Icons.DELETE_OUTLINE,
                                icon_color=theme.TEXT_SECONDARY,
                                tooltip="Remover categoria",
                                data=category.name,
                                on_click=self._on_remove_category_click,
                            ),
                        ],
                    ),
                    padding=12 if self._is_compact_mode else 14,
                )
            )
        self.categories_column.controls = cards

    async def _save(self, _: ft.ControlEvent) -> None:
        api_key = (self.api_key_field.value or "").strip()
        notes_source = (self.notes_source_group.value or "local").strip().lower()
        notes_directory = (self.notes_dir_field.value or "").strip()
        base_prompt = (self.base_prompt_field.value or "").strip()

        if not api_key:
            self._show_snackbar("Informe a API Key.")
            return
        if notes_source not in {"local", "antinote"}:
            self._show_snackbar("Selecione uma fonte de notas válida.")
            return
        if notes_source == "local" and not notes_directory:
            self._show_snackbar("Informe a pasta base das notas.")
            return
        if not base_prompt:
            self._show_snackbar("Informe um prompt base.")
            return
        if not self.categories:
            self._show_snackbar("Adicione ao menos uma categoria.")
            return

        config = AppConfig(
            api_key=api_key,
            notes_directory=notes_directory,
            notes_source=notes_source,
            base_prompt=base_prompt,
            categories=self.categories,
        )

        try:
            await self.config_manager.save(config)
            self._show_snackbar("Configurações salvas com sucesso.")
        except Exception as error:
            self._show_snackbar(f"Falha ao salvar configurações: {error}")

    def _show_snackbar(self, message: str) -> None:
        snackbar = ft.SnackBar(
            content=ft.Text(message, color=ft.Colors.WHITE),
            bgcolor=theme.TEXT_PRIMARY,
            behavior=ft.SnackBarBehavior.FLOATING,
        )
        self.page.overlay.append(snackbar)
        snackbar.open = True
        self.page.update()
