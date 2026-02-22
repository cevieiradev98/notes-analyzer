from __future__ import annotations

from pathlib import Path

import flet as ft

from src.services import history_service
from src.utils.config_manager import ConfigManager
from src.views.dashboard_view import DashboardView
from src.views.history_view import HistoryView
from src.views.settings_view import SettingsView
from src.views import theme


async def main(page: ft.Page) -> None:
    project_root = Path(__file__).resolve().parent.parent
    root_assets_path = project_root / "assets"
    src_assets_path = Path(__file__).resolve().parent / "assets"
    icon_path = root_assets_path / "icon.png"
    if not icon_path.exists():
        icon_path = src_assets_path / "icon.png"

    page.title = "Notes Analyzer"
    if icon_path.exists():
        page.window.icon = str(icon_path)
    page.window.width = 1100
    page.window.height = 760
    page.window.min_width = 460
    page.window.min_height = 560
    page.padding = 0
    page.bgcolor = theme.BG_PAGE
    page.theme = ft.Theme(
        color_scheme_seed=theme.ACCENT,
        font_family="Helvetica Neue",
    )
    await history_service.init_db()

    config_manager = ConfigManager(page)
    dashboard_view = DashboardView(page=page, config_manager=config_manager)
    history_view = HistoryView(page=page, config_manager=config_manager)
    settings_view = SettingsView(page=page, config_manager=config_manager)

    content_area = ft.Container(
        expand=True,
        bgcolor=theme.BG_PAGE,
        content=dashboard_view.control,
    )

    async def on_nav_change(event: ft.ControlEvent) -> None:
        if event.control.selected_index == 0:
            content_area.content = dashboard_view.control
        elif event.control.selected_index == 1:
            await history_view.load()
            content_area.content = history_view.control
        else:
            await settings_view.load()
            content_area.content = settings_view.control
        page.update()

    def apply_compact_mode() -> None:
        is_compact = True

        navigation.label_type = (
            ft.NavigationRailLabelType.NONE
            if is_compact
            else ft.NavigationRailLabelType.ALL
        )
        navigation.min_width = 64 if is_compact else 100
        navigation.min_extended_width = 64 if is_compact else 140

        dashboard_view.set_compact_mode(is_compact)
        history_view.set_compact_mode(is_compact)
        settings_view.set_compact_mode(is_compact)
        dashboard_view.on_host_resized()

    navigation = ft.NavigationRail(
        selected_index=0,
        bgcolor=theme.NAV_BG,
        indicator_color=ft.Colors.with_opacity(0.18, theme.ACCENT),
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=100,
        min_extended_width=140,
        leading=ft.Container(
            padding=ft.Padding.only(top=14, bottom=8),
            content=ft.Icon(ft.Icons.AUTO_AWESOME, color=theme.ACCENT, size=22),
        ),
        group_alignment=-0.9,
        trailing=ft.Container(expand=True),
        destinations=[
            ft.NavigationRailDestination(
                icon=ft.Icon(ft.Icons.HOME_OUTLINED, color=theme.TEXT_SECONDARY),
                selected_icon=ft.Icon(ft.Icons.HOME, color=theme.ACCENT),
                label="Dashboard",
            ),
            ft.NavigationRailDestination(
                icon=ft.Icon(ft.Icons.CALENDAR_MONTH_OUTLINED, color=theme.TEXT_SECONDARY),
                selected_icon=ft.Icon(ft.Icons.CALENDAR_MONTH, color=theme.ACCENT),
                label="Histórico",
            ),
            ft.NavigationRailDestination(
                icon=ft.Icon(ft.Icons.SETTINGS_OUTLINED, color=theme.TEXT_SECONDARY),
                selected_icon=ft.Icon(ft.Icons.SETTINGS, color=theme.ACCENT),
                label="Configurações",
            ),
        ],
        on_change=on_nav_change,
    )

    page.add(
        ft.Row(
            expand=True,
            controls=[
                ft.Container(
                    bgcolor=theme.NAV_BG,
                    padding=ft.Padding.symmetric(horizontal=8, vertical=10),
                    content=navigation,
                ),
                content_area,
            ],
        )
    )

    def on_page_resized(_: ft.ControlEvent) -> None:
        apply_compact_mode()
        page.update()

    page.on_resized = on_page_resized
    
    apply_compact_mode()
    page.update()


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    root_assets_path = project_root / "assets"
    src_assets_path = Path(__file__).resolve().parent / "assets"
    assets_path = root_assets_path if root_assets_path.exists() else src_assets_path
    ft.run(main, name="Notes Analyzer", assets_dir=str(assets_path))
