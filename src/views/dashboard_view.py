from __future__ import annotations

import flet as ft

from src.models.schemas import AnalysisResult
from src.services.ai_service import AIService
from src.services.antinote_service import get_today_notes_from_antinote
from src.services import history_service
from src.services.notes_service import get_today_notes
from src.utils.config_manager import ConfigManager
from src.views import theme


class DashboardView:
    def __init__(self, page: ft.Page, config_manager: ConfigManager) -> None:
        self.page = page
        self.config_manager = config_manager
        self._latest_results: list[AnalysisResult] = []
        self._is_compact_mode = False

        self.progress_ring = ft.ProgressRing(
            visible=False,
            width=18,
            height=18,
            color=theme.ACCENT,
            stroke_width=3,
        )
        self.progress_text = ft.Text(visible=False, color=theme.TEXT_SECONDARY, size=14)

        self.title_text = theme.ios_title("Dashboard")
        self.subtitle_text = theme.ios_subtitle(
            "Analise e organize automaticamente as notas criadas hoje.",
        )

        self.analyze_button = ft.FilledButton(
            content=ft.Text("Analisar Notas de Hoje", weight=ft.FontWeight.W_600),
            icon=ft.Icons.AUTO_AWESOME,
            style=theme.ios_primary_button_style(),
            on_click=self._analyze_notes,
        )

        self.empty_state_text = ft.Text(
            "Clique em 'Analisar Notas de Hoje' para iniciar.",
            color=theme.TEXT_SECONDARY,
            text_align=ft.TextAlign.CENTER,
        )
        self.empty_state_card = theme.ios_card(
            ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
                controls=[
                    ft.Icon(ft.Icons.DESCRIPTION_OUTLINED, size=30, color=theme.TEXT_SECONDARY),
                    self.empty_state_text,
                ],
            )
        )

        self.results_column = ft.Column(spacing=10)
        self.results_container = ft.Column(visible=False, spacing=10, controls=[self.results_column])

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
                    ft.Container(
                        content=self.analyze_button,
                        width=320,
                    ),
                    ft.Row(
                        spacing=10,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[self.progress_ring, self.progress_text],
                    ),
                    self.empty_state_card,
                    self.results_container,
                ],
            ),
        )

    async def _analyze_notes(self, _: ft.ControlEvent) -> None:
        config = await self.config_manager.load()
        await history_service.init_db()

        if not config.api_key:
            self._show_snackbar("API Key não configurada. Vá em Configurações.")
            return
        if config.notes_source == "local" and not config.notes_directory:
            self._show_snackbar("Pasta base não configurada. Vá em Configurações.")
            return

        self.results_column.controls = []
        self.results_container.visible = False
        self.empty_state_card.visible = False
        self.progress_ring.visible = True
        self.progress_text.value = "Lendo notas do dia..."
        self.progress_text.visible = True
        self.page.update()

        try:
            if config.notes_source == "antinote":
                notes = get_today_notes_from_antinote()
            else:
                notes = get_today_notes(config.notes_directory)
        except FileNotFoundError:
            if config.notes_source == "antinote":
                self._finish_loading_with_message("Banco do Antinote não encontrado.")
            else:
                self._finish_loading_with_message("Pasta não encontrada.")
            return
        except PermissionError:
            if config.notes_source == "antinote":
                self._finish_loading_with_message("Sem permissão para ler o banco do Antinote.")
            else:
                self._finish_loading_with_message("Sem permissão para ler a pasta selecionada.")
            return
        except Exception as error:
            self._finish_loading_with_message(f"Erro ao ler notas: {error}")
            return

        if not notes:
            self._finish_loading_with_message("Nenhuma nota encontrada para hoje.")
            return

        ai_service = AIService(config.api_key)
        try:
            def on_progress(current: int, total: int) -> None:
                self.progress_text.value = f"Analisando nota {current} de {total}..."
                self.page.update()

            results = await ai_service.analyze_batch(
                notes=notes,
                base_prompt=config.base_prompt,
                categories=config.categories,
                on_progress=on_progress,
            )
        finally:
            await ai_service.close()

        self._latest_results = results
        await history_service.save_results_batch(results, config.notes_source, notes=notes)
        self._render_results_cards()

        self.progress_ring.visible = False
        self.progress_text.visible = False
        self.results_container.visible = True
        self.empty_state_card.visible = False
        self.page.update()

    def on_host_resized(self) -> None:
        if not self.results_container.visible or not self._latest_results:
            return
        self._render_results_cards()

    def _result_card(self, item: AnalysisResult) -> ft.Control:
        has_error = bool(item.error)
        tag_bg = theme.ERROR_BG if has_error else theme.TAG_BG
        tag_text_color = theme.ERROR_TEXT if has_error else theme.TAG_TEXT
        subtitle_text = item.error if item.error else item.justification

        return theme.ios_card(
            ft.Column(
                spacing=8,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.START,
                        controls=[
                            ft.Text(
                                item.file_name,
                                size=15 if self._is_compact_mode else 16,
                                weight=ft.FontWeight.W_600,
                                color=theme.TEXT_PRIMARY,
                                expand=True,
                            ),
                            ft.Container(
                                bgcolor=tag_bg,
                                border_radius=theme.RADIUS_TAG,
                                padding=ft.Padding.symmetric(horizontal=10, vertical=6),
                                content=ft.Text(
                                    item.category,
                                    color=tag_text_color,
                                    size=11,
                                    weight=ft.FontWeight.W_600,
                                ),
                            ),
                        ],
                    ),
                    ft.Text(
                        item.destination,
                        size=12,
                        color=theme.TEXT_SECONDARY,
                    ),
                    ft.Text(
                        subtitle_text,
                        size=12 if self._is_compact_mode else 13,
                        color=theme.TEXT_SECONDARY,
                    ),
                ],
            ),
            padding=12 if self._is_compact_mode else 14,
        )

    def _render_results_cards(self) -> None:
        self.results_column.controls = [self._result_card(item) for item in self._latest_results]

    def _finish_loading_with_message(self, message: str) -> None:
        self.progress_ring.visible = False
        self.progress_text.visible = False
        self.empty_state_text.value = message
        self.empty_state_card.visible = True
        self.results_container.visible = False
        self.page.update()

    def set_compact_mode(self, is_compact: bool) -> None:
        self._is_compact_mode = is_compact
        self.control.padding = 14 if is_compact else 24
        self.title_text.size = 20 if is_compact else 30
        self.subtitle_text.size = 12 if is_compact else 14
        self.progress_text.size = 12 if is_compact else 14
        self.empty_state_text.size = 12 if is_compact else 14
        self.analyze_button.style = theme.ios_primary_button_style()
        if self._latest_results:
            self._render_results_cards()

    def _show_snackbar(self, message: str) -> None:
        snackbar = ft.SnackBar(
            content=ft.Text(message, color=ft.Colors.WHITE),
            bgcolor=theme.TEXT_PRIMARY,
            behavior=ft.SnackBarBehavior.FLOATING,
        )
        self.page.overlay.append(snackbar)
        snackbar.open = True
        self.page.update()
