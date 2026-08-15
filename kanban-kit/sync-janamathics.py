# -*- coding: utf-8 -*-
"""Template-Features nach brainstorm/ (Janamathics) spiegeln – JSON/Flipcharts bleiben erhalten."""
from __future__ import annotations

import json
import re
from pathlib import Path

KIT_ROOT = Path(__file__).resolve().parent
REPO_ROOT = KIT_ROOT.parent
TEMPLATE = KIT_ROOT / "template"
BRAINSTORM = REPO_ROOT / "brainstorm"

MAPPING = {
    "__BOARD_TITLE__": "Janamathics \u2013 Kanban & Brainstorm",
    "__BOARD_SLUG__": "janamathics",
    "__BOARD_HTML__": "janamathics-kanban.html",
    "__BOARD_JSON__": "janamathics-kanban.json",
    "__FLIPCHART_JSON__": "janamathics-flipchart.json",
    "__BOARD_PORT__": "8765",
    "__BOARD_SOURCE__": "janamathics-kanban",
    "__BOARD_DIR__": "brainstorm",
    "__STORAGE_KEY__": "janamathics-kanban-v1",
    "__FILE_HANDLE_DB__": "janamathics-kanban-handles",
    "__FLIPCHART_LS_PREFIX__": "janamathics-flipchart-v1:",
}

# Dateien aus der Vorlage → Zielname in brainstorm/
TEMPLATE_COPY_MAP = {
    "board.html": "janamathics-kanban.html",
    "board.config.json": "board.config.json",
    "kanban_server.py": "kanban_server.py",
    "export_lib.py": "export_lib.py",
    "Kanban oeffnen.ps1": "Kanban oeffnen.ps1",
    "Kanban oeffnen.bat": "Kanban oeffnen.bat",
    ".gitignore": ".gitignore",
}

# Gemeinsame Libs nur aus kanban-kit/ (eine Quelle)
SHARED_LIB_FILES = (
    "theme_lib.js",
    "theme_lib.py",
    "theme_shared.css",
    "i18n_lib.js",
)

# Janamathics-Spalten (Reset / Seed) – „Umgesetzt“ mit Spiel-Hinweis
JANA_DEFAULT_COLUMNS = """    const DEFAULT_COLUMNS = [
      { id: "ist", title: "Umgesetzt", hint: "Was schon im Spiel steckt", color: "green" },
      { id: "brainstorm", title: "Brainstorm", hint: "Freie Ideen", color: "yellow" },
      { id: "backlog", title: "Backlog", hint: "Irgendwann / geparkt", color: "orange" },
      { id: "next", title: "Als Nächstes", hint: "Konkrete Prioritäten", color: "blue" },
    ];"""


def apply_placeholders(text: str) -> str:
    for key, value in MAPPING.items():
        text = text.replace(key, value)
    return text


def extract_const_block(html: str, name: str) -> str | None:
    m = re.search(rf"(    const {name} = \[.*?\];)", html, flags=re.S)
    return m.group(1) if m else None


def patch_janamathics_defaults(html: str, *, columns_block: str | None, seed_block: str | None) -> str:
    """Spalten/Seed von Janamathics behalten, falls vorhanden."""
    cols = columns_block or JANA_DEFAULT_COLUMNS
    html, n = re.subn(r"    const DEFAULT_COLUMNS = \[.*?\];", cols, html, count=1, flags=re.S)
    if n != 1:
        raise SystemExit(f"DEFAULT_COLUMNS patch fehlgeschlagen (n={n})")
    if seed_block:
        html, n = re.subn(r"    const SEED_CARDS = \[.*?\];", seed_block, html, count=1, flags=re.S)
        if n != 1:
            raise SystemExit(f"SEED_CARDS patch fehlgeschlagen (n={n})")
    return html


def main() -> None:
    if not TEMPLATE.is_dir():
        raise SystemExit(f"Vorlage fehlt: {TEMPLATE}")
    BRAINSTORM.mkdir(parents=True, exist_ok=True)
    (BRAINSTORM / "flipcharts").mkdir(exist_ok=True)
    (BRAINSTORM / "attachments").mkdir(exist_ok=True)
    keep = BRAINSTORM / "attachments" / ".gitkeep"
    if not keep.exists():
        keep.write_text("", encoding="utf-8")

    old_html_path = BRAINSTORM / "janamathics-kanban.html"
    old_columns = old_seed = None
    if old_html_path.exists():
        old = old_html_path.read_text(encoding="utf-8")
        old_columns = extract_const_block(old, "DEFAULT_COLUMNS")
        old_seed = extract_const_block(old, "SEED_CARDS")

    for src_name, dest_name in TEMPLATE_COPY_MAP.items():
        src = TEMPLATE / src_name
        if not src.exists():
            raise SystemExit(f"Vorlage-Datei fehlt: {src}")
        dest = BRAINSTORM / dest_name
        text = apply_placeholders(src.read_text(encoding="utf-8"))
        if dest_name == "janamathics-kanban.html":
            text = patch_janamathics_defaults(text, columns_block=old_columns, seed_block=old_seed)
        dest.write_text(text, encoding="utf-8")
        print(f"geschrieben: {dest_name}")

    for fname in SHARED_LIB_FILES:
        src = KIT_ROOT / fname
        if not src.exists():
            raise SystemExit(f"Shared-Lib fehlt: {src}")
        dest = BRAINSTORM / fname
        dest.write_bytes(src.read_bytes())
        print(f"geschrieben (shared): {fname}")

    cfg_path = BRAINSTORM / "board.config.json"
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    cfg_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    html_text = (BRAINSTORM / "janamathics-kanban.html").read_text(encoding="utf-8")
    leftover = {k: html_text.count(k) for k in MAPPING if html_text.count(k)}
    if leftover:
        print("WARNUNG: Platzhalter übrig:", leftover)
    else:
        print("OK: keine Platzhalter mehr in janamathics-kanban.html")

    # Smoke: Feature-Marker
    markers = (
        "attachments",
        "dueDate",
        "dueFilter",
        "export-menu",
        "data-export",
        "btn-copy-card",
        "/api/export",
        "/api/attachments",
        "renderWeekView",
        "openStatsDialog",
        "milestone-bar",
        "field-recurrence",
        'data-export="odt"',
        "/api/versions",
        "import-csv",
        "openVersionsDialog",
    )
    missing = [m for m in markers if m not in html_text]
    if missing:
        print("WARNUNG: Feature-Marker fehlen:", missing)
    else:
        print("OK: Anhaenge, Due-Date, Multi-Export, Copy-Marker vorhanden")

    print(f"Janamathics synchronisiert -> {BRAINSTORM}")
    print("Hinweis: janamathics-kanban.json / Flipcharts wurden nicht ueberschrieben.")


if __name__ == "__main__":
    main()
