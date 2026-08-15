# -*- coding: utf-8 -*-
"""Lokaler Kanban-Manager: Boards anlegen, auflisten und öffnen."""
from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import threading
import time
import uuid
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, quote, urlparse

KIT_ROOT = Path(__file__).resolve().parent

_spec = importlib.util.spec_from_file_location("new_board", KIT_ROOT / "new-board.py")
assert _spec and _spec.loader
_new_board = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_new_board)

_theme_spec = importlib.util.spec_from_file_location("theme_lib", KIT_ROOT / "theme_lib.py")
assert _theme_spec and _theme_spec.loader
_theme_lib = importlib.util.module_from_spec(_theme_spec)
_theme_spec.loader.exec_module(_theme_lib)

create_board = _new_board.create_board
update_board_at = _new_board.update_board_at
BoardError = _new_board.BoardError
BOARDS_ROOT = _new_board.BOARDS_ROOT
REPO_ROOT = _new_board.REPO_ROOT
default_boards_root = _new_board.default_boards_root
collect_used_ports = _new_board.collect_used_ports
next_free_port = _new_board.next_free_port
slugify = _new_board.slugify
normalize_theme = _theme_lib.normalize_theme
DEFAULT_THEME = _theme_lib.DEFAULT_THEME
THEME_PRESETS = _theme_lib.THEME_PRESETS

MANAGER_PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8760
MANAGER_HTML = "manager.html"
REGISTRY_FILE = KIT_ROOT / "manager-registry.json"
ICONS_DIR = KIT_ROOT / "icons"
ICONS_CATALOG = ICONS_DIR / "catalog.json"

_running: dict[str, subprocess.Popen] = {}
_lock = threading.Lock()
_picker_lock = threading.Lock()
_presence_lock = threading.Lock()
_board_presence: dict[str, float] = {}
_reload_hints: dict[str, dict[str, Any]] = {}
PRESENCE_TTL = 45.0


def touch_board_presence(slug: str) -> dict[str, Any] | None:
    slug = str(slug or "").strip()
    if not slug:
        return None
    now = time.time()
    with _presence_lock:
        _board_presence[slug] = now
        return _reload_hints.pop(slug, None)


def is_board_open(slug: str) -> bool:
    slug = str(slug or "").strip()
    if not slug:
        return False
    with _presence_lock:
        ts = _board_presence.get(slug)
    return ts is not None and (time.time() - ts) <= PRESENCE_TTL


