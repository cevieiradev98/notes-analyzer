from __future__ import annotations

import flet as ft

BG_PAGE = "#F2F2F7"
BG_CARD = "#FFFFFF"
NAV_BG = "#F7F7FA"
ACCENT = "#007AFF"
TEXT_PRIMARY = "#000000"
TEXT_SECONDARY = "#8E8E93"
BORDER_COLOR = "#C6C6C8"
INPUT_BG = "#E5E5EA"
TAG_BG = "#DCEBFF"
TAG_TEXT = "#0056B3"
ERROR_BG = "#FFE8E6"
ERROR_TEXT = "#D12D1F"
HEATMAP_EMPTY = "#EBEDF0"
HEATMAP_L1 = "#9BE9A8"
HEATMAP_L2 = "#40C463"
HEATMAP_L3 = "#30A14E"
HEATMAP_L4 = "#216E39"
TIMELINE_LINE = "#D1D5DA"
TIMELINE_DOT = ACCENT

RADIUS_CARD = 16
RADIUS_BUTTON = 12
RADIUS_INPUT = 12
RADIUS_TAG = 10


def soft_shadow() -> list[ft.BoxShadow]:
    return [
        ft.BoxShadow(
            spread_radius=0,
            blur_radius=14,
            color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK),
            offset=ft.Offset(0, 3),
        )
    ]


def ios_title(value: str, *, compact: bool = False) -> ft.Text:
    return ft.Text(
        value,
        size=22 if compact else 30,
        weight=ft.FontWeight.BOLD,
        color=TEXT_PRIMARY,
    )


def ios_subtitle(value: str, *, compact: bool = False) -> ft.Text:
    return ft.Text(
        value,
        size=12 if compact else 14,
        color=TEXT_SECONDARY,
    )


def ios_primary_button_style() -> ft.ButtonStyle:
    return ft.ButtonStyle(
        bgcolor=ACCENT,
        color=ft.Colors.WHITE,
        shape=ft.RoundedRectangleBorder(radius=RADIUS_BUTTON),
        padding=ft.Padding.symmetric(horizontal=20, vertical=14),
    )


def ios_secondary_button_style() -> ft.ButtonStyle:
    return ft.ButtonStyle(
        color=ACCENT,
        shape=ft.RoundedRectangleBorder(radius=RADIUS_BUTTON),
        padding=ft.Padding.symmetric(horizontal=12, vertical=10),
    )


def ios_input_container(content: ft.Control) -> ft.Container:
    return ft.Container(
        bgcolor=INPUT_BG,
        border_radius=RADIUS_INPUT,
        padding=ft.Padding.symmetric(horizontal=12, vertical=4),
        content=content,
    )


def ios_card(content: ft.Control, *, padding: int = 16) -> ft.Container:
    return ft.Container(
        bgcolor=BG_CARD,
        border_radius=RADIUS_CARD,
        padding=padding,
        shadow=soft_shadow(),
        content=content,
    )


def ios_section_title(value: str) -> ft.Text:
    return ft.Text(value, size=13, weight=ft.FontWeight.W_600, color=TEXT_SECONDARY)


def heatmap_color(count: int) -> str:
    if count <= 0:
        return HEATMAP_EMPTY
    if count == 1:
        return HEATMAP_L1
    if count <= 3:
        return HEATMAP_L2
    if count <= 5:
        return HEATMAP_L3
    return HEATMAP_L4
