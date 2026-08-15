# -*- coding: utf-8 -*-
"""Neues Kanban/Brainstorm-Board aus der Vorlage anlegen (CLI + Bibliothek)."""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any

KIT_ROOT = Path(__file__).resolve().parent
TEMPLATE = KIT_ROOT / "template"
# Projektwurzel = Ordner über kanban-kit/ (Repo-Root)
REPO_ROOT = KIT_ROOT.parent

try:
    from theme_lib import normalize_theme as _normalize_theme
except Exception:  # noqa: BLE001
    def _normalize_theme(raw):  # type: ignore
        base = {
            "bg": "#1f3d2f",
            "bg2": "#274c3a",
            "accent": "#e2a53a",
            "chalk": "#e8f0e6",
            "angle": 160,
            "spots": True,
        }
        data = raw if isinstance(raw, dict) else {}
        out = dict(base)
        out.update({k: data[k] for k in base if k in data})
        return out


def default_boards_root() -> Path:
    """Erster Standard: Downloads-Ordner des Benutzers."""
    return (Path.home() / "Downloads").resolve()


BOARDS_ROOT = default_boards_root()

PLACEHOLDER_FILES = (
    "board.html",
    "board.config.json",
    "board.json",
    "flipchart.json",
    "Kanban oeffnen.ps1",
    "Kanban oeffnen.bat",
    "kanban_server.py",
    "export_lib.py",
)

# Gemeinsame Libs liegen nur in kanban-kit/ (nicht doppelt unter template/)
SHARED_LIB_FILES = (
    "theme_lib.js",
    "theme_shared.css",
    "theme_lib.py",
    "i18n_lib.js",
)

COPY_ONLY_FILES = ()  # reserved; all listed above are copied (placeholders applied when present)

STOP_SCRIPT_FILES = (
    "Kanban Server beenden.ps1",
    "Kanban Server beenden.bat",
)


class BoardError(Exception):
    """Benutzerfehler beim Anlegen eines Boards."""


def slugify(name: str) -> str:
    s = name.strip().lower()
    s = s.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "board"


def apply_placeholders(text: str, mapping: dict[str, str]) -> str:
    for key, value in mapping.items():
        text = text.replace(key, value)
    return text


def next_free_port(preferred: int, used: set[int]) -> int:
    port = preferred
    while port in used:
        port += 1
    return port


def collect_used_ports(search_roots: list[Path] | None = None) -> set[int]:
    used: set[int] = {8765}  # Janamathics
    roots = search_roots or [
        default_boards_root(),
        REPO_ROOT / "boards",
        REPO_ROOT / "brainstorm",
        KIT_ROOT,
    ]
    for root in roots:
        if not root.exists():
            continue
        for cfg in root.rglob("board.config.json"):
            try:
                data = json.loads(cfg.read_text(encoding="utf-8"))
                used.add(int(data["port"]))
            except Exception:
                continue
    return used