def queue_reload_hint(slug: str, *, card_id: str = "", card_title: str = "") -> None:
    slug = str(slug or "").strip()
    if not slug:
        return
    with _presence_lock:
        _reload_hints[slug] = {
            "reason": "card-copied",
            "cardId": card_id,
            "cardTitle": card_title,
            "at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }


def _default_settings() -> dict[str, Any]:
    return {
        "boardsRoot": str(default_boards_root()),
        "extraPaths": [],
        "theme": dict(normalize_theme(None)),
    }


def _load_settings() -> dict[str, Any]:
    settings = _default_settings()
    if not REGISTRY_FILE.exists():
        return settings
    try:
        data = json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
        if isinstance(data.get("boardsRoot"), str) and data["boardsRoot"].strip():
            settings["boardsRoot"] = data["boardsRoot"].strip()
        settings["extraPaths"] = list(data.get("extraPaths") or [])
        if "theme" in data:
            settings["theme"] = normalize_theme(data.get("theme"))
    except Exception:
        pass
    return settings


def _save_settings(settings: dict[str, Any]) -> None:
    payload = {
        "boardsRoot": str(Path(settings["boardsRoot"]).expanduser().resolve()),
        "extraPaths": list(settings.get("extraPaths") or []),
        "theme": normalize_theme(settings.get("theme")),
    }
    REGISTRY_FILE.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _load_registry() -> list[str]:
    return list(_load_settings().get("extraPaths") or [])


def _save_registry(paths: list[str]) -> None:
    settings = _load_settings()
    settings["extraPaths"] = paths
    _save_settings(settings)


def get_boards_root() -> Path:
    root = Path(_load_settings()["boardsRoot"]).expanduser()
    try:
        root.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass
    return root.resolve()


def set_boards_root(path: str | Path) -> Path:
    root = Path(path).expanduser().resolve()
    if root.exists() and not root.is_dir():
        raise BoardError("Speicherort muss ein Ordner sein.")
    root.mkdir(parents=True, exist_ok=True)
    settings = _load_settings()
    settings["boardsRoot"] = str(root)
    _save_settings(settings)
    return root


def get_theme() -> dict[str, Any]:
    return normalize_theme(_load_settings().get("theme"))


def set_theme(theme: Any) -> dict[str, Any]:
    settings = _load_settings()
    settings["theme"] = normalize_theme(theme)
    _save_settings(settings)
    return settings["theme"]


def pick_folder(initial: str | Path | None = None, title: str = "Ordner wählen") -> str | None:
    """Öffnet den nativen Ordnerdialog (Windows/macOS/Linux via tkinter)."""
    start = str(Path(initial).expanduser()) if initial else str(get_boards_root())
    script = (
        "import sys\n"
        "import tkinter as tk\n"
        "from tkinter import filedialog\n"
        "root = tk.Tk()\n"
        "root.withdraw()\n"
        "try:\n"
        "    root.attributes('-topmost', True)\n"
        "except Exception:\n"
        "    pass\n"
        "path = filedialog.askdirectory(initialdir=sys.argv[1] or None, title=sys.argv[2])\n"
        "root.destroy()\n"
        "sys.stdout.write(path or '')\n"
    )
    with _picker_lock:
        try:
            result = subprocess.run(
                [sys.executable, "-c", script, start, title],
                capture_output=True,
                text=True,
                timeout=600,
                check=False,
            )
        except Exception as exc:  # noqa: BLE001
            raise BoardError(f"Ordnerdialog fehlgeschlagen: {exc}") from exc
    path = (result.stdout or "").strip()
    return path or None


def pick_image_file(initial: str | Path | None = None, title: str = "Icon wählen") -> str | None:
    start = str(Path(initial).expanduser()) if initial else str(Path.home() / "Pictures")
    if not Path(start).exists():
        start = str(Path.home())
    script = (
        "import sys\n"
        "import tkinter as tk\n"
        "from tkinter import filedialog\n"
        "root = tk.Tk()\n"
        "root.withdraw()\n"
        "try:\n"
        "    root.attributes('-topmost', True)\n"
        "except Exception:\n"
        "    pass\n"
        "path = filedialog.askopenfilename(\n"
        "    initialdir=sys.argv[1] or None,\n"
        "    title=sys.argv[2],\n"
        "    filetypes=[\n"
        "        ('Bilder', '*.ico *.png *.jpg *.jpeg *.webp *.gif *.bmp'),\n"
        "        ('Icon', '*.ico'),\n"
        "        ('Alle Dateien', '*.*'),\n"
        "    ],\n"
        ")\n"
        "root.destroy()\n"
        "sys.stdout.write(path or '')\n"
    )
    with _picker_lock:
        try:
            result = subprocess.run(
                [sys.executable, "-c", script, start, title],
                capture_output=True,
                text=True,
                timeout=600,
                check=False,
            )
        except Exception as exc:  # noqa: BLE001
            raise BoardError(f"Dateidialog fehlgeschlagen: {exc}") from exc
    path = (result.stdout or "").strip()
    return path or None


def _image_preview_data_url(path: Path, size: int = 72) -> str | None:
    try:
        from PIL import Image
        import base64
        from io import BytesIO

        with Image.open(path) as img:
            img = img.convert("RGBA")
            img.thumbnail((size, size))
            buf = BytesIO()
            img.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode("ascii")
        return "data:image/png;base64," + b64
    except Exception:
        return None


def install_board_icon(source: str | Path, board_dir: Path) -> Path:
    """Kopiert/konvertiert ein Bild nach board-icon.ico im Board-Ordner."""
    src = Path(source).expanduser().resolve()
    if not src.is_file():
        raise BoardError(f"Icon-Datei nicht gefunden: {src}")

    dest = board_dir / "board-icon.ico"
    suffix = src.suffix.lower()
    if suffix == ".ico":
        shutil.copy2(src, dest)
    else:
        try:
            from PIL import Image
        except ImportError as exc:
            raise BoardError(
                "Für PNG/JPG bitte Pillow installieren oder eine .ico-Datei wählen."
            ) from exc
        with Image.open(src) as img:
            img = img.convert("RGBA")
            w, h = img.size
            side = min(w, h)
            left = (w - side) // 2
            top = (h - side) // 2
            img = img.crop((left, top, left + side, top + side))
            sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
            frames = [img.resize(s, Image.Resampling.LANCZOS) for s in sizes]
            frames[0].save(
                dest,
                format="ICO",
                sizes=sizes,
                append_images=frames[1:],
            )

    # Config aktualisieren
    cfg_path = board_dir / "board.config.json"
    if cfg_path.exists():
        try:
            cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
            cfg["icon"] = "board-icon.ico"
            cfg_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass
    return dest


def _desktop_dir() -> Path:
    if sys.platform == "win32":
        try:
            result = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    "[Environment]::GetFolderPath('Desktop')",
                ],
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )
            path = (result.stdout or "").strip()
            if path:
                return Path(path)
        except Exception:
            pass
    return Path.home() / "Desktop"


def create_desktop_shortcut(
    *,
    name: str,
    target: Path,
    work_dir: Path,
    icon: Path | None = None,
    description: str = "",
    also_copy_to: Path | None = None,
) -> Path:
    """Erstellt eine .lnk auf dem Desktop (Windows)."""
    if sys.platform != "win32":
        raise BoardError("Desktop-Verknüpfungen sind hier nur unter Windows verfügbar.")

    target = Path(target)
    work_dir = Path(work_dir)
    if not target.exists():
        raise BoardError(f"Starter fehlt: {target}")

    safe_name = re.sub(r'[<>:"/\\|?*]+', " ", name).strip() or "Kanban"
    lnk_path = _desktop_dir() / f"{safe_name}.lnk"
    icon_loc = f"{icon},0" if icon and Path(icon).exists() else ""

    ps = (
        "$s = (New-Object -ComObject WScript.Shell).CreateShortcut([string]$env:LNK);\n"
        "$s.TargetPath = [string]$env:TARGET;\n"
        "$s.WorkingDirectory = [string]$env:WORKDIR;\n"
        "$s.WindowStyle = 1;\n"
        "$s.Description = [string]$env:DESC;\n"
        "if ($env:ICON) { $s.IconLocation = [string]$env:ICON }\n"
        "$s.Save();\n"
        "Write-Output $env:LNK\n"
    )
    env = os.environ.copy()
    env["LNK"] = str(lnk_path)
    env["TARGET"] = str(target.resolve())
    env["WORKDIR"] = str(work_dir.resolve())
    env["DESC"] = description or name
    env["ICON"] = icon_loc

    result = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            ps,
        ],
        capture_output=True,
        text=True,
        env=env,
        timeout=60,
        check=False,
    )
    if result.returncode != 0:
        raise BoardError(
            "Verknüpfung fehlgeschlagen: "
            + ((result.stderr or result.stdout or "").strip() or "unbekannt")
        )

    copy_dir = also_copy_to if also_copy_to is not None else work_dir
    local_lnk = Path(copy_dir) / f"{safe_name}.lnk"
    try:
        if local_lnk.resolve() != lnk_path.resolve():
            shutil.copy2(lnk_path, local_lnk)
    except Exception:
        pass

    return lnk_path


