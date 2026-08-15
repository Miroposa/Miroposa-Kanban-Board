# -*- coding: utf-8 -*-
"""Gemeinsames Theme-Schema für Manager und Boards."""
from __future__ import annotations

from typing import Any

FONT_OPTIONS: list[dict[str, Any]] = [
    {"id": "segoe", "label": "Segoe UI", "excalidraw": 2},
    {"id": "verdana", "label": "Verdana", "excalidraw": 2},
    {"id": "trebuchet", "label": "Trebuchet", "excalidraw": 2},
    {"id": "georgia", "label": "Georgia", "excalidraw": 1},
    {"id": "garamond", "label": "Garamond", "excalidraw": 1},
    {"id": "comic", "label": "Handschrift", "excalidraw": 1},
    {"id": "consolas", "label": "Consolas", "excalidraw": 3},
    {"id": "arial", "label": "Arial", "excalidraw": 2},
]

_FONT_IDS = {f["id"] for f in FONT_OPTIONS}

DEFAULT_THEME: dict[str, Any] = {
    "bg": "#1f3d2f",
    "bg2": "#274c3a",
    "accent": "#e2a53a",
    "chalk": "#e8f0e6",
    "angle": 160,
    "spots": True,
    "font": "segoe",
    "lang": "auto",
}

THEME_PRESETS: list[dict[str, Any]] = [
    {
        "id": "forest",
        "label": "Waldgrün",
        "theme": {
            "bg": "#1f3d2f",
            "bg2": "#274c3a",
            "accent": "#e2a53a",
            "chalk": "#e8f0e6",
            "angle": 160,
            "spots": True,
        },
    },
    {
        "id": "ocean",
        "label": "Ozean",
        "theme": {
            "bg": "#1a3348",
            "bg2": "#234a63",
            "accent": "#5eb3c4",
            "chalk": "#e6f2f5",
            "angle": 150,
            "spots": True,
        },
    },
    {
        "id": "dusk",
        "label": "Abendrot",
        "theme": {
            "bg": "#3a2428",
            "bg2": "#5a3038",
            "accent": "#e08a5a",
            "chalk": "#f5ebe8",
            "angle": 145,
            "spots": True,
        },
    },
    {
        "id": "slate",
        "label": "Schiefer",
        "theme": {
            "bg": "#2a3038",
            "bg2": "#3a4450",
            "accent": "#c4a574",
            "chalk": "#eef1f4",
            "angle": 170,
            "spots": True,
        },
    },
    {
        "id": "sand",
        "label": "Sand",
        "theme": {
            "bg": "#3d3428",
            "bg2": "#564736",
            "accent": "#d4a84b",
            "chalk": "#f7f1e6",
            "angle": 155,
            "spots": True,
        },
    },
    {
        "id": "night",
        "label": "Nachtblau",
        "theme": {
            "bg": "#141c33",
            "bg2": "#1e2a4a",
            "accent": "#7b9cff",
            "chalk": "#e8ecf8",
            "angle": 165,
            "spots": True,
        },
    },
]


def _as_hex(value: Any, fallback: str) -> str:
    if not isinstance(value, str):
        return fallback
    s = value.strip()
    if len(s) == 4 and s.startswith("#"):
        s = "#" + "".join(ch * 2 for ch in s[1:])
    if len(s) == 7 and s.startswith("#"):
        try:
            int(s[1:], 16)
            return s.lower()
        except ValueError:
            return fallback
    return fallback


def normalize_theme(raw: Any) -> dict[str, Any]:
    data = raw if isinstance(raw, dict) else {}
    angle = data.get("angle", DEFAULT_THEME["angle"])
    try:
        angle_i = int(angle)
    except (TypeError, ValueError):
        angle_i = int(DEFAULT_THEME["angle"])
    angle_i = max(0, min(360, angle_i))
    spots = data.get("spots", DEFAULT_THEME["spots"])
    if isinstance(spots, str):
        spots = spots.strip().lower() in ("1", "true", "yes", "on")
    else:
        spots = bool(spots)
    font = data.get("font", DEFAULT_THEME["font"])
    if not isinstance(font, str) or font.strip() not in _FONT_IDS:
        font = str(DEFAULT_THEME["font"])
    else:
        font = font.strip()
    lang = data.get("lang", DEFAULT_THEME["lang"])
    if not isinstance(lang, str) or lang.strip().lower() not in ("auto", "de", "en"):
        lang = str(DEFAULT_THEME["lang"])
    else:
        lang = lang.strip().lower()
    return {
        "bg": _as_hex(data.get("bg"), str(DEFAULT_THEME["bg"])),
        "bg2": _as_hex(data.get("bg2"), str(DEFAULT_THEME["bg2"])),
        "accent": _as_hex(data.get("accent"), str(DEFAULT_THEME["accent"])),
        "chalk": _as_hex(data.get("chalk"), str(DEFAULT_THEME["chalk"])),
        "angle": angle_i,
        "spots": spots,
        "font": font,
        "lang": lang,
    }
