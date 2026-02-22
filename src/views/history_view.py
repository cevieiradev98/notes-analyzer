from __future__ import annotations

import calendar
from collections import defaultdict
from datetime import date, datetime

import flet as ft

from src.models.schemas import NoteFile
from src.services.ai_service import AIService
from src.services import history_service
from src.utils.config_manager import ConfigManager
from src.views import theme


_PT_MONTHS = [
    "janeiro",
    "fevereiro",
    "março",
    "abril",
    "maio",
    "junho",
    "julho",
    "agosto",
    "setembro",
    "outubro",
    "novembro",
    "dezembro",
]


class HistoryView:
    def __init__(self, page: ft.Page, config_manager: ConfigManager) -> None:
        self.page = page
        self.config_manager = config_manager
        today = date.today()
        self._current_year = today.year
        self._current_month = today.month
        self._is_compact_mode = False
        self._counts_by_day: dict[int, int] = {}
        self._entries: list[dict[str, str]] = []
        self._selected_entry_ids: set[str] = set()
        self._expanded_dates: set[str] = set()

        self.title_text = theme.ios_title("Histórico")
        self.subtitle_text = theme.ios_subtitle(
            "Acompanhe o volume diário de notas processadas.",
        )

        self.month_label = ft.Text(weight=ft.FontWeight.W_600, color=theme.TEXT_PRIMARY)
        self.map_card = theme.ios_card(ft.Container())
        self.timeline_card = theme.ios_card(ft.Container())

        self.control = ft.Container(
            expand=True,
            bgcolor=theme.BG_PAGE,
            padding=24,
            content=ft.Column(
                expand=True,
                scroll=ft.ScrollMode.AUTO,
                spacing=16,
                controls=[
                    ft.Column(spacing=4, controls=[self.title_text, self.subtitle_text]),
                    self.map_card,
                    self.timeline_card,
                ],
            ),
        )

    async def load(self) -> None:
        await history_service.init_db()
        self._counts_by_day = await history_service.get_month_counts(
            self._current_year,
            self._current_month,
        )
        self._entries = await history_service.get_month_entries(
            self._current_year,
            self._current_month,
        )
        valid_entry_ids = {item["id"] for item in self._entries}
        self._selected_entry_ids = {
            entry_id for entry_id in self._selected_entry_ids if entry_id in valid_entry_ids
        }
        self._build_content()

    def set_compact_mode(self, is_compact: bool) -> None:
        self._is_compact_mode = is_compact
        self.control.padding = 14 if is_compact else 24
        self.title_text.size = 20 if is_compact else 30
        self.subtitle_text.size = 12 if is_compact else 14

    def _build_content(self) -> None:
        self._update_month_label()
        self.map_card.content = self._build_heatmap()
        self.timeline_card.content = self._build_timeline()

    def _update_month_label(self) -> None:
        self.month_label.value = f"{_PT_MONTHS[self._current_month - 1].capitalize()} de {self._current_year}"

    async def _go_prev_month(self, _: ft.ControlEvent) -> None:
        if self._current_month == 1:
            self._current_month = 12
            self._current_year -= 1
        else:
            self._current_month -= 1
        await self.load()
        self.page.update()

    async def _go_next_month(self, _: ft.ControlEvent) -> None:
        if self._current_month == 12:
            self._current_month = 1
            self._current_year += 1
        else:
            self._current_month += 1
        await self.load()
        self.page.update()

    def _build_heatmap(self) -> ft.Control:
        first_weekday, total_days = calendar.monthrange(self._current_year, self._current_month)
        offset = (first_weekday + 1) % 7

        cells: list[ft.Control] = []
        for _ in range(offset):
            cells.append(
                ft.Container(
                    width=16,
                    height=16,
                    border_radius=3,
                    bgcolor=ft.Colors.TRANSPARENT,
                )
            )

        for day in range(1, total_days + 1):
            count = self._counts_by_day.get(day, 0)
            cells.append(
                ft.Container(
                    width=16,
                    height=16,
                    border_radius=3,
                    bgcolor=theme.heatmap_color(count),
                    tooltip=f"Dia {day}: {count} nota(s)",
                )
            )

        while len(cells) % 7 != 0:
            cells.append(
                ft.Container(
                    width=16,
                    height=16,
                    border_radius=3,
                    bgcolor=ft.Colors.TRANSPARENT,
                )
            )

        rows: list[ft.Control] = []
        for index in range(0, len(cells), 7):
            rows.append(ft.Row(spacing=4, controls=cells[index:index + 7]))

        total_notes_month = sum(self._counts_by_day.values())

        return ft.Column(
            spacing=12,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        theme.ios_section_title("MAPA DE CALOR"),
                        ft.Row(
                            spacing=4,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.IconButton(
                                    icon=ft.Icons.CHEVRON_LEFT,
                                    icon_size=18,
                                    on_click=self._go_prev_month,
                                ),
                                self.month_label,
                                ft.IconButton(
                                    icon=ft.Icons.CHEVRON_RIGHT,
                                    icon_size=18,
                                    on_click=self._go_next_month,
                                ),
                            ],
                        ),
                    ],
                ),
                ft.Column(spacing=4, controls=rows),
                ft.Row(
                    alignment=ft.MainAxisAlignment.END,
                    spacing=8,
                    controls=[
                        ft.Text("Menos", size=11, color=theme.TEXT_SECONDARY),
                        ft.Container(width=14, height=14, border_radius=3, bgcolor=theme.HEATMAP_EMPTY),
                        ft.Container(width=14, height=14, border_radius=3, bgcolor=theme.HEATMAP_L1),
                        ft.Container(width=14, height=14, border_radius=3, bgcolor=theme.HEATMAP_L2),
                        ft.Container(width=14, height=14, border_radius=3, bgcolor=theme.HEATMAP_L3),
                        ft.Container(width=14, height=14, border_radius=3, bgcolor=theme.HEATMAP_L4),
                        ft.Text("Mais", size=11, color=theme.TEXT_SECONDARY),
                    ],
                ),
                ft.Text(
                    f"{total_notes_month} nota(s) processada(s) no mês.",
                    size=12,
                    color=theme.TEXT_SECONDARY,
                ),
            ],
        )

    def _build_timeline(self) -> ft.Control:
        if not self._entries:
            return ft.Column(
                spacing=10,
                controls=[
                    self._timeline_header(),
                    ft.Text(
                        "Nenhuma nota processada neste mês.",
                        size=13,
                        color=theme.TEXT_SECONDARY,
                    ),
                ],
            )

        grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
        for item in self._entries:
            grouped[item["data"]].append(item)

        sorted_dates = sorted(grouped.keys(), reverse=True)

        rows: list[ft.Control] = [self._timeline_header()]
        for index, data_str in enumerate(sorted_dates):
            daily_items = grouped[data_str]
            summary_text = self._build_summary(daily_items)
            formatted_date = self._format_date_label(data_str)

            top_line_color = theme.BG_CARD if index == 0 else theme.TIMELINE_LINE
            bottom_line_color = theme.BG_CARD if index == len(sorted_dates) - 1 else theme.TIMELINE_LINE

            left_column = ft.Column(
                spacing=0,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(width=2, height=12, bgcolor=top_line_color),
                    ft.Container(width=12, height=12, border_radius=6, bgcolor=theme.TIMELINE_DOT),
                    ft.Container(width=2, height=72, bgcolor=bottom_line_color),
                ],
            )

            details_controls = [
                self._timeline_item_tile(item)
                for item in daily_items
            ]

            summary_button = ft.IconButton(
                icon=ft.Icons.AUTO_AWESOME,
                icon_size=18,
                tooltip="Resumo do dia",
                on_click=lambda event, date_value=data_str, day_items=list(daily_items): self.page.run_task(
                    self._handle_day_summary,
                    event,
                    date_value,
                    day_items,
                ),
            )

            tile_title = ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Text(
                        f"{formatted_date}: {summary_text}",
                        size=13 if self._is_compact_mode else 14,
                        color=theme.TEXT_PRIMARY,
                        weight=ft.FontWeight.W_500,
                    ),
                    summary_button,
                ],
            )

            expansion = ft.ExpansionTile(
                title=tile_title,
                controls=details_controls,
                text_color=theme.TEXT_PRIMARY,
                icon_color=theme.TEXT_SECONDARY,
                collapsed_text_color=theme.TEXT_PRIMARY,
                collapsed_icon_color=theme.TEXT_SECONDARY,
                tile_padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                expanded=data_str in self._expanded_dates,
                on_change=lambda event, date_value=data_str: self._handle_day_expansion_change(event, date_value),
                maintain_state=True,
            )

            rows.append(
                ft.Row(
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                    controls=[
                        ft.Container(width=24, content=left_column),
                        ft.Container(expand=True, content=expansion),
                    ],
                )
            )

        return ft.Column(spacing=6, controls=rows)

    def _timeline_header(self) -> ft.Control:
        selected_count = len(self._selected_entry_ids)
        total_count = len(self._entries)
        return ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                theme.ios_section_title("LINHA DO TEMPO"),
                ft.Row(
                    spacing=8,
                    controls=[
                        ft.TextButton(
                            f"Excluir selecionadas ({selected_count})",
                            icon=ft.Icons.DELETE_OUTLINE,
                            style=theme.ios_secondary_button_style(),
                            disabled=selected_count == 0,
                            on_click=self._confirm_delete_selected_entries,
                        ),
                        ft.TextButton(
                            "Selecionar todas",
                            icon=ft.Icons.SELECT_ALL,
                            style=theme.ios_secondary_button_style(),
                            disabled=total_count == 0 or selected_count == total_count,
                            on_click=self._select_all_entries,
                        ),
                        ft.TextButton(
                            "Limpar seleção",
                            icon=ft.Icons.DESELECT,
                            style=theme.ios_secondary_button_style(),
                            disabled=selected_count == 0,
                            on_click=self._clear_selection,
                        ),
                        ft.TextButton(
                            "Limpar histórico",
                            icon=ft.Icons.DELETE_SWEEP_OUTLINED,
                            style=theme.ios_secondary_button_style(),
                            on_click=self._confirm_clear_history,
                        ),
                    ],
                ),
            ],
        )

    def _timeline_item_tile(self, item: dict[str, str]) -> ft.Control:
        async def handle_delete(_: ft.ControlEvent) -> None:
            self._confirm_delete_entry(item)

        category_tag = ft.Container(
            bgcolor=theme.TAG_BG,
            border_radius=theme.RADIUS_TAG,
            padding=ft.Padding.symmetric(horizontal=8, vertical=4),
            content=ft.Text(
                item["categoria"],
                size=10,
                color=theme.TAG_TEXT,
                weight=ft.FontWeight.W_600,
            ),
        )

        item_id = item["id"]

        def handle_selection_change(event: ft.ControlEvent) -> None:
            is_selected = bool(event.control.value)
            if is_selected:
                self._selected_entry_ids.add(item_id)
            else:
                self._selected_entry_ids.discard(item_id)
            self._build_content()
            self.page.update()

        return ft.ListTile(
            dense=True,
            leading=ft.Checkbox(
                value=item_id in self._selected_entry_ids,
                on_change=handle_selection_change,
            ),
            title=ft.Text(item["titulo"], size=12, color=theme.TEXT_PRIMARY),
            subtitle=ft.Text(
                f"{item['hora']} · {self._build_note_preview(item)}",
                size=11,
                color=theme.TEXT_SECONDARY,
            ),
            trailing=ft.Row(
                spacing=6,
                tight=True,
                controls=[
                    category_tag,
                    ft.IconButton(
                        icon=ft.Icons.DELETE_OUTLINE,
                        icon_color=theme.ERROR_TEXT,
                        icon_size=18,
                        tooltip="Apagar nota",
                        on_click=handle_delete,
                    ),
                ],
            ),
            on_click=lambda _: self._open_note_dialog(item),
        )

    def _confirm_delete_entry(self, item: dict[str, str]) -> None:
        async def handle_confirm(_: ft.ControlEvent) -> None:
            deleted_item = dict(item)
            await history_service.delete_entry(int(item["id"]))
            dialog.open = False
            await self.load()
            self.page.update()

            def handle_undo_action(_: ft.ControlEvent) -> None:
                self.page.run_task(self._undo_deleted_entry, deleted_item)

            self._show_snackbar(
                "Nota removida do histórico.",
                action_label="Desfazer",
                on_action=handle_undo_action,
            )

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Apagar nota"),
            content=ft.Text("Deseja realmente apagar esta nota do histórico?"),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: self._close_dialog(dialog)),
                ft.TextButton(
                    "Apagar",
                    style=ft.ButtonStyle(color=theme.ERROR_TEXT),
                    on_click=handle_confirm,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def _confirm_delete_selected_entries(self, _: ft.ControlEvent) -> None:
        selected_ids = list(self._selected_entry_ids)
        if not selected_ids:
            self._show_snackbar("Selecione ao menos uma nota para excluir.")
            return

        async def handle_confirm(_: ft.ControlEvent) -> None:
            for entry_id in selected_ids:
                await history_service.delete_entry(int(entry_id))

            self._selected_entry_ids.clear()
            dialog.open = False
            await self.load()
            self.page.update()
            self._show_snackbar(f"{len(selected_ids)} nota(s) removida(s) do histórico.")

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Apagar notas selecionadas"),
            content=ft.Text(
                f"Deseja realmente apagar {len(selected_ids)} nota(s) selecionada(s)?"
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: self._close_dialog(dialog)),
                ft.TextButton(
                    "Apagar",
                    style=ft.ButtonStyle(color=theme.ERROR_TEXT),
                    on_click=handle_confirm,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def _select_all_entries(self, _: ft.ControlEvent) -> None:
        self._selected_entry_ids = {item["id"] for item in self._entries}
        self._build_content()
        self.page.update()

    def _clear_selection(self, _: ft.ControlEvent) -> None:
        self._selected_entry_ids.clear()
        self._build_content()
        self.page.update()

    def _handle_day_expansion_change(self, event: ft.ControlEvent, date_str: str) -> None:
        is_expanded = str(getattr(event, "data", "")).lower() == "true"
        if is_expanded:
            self._expanded_dates.add(date_str)
        else:
            self._expanded_dates.discard(date_str)

    def _confirm_clear_history(self, _: ft.ControlEvent) -> None:
        async def handle_clear(_: ft.ControlEvent) -> None:
            await history_service.clear_history()
            dialog.open = False
            await self.load()
            self.page.update()
            self._show_snackbar("Histórico limpo com sucesso.")

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Limpar histórico"),
            content=ft.Text("Essa ação remove todas as notas salvas no histórico. Continuar?"),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: self._close_dialog(dialog)),
                ft.TextButton(
                    "Limpar tudo",
                    style=ft.ButtonStyle(color=theme.ERROR_TEXT),
                    on_click=handle_clear,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def _build_note_preview(self, item: dict[str, str]) -> str:
        preview = item.get("resumo", "").strip()
        if preview:
            return preview

        content = " ".join(item.get("conteudo", "").split())
        if content:
            return f"{content[:80].rstrip()}..." if len(content) > 80 else content

        return f"Fonte: {item['fonte']}"

    def _open_note_dialog(self, item: dict[str, str]) -> None:
        content_text = item.get("conteudo", "").strip()
        note_text = content_text if content_text else "Conteúdo da nota não disponível para este registro antigo."

        async def handle_reprocess(event: ft.ControlEvent) -> None:
            await self._reprocess_note(event, item, dialog)

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(item["titulo"], size=16, color=theme.TEXT_PRIMARY, weight=ft.FontWeight.W_600),
            content=ft.Container(
                width=660,
                height=340,
                padding=12,
                bgcolor=theme.INPUT_BG,
                border_radius=theme.RADIUS_INPUT,
                content=ft.Column(
                    spacing=10,
                    controls=[
                        ft.Text(
                            f"{item['data']} · {item['hora']} · {item['fonte']}",
                            size=12,
                            color=theme.TEXT_SECONDARY,
                        ),
                        ft.Text(
                            note_text,
                            size=13,
                            color=theme.TEXT_PRIMARY,
                            selectable=True,
                        ),
                    ],
                    scroll=ft.ScrollMode.AUTO,
                ),
            ),
            actions=[
                ft.TextButton("Fechar", on_click=lambda _: self._close_dialog(dialog)),
                ft.FilledButton(
                    "Reprocessar nota",
                    icon=ft.Icons.AUTO_AWESOME,
                    style=theme.ios_primary_button_style(),
                    on_click=handle_reprocess,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def _close_dialog(self, dialog: ft.AlertDialog) -> None:
        dialog.open = False
        self.page.update()

    async def _reprocess_note(
        self,
        event: ft.ControlEvent,
        item: dict[str, str],
        dialog: ft.AlertDialog,
    ) -> None:
        note_content = item.get("conteudo", "").strip()
        if not note_content:
            self._show_snackbar("Não há conteúdo salvo para reprocessar esta nota.")
            return

        config = await self.config_manager.load()
        if not config.api_key:
            self._show_snackbar("API Key não configurada. Vá em Configurações.")
            return

        event.control.disabled = True
        self.page.update()

        ai_service = AIService(config.api_key)
        try:
            result = await ai_service.analyze_note(
                note=NoteFile(
                    file_name=item["titulo"],
                    file_path=f"historico://{item['id']}",
                    modified_at=datetime.now(),
                    content=note_content,
                ),
                base_prompt=config.base_prompt,
                categories=config.categories,
            )
        finally:
            await ai_service.close()

        if result.error:
            event.control.disabled = False
            self.page.update()
            self._show_snackbar(result.error)
            return

        await history_service.update_entry_analysis(
            entry_id=int(item["id"]),
            category=result.category,
            destination=result.destination,
            justification=result.justification,
        )
        await self.load()

        dialog.open = False
        self.page.update()
        self._show_snackbar("Nota reprocessada com sucesso.")

    async def _undo_deleted_entry(self, deleted_item: dict[str, str]) -> None:
        await history_service.restore_entry(deleted_item)
        await self.load()
        self.page.update()
        self._show_snackbar("Nota restaurada no histórico.")

    async def _handle_day_summary(
        self,
        event: ft.ControlEvent,
        date_str: str,
        daily_items: list[dict[str, str]],
    ) -> None:
        event.control.disabled = True
        self.page.update()

        try:
            summary_text = await self._get_or_generate_day_summary(
                date_str=date_str,
                daily_items=daily_items,
                force_refresh=False,
            )
            if not summary_text:
                return
            self._open_summary_dialog(
                date_str=date_str,
                summary_text=summary_text,
                daily_items=daily_items,
            )
        finally:
            event.control.disabled = False
            self.page.update()

    async def _get_or_generate_day_summary(
        self,
        date_str: str,
        daily_items: list[dict[str, str]],
        force_refresh: bool,
    ) -> str | None:
        note_contents = [
            str(item.get("conteudo", "") or "").strip()
            for item in daily_items
            if str(item.get("conteudo", "") or "").strip()
        ]
        if not note_contents:
            self._show_snackbar("Nenhuma nota com conteúdo para resumir neste dia.")
            return None

        if not force_refresh:
            cached_summary = await history_service.get_daily_summary(date_str)
            if cached_summary:
                return cached_summary

        config = await self.config_manager.load()
        if not config.api_key:
            self._show_snackbar("API Key não configurada. Vá em Configurações.")
            return None

        combined_text = "\n\n---\n\n".join(note_contents)
        ai_service = AIService(config.api_key)
        try:
            summary = await ai_service.generate_summary(combined_text)
        except Exception as error:
            self._show_snackbar(str(error) or "Falha ao gerar resumo do dia.")
            return None
        finally:
            await ai_service.close()

        await history_service.save_daily_summary(date_str, summary)
        return summary

    def _open_summary_dialog(
        self,
        date_str: str,
        summary_text: str,
        daily_items: list[dict[str, str]],
    ) -> None:
        summary_value = ft.Text(
            summary_text,
            size=13,
            color=theme.TEXT_PRIMARY,
            selectable=True,
        )
        date_label = self._format_date_label(date_str)

        async def handle_regenerate(event: ft.ControlEvent) -> None:
            event.control.disabled = True
            self.page.update()

            try:
                refreshed_summary = await self._get_or_generate_day_summary(
                    date_str=date_str,
                    daily_items=daily_items,
                    force_refresh=True,
                )
                if not refreshed_summary:
                    return

                summary_value.value = refreshed_summary
                self.page.update()
                self._show_snackbar("Resumo do dia atualizado.")
            finally:
                event.control.disabled = False
                self.page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(
                f"Resumo do dia — {date_label}",
                size=16,
                color=theme.TEXT_PRIMARY,
                weight=ft.FontWeight.W_600,
            ),
            content=ft.Container(
                width=680,
                height=360,
                padding=12,
                bgcolor=theme.INPUT_BG,
                border_radius=theme.RADIUS_INPUT,
                content=ft.Column(
                    spacing=10,
                    scroll=ft.ScrollMode.AUTO,
                    controls=[summary_value],
                ),
            ),
            actions=[
                ft.TextButton("Fechar", on_click=lambda _: self._close_dialog(dialog)),
                ft.FilledButton(
                    "Regenerar",
                    icon=ft.Icons.REFRESH,
                    style=theme.ios_primary_button_style(),
                    on_click=lambda event: self.page.run_task(handle_regenerate, event),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def _build_summary(self, daily_items: list[dict[str, str]]) -> str:
        category_counts: dict[str, int] = defaultdict(int)
        for item in daily_items:
            category_counts[item["categoria"]] += 1

        ordered_categories = sorted(category_counts.items(), key=lambda entry: entry[1], reverse=True)
        category_parts = [f"{count} {name}" for name, count in ordered_categories[:3]]
        category_text = ", ".join(category_parts) if category_parts else "sem categorias"

        return f"{len(daily_items)} notas processadas ({category_text})"

    def _format_date_label(self, date_str: str) -> str:
        parsed = datetime.strptime(date_str, "%Y-%m-%d")
        return f"{parsed.day} de {_PT_MONTHS[parsed.month - 1][:3]}"

    def _show_snackbar(
        self,
        message: str,
        action_label: str | None = None,
        on_action: ft.OptionalControlEventCallable = None,
    ) -> None:
        snackbar = ft.SnackBar(
            content=ft.Text(message, color=ft.Colors.WHITE),
            bgcolor=theme.TEXT_PRIMARY,
            behavior=ft.SnackBarBehavior.FLOATING,
            duration=2000,
            action=action_label,
            on_action=on_action,
        )
        self.page.overlay.append(snackbar)
        snackbar.open = True
        self.page.update()