def create_manager_desktop_shortcut() -> Path:
    """Desktop-Verknüpfung für den Kanban-Manager."""
    bat = KIT_ROOT / "Kanban Manager oeffnen.bat"
    icon = KIT_ROOT / "icons" / "kanban.ico"
    return create_desktop_shortcut(
        name="Kanban-Manager",
        target=bat,
        work_dir=KIT_ROOT,
        icon=icon if icon.exists() else None,
        description="Kanban-Manager – lokale Boards anlegen und öffnen",
        also_copy_to=KIT_ROOT,
    )


def apply_board_branding(
    board: dict[str, Any],
    *,
    icon_path: str | None = None,
    desktop_shortcut: bool = True,
) -> dict[str, Any]:
    board_dir = Path(board["path"])
    icon_file: Path | None = None
    if icon_path:
        icon_file = install_board_icon(icon_path, board_dir)
    else:
        existing = board_dir / "board-icon.ico"
        if existing.exists():
            icon_file = existing

    shortcut: Path | None = None
    if desktop_shortcut and sys.platform == "win32":
        shortcut = create_desktop_shortcut(
            name=board.get("name") or board.get("title") or board.get("slug") or "Kanban",
            target=board_dir / "Kanban oeffnen.bat",
            work_dir=board_dir,
            icon=icon_file,
            description=f"Kanban: {board.get('name') or board.get('title') or board.get('slug') or 'Board'}",
            also_copy_to=board_dir,
        )

    return {
        "icon": str(icon_file) if icon_file else None,
        "shortcut": str(shortcut) if shortcut else None,
    }


def list_preset_icons() -> list[dict[str, Any]]:
    icons: list[dict[str, Any]] = []
    if ICONS_CATALOG.exists():
        try:
            data = json.loads(ICONS_CATALOG.read_text(encoding="utf-8"))
            for item in data.get("icons") or []:
                ico = ICONS_DIR / str(item.get("ico") or "")
                png = ICONS_DIR / str(item.get("png") or "")
                if not ico.exists():
                    continue
                icons.append(
                    {
                        "id": item.get("id") or ico.stem,
                        "label": item.get("label") or ico.stem,
                        "path": str(ico.resolve()),
                        "previewUrl": f"/icons/{png.name}" if png.exists() else f"/icons/{ico.name}",
                    }
                )
            return icons
        except Exception:
            pass
    # Fallback: Ordner scannen
    if ICONS_DIR.exists():
        for ico in sorted(ICONS_DIR.glob("*.ico")):
            png = ico.with_suffix(".png")
            icons.append(
                {
                    "id": ico.stem,
                    "label": ico.stem,
                    "path": str(ico.resolve()),
                    "previewUrl": f"/icons/{png.name}" if png.exists() else f"/icons/{ico.name}",
                }
            )
    return icons


def resolve_preset_icon(icon_id: str) -> Path | None:
    for item in list_preset_icons():
        if item["id"] == icon_id:
            path = Path(item["path"])
            return path if path.exists() else None
    return None


def _creationflags() -> int:
    if sys.platform == "win32":
        return int(subprocess.CREATE_NO_WINDOW)  # type: ignore[attr-defined]
    return 0


def _port_open(port: int) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.35):
            return True
    except OSError:
        return False


def _board_http_ok(port: int, board_html: str) -> bool:
    """Prüft, ob auf dem Port ein erreichbares Board antwortet (kein toter/falscher Listener)."""
    path = str(board_html or "").lstrip("/") or "index.html"
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.5) as sock:
            req = (
                f"GET /{path} HTTP/1.1\r\n"
                f"Host: 127.0.0.1:{port}\r\n"
                "Connection: close\r\n\r\n"
            ).encode("ascii")
            sock.sendall(req)
            sock.settimeout(0.8)
            buf = b""
            while len(buf) < 64:
                chunk = sock.recv(64 - len(buf))
                if not chunk:
                    break
                buf += chunk
        head = buf.decode("latin-1", "ignore")
        return head.startswith("HTTP/1.") and " 200 " in head[:20]
    except OSError:
        return False