def create_board(
    name: str,
    *,
    slug: str = "",
    out: str | Path | None = None,
    port: int = 0,
    force: bool = False,
    theme: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Legt ein Board an und gibt Metadaten zurück."""
    if not TEMPLATE.is_dir():
        raise BoardError(f"Vorlage fehlt: {TEMPLATE}")

    display_name = name.strip()
    if not display_name:
        raise BoardError("Name darf nicht leer sein.")

    slug_val = (slug or "").strip() or slugify(display_name)
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", slug_val):
        raise BoardError(f"Ungültiger slug: {slug_val}")

    default_out = BOARDS_ROOT / slug_val
    out_dir = Path(out).expanduser().resolve() if out else default_out.resolve()

    if out_dir.exists() and any(out_dir.iterdir()) and not force:
        raise BoardError(
            f"Ziel existiert bereits: {out_dir}. Aktiviere „Überschreiben“, um fortzufahren."
        )

    used_ports = collect_used_ports()
    port_val = port if port else next_free_port(8766, used_ports)
    if not port and port_val in used_ports:
        port_val = next_free_port(8766, used_ports)
    if port and port_val in used_ports and not force:
        # Expliziter Port: Warnung nur wenn belegt – trotzdem erlauben, Nutzer wählt bewusst
        pass

    title = f"{display_name} \u2013 Kanban Board"
    board_html = f"{slug_val}-kanban.html"
    board_json = f"{slug_val}-kanban.json"
    flipchart_json = f"{slug_val}-flipchart.json"
    try:
        board_dir = str(out_dir.relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        board_dir = str(out_dir).replace("\\", "/")

    mapping = {
        "__BOARD_TITLE__": title,
        "__BOARD_SLUG__": slug_val,
        "__BOARD_HTML__": board_html,
        "__BOARD_JSON__": board_json,
        "__FLIPCHART_JSON__": flipchart_json,
        "__BOARD_PORT__": str(port_val),
        "__BOARD_SOURCE__": f"{slug_val}-kanban",
        "__BOARD_DIR__": board_dir,
        "__STORAGE_KEY__": f"{slug_val}-kanban-v1",
        "__FILE_HANDLE_DB__": f"{slug_val}-kanban-handles",
        "__FLIPCHART_LS_PREFIX__": f"{slug_val}-flipchart-v1:",
    }

    if out_dir.exists() and force:
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "flipcharts").mkdir(exist_ok=True)
    (out_dir / "flipcharts" / ".gitkeep").write_text("", encoding="utf-8")
    (out_dir / "attachments").mkdir(exist_ok=True)
    (out_dir / "attachments" / ".gitkeep").write_text("", encoding="utf-8")

    for fname in PLACEHOLDER_FILES:
        src = TEMPLATE / fname
        if not src.exists():
            raise BoardError(f"Vorlage-Datei fehlt: {src}")
        text = apply_placeholders(src.read_text(encoding="utf-8"), mapping)
        dest_name = board_html if fname == "board.html" else fname
        if fname == "board.json":
            dest_name = board_json
        elif fname == "flipchart.json":
            dest_name = flipchart_json
        (out_dir / dest_name).write_text(text, encoding="utf-8")

    for fname in SHARED_LIB_FILES:
        src = KIT_ROOT / fname
        if not src.exists():
            raise BoardError(f"Shared-Lib fehlt: {src}")
        shutil.copy2(src, out_dir / fname)

    for fname in STOP_SCRIPT_FILES:
        src = TEMPLATE / fname
        if src.exists():
            shutil.copy2(src, out_dir / fname)

    # Theme aus Manager (oder Default) in board.config.json schreiben
    cfg_path = out_dir / "board.config.json"
    try:
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        cfg["theme"] = _normalize_theme(theme)
        cfg_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass

    readme = f"""# {display_name} \u2013 Kanban Board

Lokales Board aus dem Kanban-Kit.

## Öffnen

- Doppelklick: `Kanban oeffnen.bat`
- URL: http://127.0.0.1:{port_val}/{board_html}

## Speicherung

- Board: `{board_json}`
- Flipchart: `{flipchart_json}`
- Karten-Flipcharts: `flipcharts/`

Nicht die HTML-Datei per Doppelklick öffnen (`file://`) – sonst landet der Stand nur im Browser.
"""
    (out_dir / "README.md").write_text(readme, encoding="utf-8")

    return {
        "ok": True,
        "name": display_name,
        "title": title,
        "slug": slug_val,
        "path": str(out_dir),
        "port": port_val,
        "boardHtml": board_html,
        "boardJson": board_json,
        "flipchartJson": flipchart_json,
        "url": f"http://127.0.0.1:{port_val}/{board_html}",
        "theme": _normalize_theme(theme),
    }


def mapping_from_config(out_dir: Path, cfg: dict[str, Any]) -> dict[str, str]:
    slug_val = str(cfg.get("slug") or "").strip()
    if not slug_val:
        raise BoardError("board.config.json: slug fehlt")
    try:
        board_dir = str(out_dir.relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        board_dir = str(cfg.get("boardDir") or out_dir).replace("\\", "/")
    return {
        "__BOARD_TITLE__": str(cfg.get("title") or f"{slug_val} – Kanban Board"),
        "__BOARD_SLUG__": slug_val,
        "__BOARD_HTML__": str(cfg.get("boardHtml") or f"{slug_val}-kanban.html"),
        "__BOARD_JSON__": str(cfg.get("boardJson") or f"{slug_val}-kanban.json"),
        "__FLIPCHART_JSON__": str(cfg.get("flipchartJson") or f"{slug_val}-flipchart.json"),
        "__BOARD_PORT__": str(int(cfg.get("port") or 8766)),
        "__BOARD_SOURCE__": str(cfg.get("source") or f"{slug_val}-kanban"),
        "__BOARD_DIR__": board_dir,
        "__STORAGE_KEY__": f"{slug_val}-kanban-v1",
        "__FILE_HANDLE_DB__": f"{slug_val}-kanban-handles",
        "__FLIPCHART_LS_PREFIX__": f"{slug_val}-flipchart-v1:",
    }


def update_board_at(path: str | Path) -> dict[str, Any]:
    """Programmdateien eines bestehenden Boards aus der Vorlage aktualisieren."""
    if not TEMPLATE.is_dir():
        raise BoardError(f"Vorlage fehlt: {TEMPLATE}")

    out_dir = Path(path).expanduser().resolve()
    cfg_path = out_dir / "board.config.json"
    if not cfg_path.exists():
        raise BoardError(f"Kein Board (board.config.json fehlt): {out_dir}")

    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    mapping = mapping_from_config(out_dir, cfg)
    board_html = mapping["__BOARD_HTML__"]
    preserved_theme = cfg.get("theme")
    preserved_icon = cfg.get("icon")

    (out_dir / "flipcharts").mkdir(exist_ok=True)
    (out_dir / "attachments").mkdir(exist_ok=True)

    updated: list[str] = []
    for fname in PLACEHOLDER_FILES:
        if fname in ("board.json", "flipchart.json"):
            continue
        src = TEMPLATE / fname
        if not src.exists():
            raise BoardError(f"Vorlage-Datei fehlt: {src}")
        text = apply_placeholders(src.read_text(encoding="utf-8"), mapping)
        if fname == "board.html":
            dest_name = board_html
        elif fname == "board.config.json":
            dest_name = "board.config.json"
            new_cfg = json.loads(text)
            if preserved_theme:
                new_cfg["theme"] = _normalize_theme(preserved_theme)
            if preserved_icon:
                new_cfg["icon"] = preserved_icon
            text = json.dumps(new_cfg, ensure_ascii=False, indent=2) + "\n"
        else:
            dest_name = fname
        (out_dir / dest_name).write_text(text, encoding="utf-8")
        updated.append(dest_name)

    for fname in SHARED_LIB_FILES:
        src = KIT_ROOT / fname
        if not src.exists():
            raise BoardError(f"Shared-Lib fehlt: {src}")
        shutil.copy2(src, out_dir / fname)
        updated.append(fname)

    for fname in STOP_SCRIPT_FILES:
        src = TEMPLATE / fname
        if src.exists():
            shutil.copy2(src, out_dir / fname)
            updated.append(fname)

    port_val = int(mapping["__BOARD_PORT__"])
    return {
        "ok": True,
        "slug": mapping["__BOARD_SLUG__"],
        "path": str(out_dir),
        "port": port_val,
        "boardHtml": board_html,
        "url": f"http://127.0.0.1:{port_val}/{board_html}",
        "updated": updated,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Legt ein neues lokales Kanban/Brainstorm-Board aus der Vorlage an."
    )
    parser.add_argument("--name", "-n", default="", help='Anzeigename, z. B. "Mein Spiel"')
    parser.add_argument("--slug", "-s", default="", help="Ordner-/Dateiname")
    parser.add_argument("--out", "-o", default="", help="Zielordner")
    parser.add_argument("--port", "-p", type=int, default=0, help="HTTP-Port")
    parser.add_argument("--force", action="store_true", help="Ziel überschreiben")
    parser.add_argument(
        "--update",
        metavar="BOARD_DIR",
        default="",
        help="Bestehendes Board aktualisieren (Programmdateien aus Vorlage)",
    )
    args = parser.parse_args()

    if args.update:
        try:
            result = update_board_at(args.update)
        except BoardError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        print(f"Board aktualisiert: {result['path']}")
        print(f"  Dateien: {', '.join(result['updated'])}")
        print(f"  URL   : {result['url']}")
        print("  Hinweis: Kanban-Server neu starten und Board-Seite hart neu laden (Strg+F5).")
        return 0

    if not args.name.strip():
        print("Name fehlt (--name / -n).", file=sys.stderr)
        return 1

    try:
        result = create_board(
            args.name,
            slug=args.slug,
            out=args.out or None,
            port=args.port,
            force=args.force,
        )
    except BoardError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(f"Board angelegt: {result['path']}")
    print(f"  Titel : {result['title']}")
    print(f"  Port  : {result['port']}")
    print(f"  Öffnen: {Path(result['path']) / 'Kanban oeffnen.bat'}")
    print(f"  URL   : {result['url']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