def _pids_listening_on_port(port: int) -> list[int]:
    """PIDs, die am Port lauschen (Windows: netstat, Fallback PowerShell)."""
    pids: list[int] = []
    port = int(port)
    try:
        out = subprocess.check_output(
            ["netstat", "-ano", "-p", "tcp"],
            text=True,
            errors="ignore",
            creationflags=_creationflags(),
        )
    except (OSError, subprocess.CalledProcessError):
        out = ""
    # bewusst locker: "TCP …:8766 … LISTENING 12345"
    pat = re.compile(rf":{port}\s+\S+\s+LISTENING\s+(\d+)", re.I)
    for match in pat.finditer(out):
        pid = int(match.group(1))
        if pid > 0 and pid not in pids:
            pids.append(pid)
    if pids:
        return pids
    if sys.platform == "win32":
        try:
            ps = subprocess.check_output(
                [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    f"(Get-NetTCPConnection -LocalPort {port} -State Listen -ErrorAction SilentlyContinue)."
                    "OwningProcess | Select-Object -Unique",
                ],
                text=True,
                errors="ignore",
                creationflags=_creationflags(),
            )
            for line in ps.splitlines():
                line = line.strip()
                if line.isdigit():
                    pid = int(line)
                    if pid > 0 and pid not in pids:
                        pids.append(pid)
        except (OSError, subprocess.CalledProcessError):
            pass
    return pids


def _free_port(port: int) -> bool:
    """Alten Listener beenden und warten, bis der Port frei ist. True = Port ist frei."""
    for pid in _pids_listening_on_port(port):
        if pid == os.getpid():
            continue
        try:
            if sys.platform == "win32":
                subprocess.run(
                    ["taskkill", "/PID", str(pid), "/T", "/F"],
                    check=False,
                    capture_output=True,
                    creationflags=_creationflags(),
                )
            else:
                os.kill(pid, 15)
        except OSError:
            pass
    for _ in range(40):
        if not _port_open(port):
            return True
        time.sleep(0.15)
    return not _port_open(port)


def _read_board_config(folder: Path) -> dict[str, Any] | None:
    cfg_path = folder / "board.config.json"
    if not cfg_path.exists():
        return None
    try:
        data = json.loads(cfg_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    required = ("title", "slug", "boardHtml", "port")
    if any(k not in data for k in required):
        return None
    return data


def _count_cards(json_path: Path) -> int | None:
    if not json_path.exists():
        return None
    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
        return len(data.get("cards") or [])
    except Exception:
        return None


def _legacy_janamathics() -> dict[str, Any] | None:
    folder = REPO_ROOT / "brainstorm"
    html = folder / "janamathics-kanban.html"
    server = folder / "kanban_server.py"
    if not html.exists() or not server.exists():
        return None
    return {
        "slug": "janamathics",
        "title": "Janamathics \u2013 Kanban Board",
        "name": "Janamathics",
        "path": str(folder.resolve()),
        "port": 8765,
        "boardHtml": "janamathics-kanban.html",
        "url": "http://127.0.0.1:8765/janamathics-kanban.html",
        "legacy": True,
        "running": _port_open(8765),
        "cardCount": _count_cards(folder / "janamathics-kanban.json"),
        "hasIcon": (folder / "board-icon.ico").exists(),
        "iconUrl": "/api/boards/icon?slug=janamathics" if (folder / "board-icon.ico").exists() else None,
    }


def _board_from_folder(folder: Path, *, legacy: bool = False) -> dict[str, Any] | None:
    cfg = _read_board_config(folder)
    if not cfg:
        return None
    port = int(cfg["port"])
    board_html = cfg["boardHtml"]
    board_json = cfg.get("boardJson") or f"{cfg['slug']}-kanban.json"
    return {
        "slug": cfg["slug"],
        "title": cfg["title"],
        "name": cfg["title"].split("\u2013")[0].strip(),
        "path": str(folder.resolve()),
        "port": port,
        "boardHtml": board_html,
        "url": f"http://127.0.0.1:{port}/{board_html}",
        "legacy": legacy,
        "running": _port_open(port),
        "cardCount": _count_cards(folder / board_json),
        "hasIcon": (folder / "board-icon.ico").exists(),
        "iconUrl": f"/api/boards/icon?slug={cfg['slug']}" if (folder / "board-icon.ico").exists() else None,
    }


def list_boards() -> list[dict[str, Any]]:
    boards: list[dict[str, Any]] = []
    seen: set[str] = set()

    legacy = _legacy_janamathics()
    if legacy:
        boards.append(legacy)
        seen.add(str(Path(legacy["path"]).resolve()).lower())

    boards_root = get_boards_root()
    if boards_root.exists():
        for child in sorted(boards_root.iterdir(), key=lambda p: p.name.lower()):
            if not child.is_dir():
                continue
            info = _board_from_folder(child)
            if not info:
                continue
            key = str(Path(info["path"]).resolve()).lower()
            if key in seen:
                continue
            seen.add(key)
            boards.append(info)

    # Auch alten Repo-Ordner scannen (falls dort noch Boards liegen)
    legacy_root = (REPO_ROOT / "boards").resolve()
    if legacy_root != boards_root and legacy_root.exists():
        for child in sorted(legacy_root.iterdir(), key=lambda p: p.name.lower()):
            if not child.is_dir():
                continue
            info = _board_from_folder(child)
            if not info:
                continue
            key = str(Path(info["path"]).resolve()).lower()
            if key in seen:
                continue
            seen.add(key)
            boards.append(info)

    for raw in _load_registry():
        folder = Path(raw).expanduser()
        if not folder.is_dir():
            continue
        info = _board_from_folder(folder)
        if not info:
            continue
        key = str(Path(info["path"]).resolve()).lower()
        if key in seen:
            continue
        seen.add(key)
        boards.append(info)

    return boards


def find_board(slug: str) -> dict[str, Any] | None:
    for board in list_boards():
        if board["slug"] == slug:
            return board
    return None


def find_board_by_path(path: str) -> dict[str, Any] | None:
    try:
        key = str(Path(path).expanduser().resolve()).lower()
    except Exception:
        return None
    for board in list_boards():
        try:
            if str(Path(board["path"]).resolve()).lower() == key:
                return board
        except Exception:
            continue
    return None


def resolve_board(*, slug: str = "", path: str = "") -> dict[str, Any]:
    board = find_board(str(slug or "").strip()) if slug else None
    if not board and path:
        board = find_board_by_path(str(path))
    if not board:
        raise BoardError("Board nicht gefunden.")
    return board


def _board_data_path(board: dict[str, Any]) -> Path:
    folder = Path(board["path"])
    cfg = _read_board_config(folder) or {}
    name = cfg.get("boardJson")
    if name:
        return folder / str(name)
    if board.get("legacy"):
        return folder / "janamathics-kanban.json"
    return folder / f"{board['slug']}-kanban.json"


def _load_board_data(board: dict[str, Any]) -> dict[str, Any]:
    path = _board_data_path(board)
    if not path.exists():
        raise BoardError(f"Board-Datei fehlt: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise BoardError(f"Board-Datei unlesbar: {path}") from exc
    if not isinstance(data, dict):
        raise BoardError("Board-JSON muss ein Objekt sein.")
    if not isinstance(data.get("cards"), list):
        data["cards"] = []
    if not isinstance(data.get("columns"), list):
        data["columns"] = []
    return data


def _save_board_data(board: dict[str, Any], data: dict[str, Any]) -> Path:
    path = _board_data_path(board)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _safe_attach_name(name: str) -> str:
    base = Path(str(name or "datei")).name
    base = re.sub(r"[^\w.\- ()\[\]]+", "_", base, flags=re.UNICODE).strip("._ ")
    return (base or "datei")[:120]


def search_cards(query: str, *, limit: int = 40) -> list[dict[str, Any]]:
    """Board-übergreifend in Kartentiteln und Notizen suchen."""
    q = str(query or "").strip().lower()
    if len(q) < 2:
        return []

    limit = max(1, min(int(limit or 40), 100))
    title_hits: list[dict[str, Any]] = []
    notes_hits: list[dict[str, Any]] = []

    for board in list_boards():
        try:
            data = _load_board_data(board)
        except BoardError:
            continue
        except Exception:
            continue

        col_titles: dict[str, str] = {}
        for col in data.get("columns") or []:
            if isinstance(col, dict) and col.get("id"):
                col_titles[str(col["id"])] = str(col.get("title") or "")

        for card in data.get("cards") or []:
            if not isinstance(card, dict):
                continue
            card_id = str(card.get("id") or "").strip()
            if not card_id:
                continue
            title = str(card.get("title") or "")
            notes = str(card.get("notes") or "")
            title_l = title.lower()
            notes_l = notes.lower()
            in_title = q in title_l
            in_notes = q in notes_l
            if not in_title and not in_notes:
                continue

            preview = " ".join(notes.split())
            if len(preview) > 140:
                preview = preview[:137] + "…"

            hit = {
                "cardId": card_id,
                "title": title or "(ohne Titel)",
                "notesPreview": preview,
                "matchedIn": "title" if in_title else "notes",
                "columnId": str(card.get("column") or ""),
                "columnTitle": col_titles.get(str(card.get("column") or ""), ""),
                "boardSlug": board["slug"],
                "boardName": board.get("name") or board.get("title") or board["slug"],
                "boardPort": int(board.get("port") or 0),
            }
            if in_title:
                title_hits.append(hit)
            else:
                notes_hits.append(hit)

    return (title_hits + notes_hits)[:limit]


def board_meta(slug: str = "", path: str = "") -> dict[str, Any]:
    board = resolve_board(slug=slug, path=path)
    data = _load_board_data(board)
    columns = []
    for col in data.get("columns") or []:
        if not isinstance(col, dict) or not col.get("id"):
            continue
        columns.append(
            {
                "id": str(col["id"]),
                "title": str(col.get("title") or col["id"]),
            }
        )
    out = dict(board)
    out["columns"] = columns
    return out


def copy_card_to_board(
    *,
    source_card_id: str,
    source_slug: str = "",
    source_path: str = "",
    target_slug: str = "",
    target_path: str = "",
    target_column_id: str = "",
    open_after: bool = False,
) -> dict[str, Any]:
    source_card_id = str(source_card_id or "").strip()
    if not source_card_id:
        raise BoardError("sourceCardId fehlt.")

    source = resolve_board(slug=source_slug, path=source_path)
    target = resolve_board(slug=target_slug, path=target_path)
    if Path(source["path"]).resolve() == Path(target["path"]).resolve():
        raise BoardError("Quelle und Ziel sind dasselbe Board.")

    source_data = _load_board_data(source)
    target_data = _load_board_data(target)
    source_card = next(
        (c for c in source_data["cards"] if isinstance(c, dict) and str(c.get("id")) == source_card_id),
        None,
    )
    if not source_card:
        raise BoardError(f"Karte nicht gefunden: {source_card_id}")

    target_columns = [c for c in (target_data.get("columns") or []) if isinstance(c, dict) and c.get("id")]
    if not target_columns:
        raise BoardError("Zielboard hat keine Spalten.")

    source_col_id = str(source_card.get("column") or "")
    source_col_title = ""
    for col in source_data.get("columns") or []:
        if isinstance(col, dict) and str(col.get("id")) == source_col_id:
            source_col_title = str(col.get("title") or "")
            break

    chosen_col = str(target_column_id or "").strip()
    valid_ids = {str(c["id"]) for c in target_columns}
    if chosen_col not in valid_ids:
        # Namens-Match, sonst erste Spalte
        chosen_col = ""
        if source_col_title:
            for col in target_columns:
                if str(col.get("title") or "").strip().lower() == source_col_title.strip().lower():
                    chosen_col = str(col["id"])
                    break
        if not chosen_col:
            chosen_col = str(target_columns[0]["id"])

    new_id = "c_" + uuid.uuid4().hex[:12]
    source_folder = Path(source["path"])
    target_folder = Path(target["path"])
    src_attach_dir = source_folder / "attachments"
    dst_attach_dir = target_folder / "attachments"
    dst_attach_dir.mkdir(exist_ok=True)

    new_attachments: list[dict[str, Any]] = []
    for att in source_card.get("attachments") or []:
        if not isinstance(att, dict):
            continue
        stored = str(att.get("stored") or "")
        name = _safe_attach_name(str(att.get("name") or "datei"))
        src_file = src_attach_dir / Path(stored).name if stored else None
        if not src_file or not src_file.exists():
            # Metadaten ohne Datei überspringen
            continue
        file_id = "a_" + uuid.uuid4().hex[:12]
        new_stored = f"{file_id}_{name}"
        shutil.copy2(src_file, dst_attach_dir / new_stored)
        new_attachments.append(
            {
                "id": file_id,
                "name": name,
                "stored": new_stored,
                "url": "/attachments/" + new_stored,
                "mime": str(att.get("mime") or "application/octet-stream"),
                "size": int(att.get("size") or src_file.stat().st_size),
                "addedAt": time.strftime("%Y-%m-%dT%H:%M:%S"),
            }
        )

    src_flip = source_folder / "flipcharts" / f"{source_card_id}.json"
    if src_flip.exists():
        dst_flip_dir = target_folder / "flipcharts"
        dst_flip_dir.mkdir(exist_ok=True)
        shutil.copy2(src_flip, dst_flip_dir / f"{new_id}.json")

    new_card: dict[str, Any] = {
        "id": new_id,
        "title": str(source_card.get("title") or "Kopie"),
        "notes": str(source_card.get("notes") or ""),
        "column": chosen_col,
        "color": str(source_card.get("color") or "none"),
        "dueDate": str(source_card.get("dueDate") or ""),
        "createdAt": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "attachments": new_attachments,
        "sourceLink": {
            "boardSlug": source["slug"],
            "boardTitle": source.get("name") or source.get("title") or source["slug"],
            "cardId": source_card_id,
            "cardTitle": str(source_card.get("title") or ""),
            "port": int(source["port"]),
        },
    }

    target_data["cards"].append(new_card)
    _save_board_data(target, target_data)

    result: dict[str, Any] = {
        "ok": True,
        "card": new_card,
        "target": {
            "slug": target["slug"],
            "title": target.get("title"),
            "port": target["port"],
            "url": target["url"],
            "path": target["path"],
        },
        "source": {
            "slug": source["slug"],
            "title": source.get("title"),
            "port": source["port"],
            "url": source["url"],
        },
    }
    target_was_open = is_board_open(target["slug"])
    if target_was_open:
        queue_reload_hint(
            target["slug"],
            card_id=new_id,
            card_title=str(new_card.get("title") or ""),
        )
    result["targetWasOpen"] = target_was_open
    if open_after:
        open_board(target["slug"], card_id=new_id)
        result["opened"] = True
    return result


def open_board(slug: str, card_id: str | None = None) -> dict[str, Any]:
    board = find_board(slug)
    if not board:
        raise BoardError(f"Board nicht gefunden: {slug}")

    folder = Path(board["path"])
    server_script = folder / "kanban_server.py"
    if not server_script.exists():
        raise BoardError(f"kanban_server.py fehlt in {folder}")

    port = int(board["port"])
    board_html = str(board.get("boardHtml") or "")
    url = board["url"]
    card_id = str(card_id or "").strip()
    if card_id:
        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}card={quote(card_id)}"

    # Mehrere Boards parallel: laufenden, gesunden Server wiederverwenden
    if _port_open(port) and _board_http_ok(port, board_html):
        webbrowser.open(url)
        board = find_board(slug) or board
        board["running"] = True
        return {"ok": True, "board": board}

    # Port belegt, aber keine gültige Board-Antwort → alten Listener ersetzen
    if _port_open(port):
        with _lock:
            old = _running.pop(slug, None)
            if old is not None and old.poll() is None:
                try:
                    old.terminate()
                except OSError:
                    pass
        if not _free_port(port):
            raise BoardError(
                f"Port {port} ist belegt und konnte nicht freigegeben werden. "
                "Bitte den alten Kanban-Prozess beenden und erneut öffnen."
            )

    with _lock:
        proc = _running.get(slug)
        if proc is not None and proc.poll() is None:
            webbrowser.open(url)
            board = find_board(slug) or board
            board["running"] = True
            return {"ok": True, "board": board}
        log_path = folder / "kanban-server.log"
        log_file = open(log_path, "a", encoding="utf-8")  # noqa: SIM115
        proc = subprocess.Popen(
            [sys.executable, str(server_script), str(port)],
            cwd=str(folder),
            stdout=log_file,
            stderr=subprocess.STDOUT,
            creationflags=_creationflags(),
        )
        _running[slug] = proc

    ready = False
    for _ in range(40):
        time.sleep(0.25)
        if _port_open(port):
            ready = True
            break
    if not ready:
        raise BoardError(f"Server startet nicht auf Port {port}")

    webbrowser.open(url)
    board = find_board(slug) or board
    board["running"] = True
    return {"ok": True, "board": board}


def stop_all_board_servers() -> dict[str, Any]:
    """Beendet alle bekannten Board-Server (Manager-Tracking + Port-Scan)."""
    stopped_slugs: list[str] = []
    stopped_ports: list[int] = []

    with _lock:
        for slug, proc in list(_running.items()):
            if proc.poll() is None:
                try:
                    proc.terminate()
                    try:
                        proc.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                except OSError:
                    pass
            if slug not in stopped_slugs:
                stopped_slugs.append(slug)
        _running.clear()

    seen_ports: set[int] = set()
    for board in list_boards():
        port = int(board.get("port") or 0)
        if not port or port in seen_ports:
            continue
        seen_ports.add(port)
        if _port_open(port):
            _free_port(port)
            stopped_ports.append(port)
            slug = str(board.get("slug") or "")
            if slug and slug not in stopped_slugs:
                stopped_slugs.append(slug)

    return {"boards": stopped_slugs, "ports": stopped_ports, "count": len(stopped_ports)}


_HTTP_SERVER: ThreadingHTTPServer | None = None


def delete_board(slug: str, *, confirm: bool = False) -> dict[str, Any]:
    if not confirm:
        raise BoardError("Löschen erfordert Bestätigung.")
    board = find_board(slug)
    if not board:
        raise BoardError(f"Board nicht gefunden: {slug}")
    if board.get("legacy"):
        raise BoardError("Das Janamathics-Board kann hier nicht gelöscht werden.")

    folder = Path(board["path"])
    port = int(board["port"])
    with _lock:
        proc = _running.pop(slug, None)
        if proc and proc.poll() is None:
            try:
                proc.terminate()
            except OSError:
                pass
    _free_port(port)

    paths = [p for p in _load_registry() if Path(p).resolve() != folder.resolve()]
    _save_registry(paths)

    if folder.exists():
        shutil.rmtree(folder)
    return {"ok": True, "deleted": slug}


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(KIT_ROOT), **kwargs)

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write("[%s] %s\n" % (self.log_date_time_string(), fmt % args))

    def _send_json(self, code: int, payload: dict | list) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _read_json_body(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        data = json.loads(raw.decode("utf-8") or "{}")
        if not isinstance(data, dict):
            raise ValueError("JSON-Objekt erwartet")
        return data

    def _handle_shutdown(self) -> None:
        result = stop_all_board_servers()
        self._send_json(200, {"ok": True, **result})

        def _stop() -> None:
            time.sleep(0.3)
            server = globals().get("_HTTP_SERVER")
            if server is not None:
                try:
                    server.shutdown()
                except Exception:
                    pass
            os._exit(0)

        threading.Thread(target=_stop, daemon=True).start()

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            self.path = f"/{MANAGER_HTML}"
            return super().do_GET()
        if path == "/api/boards":
            self._send_json(200, {"boards": list_boards()})
            return
        if path == "/api/cards/search":
            qs = parse_qs(urlparse(self.path).query)
            q = (qs.get("q") or [""])[0]
            try:
                limit = int((qs.get("limit") or ["40"])[0])
            except ValueError:
                limit = 40
            self._send_json(200, {"ok": True, "query": q, "results": search_cards(q, limit=limit)})
            return
        if path == "/api/boards/meta":
            qs = parse_qs(urlparse(self.path).query)
            slug = (qs.get("slug") or [""])[0]
            board_path = (qs.get("path") or [""])[0]
            self._send_json(200, {"ok": True, "board": board_meta(slug=slug, path=board_path)})
            return
        if path == "/api/icons":
            self._send_json(200, {"icons": list_preset_icons()})
            return
        if path == "/api/boards/icon":
            qs = parse_qs(urlparse(self.path).query)
            slug = (qs.get("slug") or [""])[0]
            board = find_board(slug)
            if not board:
                self.send_error(404)
                return
            icon = Path(board["path"]) / "board-icon.ico"
            if not icon.exists():
                self.send_error(404)
                return
            raw = icon.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "image/x-icon")
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(raw)
            return
        if path == "/api/meta":
            used = sorted(collect_used_ports())
            root = get_boards_root()
            self._send_json(
                200,
                {
                    "boardsRoot": str(root),
                    "defaultBoardsRoot": str(default_boards_root()),
                    "suggestedPort": next_free_port(8766, set(used)),
                    "usedPorts": used,
                    "desktopDir": str(_desktop_dir()),
                    "theme": get_theme(),
                    "presets": THEME_PRESETS,
                },
            )
            return
        return super().do_GET()

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        try:
            if path == "/api/shutdown":
                self._handle_shutdown()
                return
            body = self._read_json_body()
            if path == "/api/boards":
                slug_val = (body.get("slug") or "").strip() or slugify(str(body.get("name") or ""))
                parent_raw = (body.get("parent") or body.get("out") or "").strip()
                parent = Path(parent_raw).expanduser() if parent_raw else get_boards_root()
                if parent.exists() and not parent.is_dir():
                    raise BoardError("Speicherort muss ein Ordner sein.")
                out_dir = parent / slug_val
                if parent.name == slug_val and (parent / "board.config.json").exists():
                    out_dir = parent

                result = create_board(
                    body.get("name", ""),
                    slug=slug_val,
                    out=out_dir,
                    port=int(body.get("port") or 0),
                    force=bool(body.get("force")),
                    theme=get_theme(),
                )
                out_path = Path(result["path"]).resolve()
                known_roots = {
                    get_boards_root(),
                    BOARDS_ROOT.resolve(),
                    (REPO_ROOT / "boards").resolve(),
                }
                under_known = any(
                    out_path == root or root in out_path.parents for root in known_roots
                )
                if not under_known:
                    paths = _load_registry()
                    key = str(out_path)
                    if key not in paths:
                        paths.append(key)
                        _save_registry(paths)

                icon_path = (body.get("iconPath") or "").strip() or None
                icon_id = (body.get("iconId") or "").strip()
                if not icon_path and icon_id:
                    preset = resolve_preset_icon(icon_id)
                    if not preset:
                        raise BoardError(f"Unbekanntes Icon: {icon_id}")
                    icon_path = str(preset)

                branding = apply_board_branding(
                    result,
                    icon_path=icon_path,
                    desktop_shortcut=bool(body.get("desktopShortcut", True)),
                )
                result.update(branding)

                if body.get("openAfter"):
                    open_board(result["slug"])
                    result["opened"] = True
                self._send_json(201, result)
                return

            if path == "/api/boards/open":
                result = open_board(
                    str(body.get("slug") or ""),
                    card_id=str(body.get("cardId") or body.get("card") or "") or None,
                )
                self._send_json(200, result)
                return

            if path == "/api/boards/presence":
                slug = str(body.get("slug") or "")
                hint = touch_board_presence(slug)
                self._send_json(200, {"ok": True, "reloadHint": hint})
                return

            if path == "/api/cards/copy":
                result = copy_card_to_board(
                    source_card_id=str(body.get("sourceCardId") or body.get("cardId") or ""),
                    source_slug=str(body.get("sourceSlug") or ""),
                    source_path=str(body.get("sourcePath") or ""),
                    target_slug=str(body.get("targetSlug") or ""),
                    target_path=str(body.get("targetPath") or ""),
                    target_column_id=str(body.get("targetColumnId") or ""),
                    open_after=bool(body.get("openAfter")),
                )
                self._send_json(200, result)
                return

            if path == "/api/boards/delete":
                result = delete_board(
                    str(body.get("slug") or ""),
                    confirm=bool(body.get("confirm")),
                )
                self._send_json(200, result)
                return

            if path == "/api/boards/update":
                board = find_board(str(body.get("slug") or ""))
                if not board:
                    raise BoardError("Board nicht gefunden.")
                result = update_board_at(board["path"])
                self._send_json(200, result)
                return

            if path == "/api/boards/set-icon":
                board = find_board(str(body.get("slug") or ""))
                if not board:
                    raise BoardError("Board nicht gefunden.")
                icon_path = (body.get("iconPath") or "").strip()
                if not icon_path:
                    chosen = pick_image_file(title="Icon für Board wählen")
                    if not chosen:
                        self._send_json(200, {"ok": True, "cancelled": True})
                        return
                    icon_path = chosen
                branding = apply_board_branding(
                    board,
                    icon_path=icon_path,
                    desktop_shortcut=bool(body.get("desktopShortcut", True)),
                )
                preview = _image_preview_data_url(Path(branding["icon"])) if branding.get("icon") else None
                self._send_json(
                    200,
                    {
                        "ok": True,
                        "cancelled": False,
                        "preview": preview,
                        **branding,
                    },
                )
                return

            if path == "/api/pick-folder":
                initial = (body.get("initial") or "").strip() or str(get_boards_root())
                title = (body.get("title") or "Ordner wählen").strip()
                chosen = pick_folder(initial, title=title)
                self._send_json(
                    200,
                    {"ok": True, "path": chosen, "cancelled": chosen is None},
                )
                return

            if path == "/api/pick-image":
                initial = (body.get("initial") or "").strip() or None
                title = (body.get("title") or "Icon wählen").strip()
                chosen = pick_image_file(initial, title=title)
                preview = _image_preview_data_url(Path(chosen)) if chosen else None
                self._send_json(
                    200,
                    {
                        "ok": True,
                        "path": chosen,
                        "cancelled": chosen is None,
                        "preview": preview,
                    },
                )
                return

            if path == "/api/settings/boards-root":
                root = set_boards_root(str(body.get("path") or ""))
                self._send_json(200, {"ok": True, "boardsRoot": str(root)})
                return

            if path == "/api/settings/theme":
                theme = set_theme(body.get("theme") or body)
                self._send_json(200, {"ok": True, "theme": theme})
                return

            if path == "/api/settings/manager-shortcut":
                shortcut = create_manager_desktop_shortcut()
                self._send_json(200, {"ok": True, "shortcut": str(shortcut)})
                return

            if path == "/api/slugify":
                self._send_json(200, {"slug": slugify(str(body.get("name") or ""))})
                return

            self.send_error(404)
        except BoardError as exc:
            self._send_json(400, {"ok": False, "error": str(exc)})
        except Exception as exc:  # noqa: BLE001
            self._send_json(500, {"ok": False, "error": str(exc)})


def main() -> None:
    global _HTTP_SERVER
    get_boards_root().mkdir(parents=True, exist_ok=True)
    _HTTP_SERVER = ThreadingHTTPServer(("127.0.0.1", MANAGER_PORT), Handler)
    server = _HTTP_SERVER
    url = f"http://127.0.0.1:{MANAGER_PORT}/{MANAGER_HTML}"
    print(f"Kanban-Manager: {url}", flush=True)
    print(f"Boards-Ordner: {get_boards_root()}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
