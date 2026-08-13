# -*- coding: utf-8 -*-
"""Mini-Server für ein lokales Kanban/Brainstorm-Board (Autosave auf Festplatte)."""
from __future__ import annotations

import base64
import json
import re
import sys
import time
import uuid
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

try:
    from export_lib import build_export  # type: ignore
except Exception:  # noqa: BLE001
    build_export = None  # type: ignore

ROOT = Path(__file__).resolve().parent
CONFIG_FILE = ROOT / "board.config.json"

try:
    from theme_lib import DEFAULT_THEME, normalize_theme  # type: ignore
except Exception:  # noqa: BLE001
    DEFAULT_THEME = {
        "bg": "#1f3d2f",
        "bg2": "#274c3a",
        "accent": "#e2a53a",
        "chalk": "#e8f0e6",
        "angle": 160,
        "spots": True,
    }

    def normalize_theme(raw):  # type: ignore
        data = raw if isinstance(raw, dict) else {}
        out = dict(DEFAULT_THEME)
        out.update({k: data[k] for k in DEFAULT_THEME if k in data})
        return out


def load_config() -> dict:
    if not CONFIG_FILE.exists():
        raise SystemExit(f"board.config.json fehlt: {CONFIG_FILE}")
    cfg = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    required = ("title", "slug", "boardHtml", "boardJson", "flipchartJson", "port")
    missing = [k for k in required if k not in cfg]
    if missing:
        raise SystemExit(f"board.config.json unvollständig, fehlt: {', '.join(missing)}")
    cfg["theme"] = normalize_theme(cfg.get("theme"))
    return cfg


def save_config(cfg: dict) -> None:
    CONFIG_FILE.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")


def get_theme() -> dict:
    cfg = load_config()
    return normalize_theme(cfg.get("theme"))


def set_theme(theme: dict) -> dict:
    cfg = load_config()
    cfg["theme"] = normalize_theme(theme)
    save_config(cfg)
    return cfg["theme"]


CFG = load_config()
DATA_FILE = ROOT / CFG["boardJson"]
FLIPCHART_FILE = ROOT / CFG["flipchartJson"]
FLIPCHART_DIR = ROOT / "flipcharts"
ATTACHMENTS_DIR = ROOT / "attachments"
BOARD_HTML = CFG["boardHtml"]
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else int(CFG["port"])
MAX_ATTACHMENT_BYTES = 40 * 1024 * 1024  # 40 MB

FLIPCHART_SEED = {
    "type": "excalidraw",
    "version": 2,
    "source": CFG.get("source", f"{CFG['slug']}-kanban"),
    "elements": [],
    "appState": {"viewBackgroundColor": "#f7f3e8", "gridSize": None},
    "files": {},
}

SEED = {
    "columns": [
        {"id": "brainstorm", "title": "Brainstorm", "hint": "Freie Ideen", "color": "yellow"},
        {"id": "backlog", "title": "Backlog", "hint": "Irgendwann / geparkt", "color": "orange"},
        {"id": "next", "title": "Als Nächstes", "hint": "Konkrete Prioritäten", "color": "blue"},
        {"id": "ist", "title": "Umgesetzt", "hint": "Was schon fertig ist", "color": "green"},
    ],
    "cards": [
        {
            "id": "c1",
            "column": "brainstorm",
            "title": "Willkommen – erste Idee notieren",
            "notes": "Diese Karte kannst du löschen oder umbenennen.",
        },
    ],
}


def ensure_data_file() -> None:
    if not DATA_FILE.exists():
        DATA_FILE.write_text(json.dumps(SEED, ensure_ascii=False, indent=2), encoding="utf-8")
    if not FLIPCHART_FILE.exists():
        FLIPCHART_FILE.write_text(
            json.dumps(FLIPCHART_SEED, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    FLIPCHART_DIR.mkdir(exist_ok=True)
    ATTACHMENTS_DIR.mkdir(exist_ok=True)


def _safe_filename(name: str) -> str:
    base = Path(str(name or "datei")).name
    base = re.sub(r"[^\w.\- ()\[\]]+", "_", base, flags=re.UNICODE).strip("._ ")
    if not base:
        base = "datei"
    return base[:120]


def _attachment_path(stored: str) -> Path | None:
    name = Path(str(stored or "")).name
    if not name or name in (".", ".."):
        return None
    path = (ATTACHMENTS_DIR / name).resolve()
    try:
        path.relative_to(ATTACHMENTS_DIR.resolve())
    except ValueError:
        return None
    return path


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write("[%s] %s\n" % (self.log_date_time_string(), fmt % args))

    def _send_json(self, code: int, payload: dict | list) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, PUT, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def _send_bytes(self, code: int, raw: bytes, content_type: str, filename: str) -> None:
        safe_name = str(filename or "export.bin").encode("ascii", "ignore").decode("ascii") or "export.bin"
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Content-Disposition", f'attachment; filename="{safe_name}"')
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(raw)

    def _handle_export(self, payload: dict) -> None:
        if build_export is None:
            raise ValueError("export_lib.py fehlt im Board-Ordner.")
        fmt = str(payload.get("format") or "").strip().lower()
        data = payload.get("state")
        if not isinstance(data, dict) or not isinstance(data.get("cards"), list):
            if DATA_FILE.exists():
                data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
            else:
                raise ValueError("Kein Board-Inhalt zum Exportieren.")
        title = str(payload.get("title") or CFG.get("title") or CFG.get("slug") or "Kanban")
        raw, filename, mime = build_export(fmt, data, title)
        self._send_bytes(200, raw, mime, filename)

    def _send_raw_json_file(self, path: Path) -> None:
        if not path.exists():
            path.write_text(
                json.dumps(FLIPCHART_SEED, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        raw = path.read_text(encoding="utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw.encode("utf-8"))))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw.encode("utf-8"))

    def _is_board(self, path: str) -> bool:
        return path in (f"/{CFG['boardJson']}", "/api/board")

    def _is_global_flipchart(self, path: str) -> bool:
        return path in (f"/{CFG['flipchartJson']}", "/api/flipchart")

    def _card_flipchart_file(self, path: str) -> Path | None:
        m = re.fullmatch(r"/flipcharts/([A-Za-z0-9_-]+)\.json", path)
        if not m:
            return None
        FLIPCHART_DIR.mkdir(exist_ok=True)
        return FLIPCHART_DIR / (m.group(1) + ".json")

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, PUT, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _is_flipchart_index(self, path: str) -> bool:
        return path in ("/api/flipchart-index", "/flipchart-index.json")

    def _read_body(self) -> bytes:
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length < 0:
            return b""
        if length > MAX_ATTACHMENT_BYTES + 1024 * 1024:
            raise ValueError(f"Datei zu groß (max. {MAX_ATTACHMENT_BYTES // (1024 * 1024)} MB)")
        return self.rfile.read(length)

    def _save_attachment_bytes(self, raw: bytes, name: str, mime: str) -> dict:
        if len(raw) > MAX_ATTACHMENT_BYTES:
            raise ValueError(f"Datei zu groß (max. {MAX_ATTACHMENT_BYTES // (1024 * 1024)} MB)")
        ATTACHMENTS_DIR.mkdir(exist_ok=True)
        safe = _safe_filename(name)
        file_id = "a_" + uuid.uuid4().hex[:12]
        stored = f"{file_id}_{safe}"
        target = ATTACHMENTS_DIR / stored
        target.write_bytes(raw)
        return {
            "id": file_id,
            "name": safe,
            "stored": stored,
            "url": "/attachments/" + stored,
            "mime": mime or "application/octet-stream",
            "size": len(raw),
            "addedAt": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }

    def _handle_attachment_upload(self) -> None:
        """Speichert Anhänge. JSON+Base64 bevorzugt; Binär-Body als Fallback."""
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query or "")
        raw = self._read_body()
        content_type = (self.headers.get("Content-Type") or "").split(";", 1)[0].strip().lower()
        wants_json = content_type in ("application/json", "text/json") or (
            not qs.get("name") and raw[:1] in (b"{", b"[")
        )

        if wants_json:
            try:
                data = json.loads(raw.decode("utf-8") or "{}")
            except UnicodeDecodeError as exc:
                raise ValueError(
                    "Ungültiger Datei-Upload. Bitte Board-Seite neu laden und Server neu starten."
                ) from exc
            if not isinstance(data, dict):
                raise ValueError("Erwarte JSON-Objekt für Datei-Upload")
            name = str(data.get("name") or "datei")
            mime = str(data.get("mime") or "application/octet-stream")
            b64 = str(data.get("data") or "")
            if "," in b64 and b64.strip().startswith("data:"):
                b64 = b64.split(",", 1)[1]
            if not b64:
                raise ValueError("Keine Dateidaten im Upload")
            file_bytes = base64.b64decode(b64, validate=False)
            meta = self._save_attachment_bytes(file_bytes, name, mime)
            self._send_json(200, {"ok": True, "attachment": meta})
            return

        name = unquote((qs.get("name") or ["datei"])[0])
        mime = unquote(
            (qs.get("mime") or [content_type or "application/octet-stream"])[0]
            or "application/octet-stream"
        )
        meta = self._save_attachment_bytes(raw, name, mime)
        self._send_json(200, {"ok": True, "attachment": meta})

    def _handle_attachment_delete(self) -> None:
        length = int(self.headers.get("Content-Length", "0") or "0")
        raw = self.rfile.read(length) if length else b"{}"
        data = json.loads(raw.decode("utf-8") or "{}")
        stored = str(data.get("stored") or data.get("id") or "")
        path = _attachment_path(stored)
        if path is None:
            # also allow deleting by stored filename from id prefix search
            raise ValueError("Ungültige Datei")
        if path.exists():
            path.unlink()
        self._send_json(200, {"ok": True})

    def _flipchart_has_content(self, path: Path) -> tuple[bool, int]:
        if not path.exists():
            return False, 0
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            elements = data.get("elements") or []
            count = sum(1 for e in elements if isinstance(e, dict) and not e.get("isDeleted"))
            return count > 0, count
        except Exception:
            return False, 0

    def _build_flipchart_index(self) -> dict:
        counts: dict[str, int] = {}
        filled, count = self._flipchart_has_content(FLIPCHART_FILE)
        if filled:
            counts["global"] = count
        FLIPCHART_DIR.mkdir(exist_ok=True)
        for path in FLIPCHART_DIR.glob("*.json"):
            filled, count = self._flipchart_has_content(path)
            if filled:
                counts[path.stem] = count
        return {"ids": sorted(counts.keys()), "counts": counts}

    def do_GET(self) -> None:
        path = self.path.split("?", 1)[0]
        ensure_data_file()
        if path in ("/", "/index.html"):
            self.path = f"/{BOARD_HTML}"
            return super().do_GET()
        if path in ("/api/theme", "/theme.json"):
            self._send_json(200, {"theme": get_theme()})
            return
        if self._is_flipchart_index(path):
            self._send_json(200, self._build_flipchart_index())
            return
        if self._is_board(path):
            self._send_raw_json_file(DATA_FILE)
            return
        if self._is_global_flipchart(path):
            self._send_raw_json_file(FLIPCHART_FILE)
            return
        card_file = self._card_flipchart_file(path)
        if card_file is not None:
            self._send_raw_json_file(card_file)
            return
        super().do_GET()

    def do_POST(self) -> None:
        path = self.path.split("?", 1)[0]
        try:
            if path in ("/api/attachments", "/attachments"):
                self._handle_attachment_upload()
                return
            raw = self._read_body()
            data = json.loads(raw.decode("utf-8") or "{}")
            if path == "/api/export":
                if not isinstance(data, dict):
                    raise ValueError("JSON-Objekt erwartet")
                self._handle_export(data)
                return
            if path in ("/api/theme", "/theme.json"):
                theme = set_theme(data.get("theme") if isinstance(data, dict) else data)
                self._send_json(200, {"ok": True, "theme": theme})
                return
            self.send_error(404)
        except Exception as exc:  # noqa: BLE001
            self._send_json(400, {"ok": False, "error": str(exc)})

    def do_DELETE(self) -> None:
        path = self.path.split("?", 1)[0]
        try:
            if path in ("/api/attachments", "/attachments"):
                self._handle_attachment_delete()
                return
            self.send_error(404)
        except Exception as exc:  # noqa: BLE001
            self._send_json(400, {"ok": False, "error": str(exc)})

    def do_PUT(self) -> None:
        path = self.path.split("?", 1)[0]
        try:
            if path in ("/api/attachments", "/attachments"):
                self._handle_attachment_upload()
                return
            if path in ("/api/theme", "/theme.json"):
                return self.do_POST()
            raw = self._read_body()
            try:
                data = json.loads(raw.decode("utf-8"))
            except UnicodeDecodeError as exc:
                raise ValueError(
                    "Ungültige Anfrage: Binärdaten statt JSON. "
                    "Bei Datei-Uploads bitte /api/attachments nutzen und den Server neu starten."
                ) from exc
            if self._is_board(path):
                if not isinstance(data, dict) or not isinstance(data.get("cards"), list):
                    raise ValueError("Erwarte Objekt mit 'cards'-Array")
                DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
                self._send_json(200, {"ok": True, "path": str(DATA_FILE), "count": len(data["cards"])})
                return

            card_file = self._card_flipchart_file(path)
            if self._is_global_flipchart(path) or card_file is not None:
                if not isinstance(data, dict) or "elements" not in data:
                    raise ValueError("Erwarte Excalidraw-Objekt mit 'elements'")
                target = FLIPCHART_FILE if card_file is None else card_file
                if card_file is not None:
                    FLIPCHART_DIR.mkdir(exist_ok=True)
                target.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
                self._send_json(
                    200,
                    {
                        "ok": True,
                        "path": str(target),
                        "count": len(data.get("elements") or []),
                    },
                )
                return
            self.send_error(404)
        except Exception as exc:  # noqa: BLE001
            self._send_json(400, {"ok": False, "error": str(exc)})


def main() -> None:
    ensure_data_file()
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"Kanban-Server: http://127.0.0.1:{PORT}/{BOARD_HTML}", flush=True)
    print(f"Titel: {CFG['title']}", flush=True)
    print(f"Speicherdatei: {DATA_FILE}", flush=True)
    print(f"Flipchart: {FLIPCHART_FILE}", flush=True)
    print(f"Karten-Flipcharts: {FLIPCHART_DIR}", flush=True)
    print(f"Anhänge: {ATTACHMENTS_DIR}", flush=True)
    print("Zum Beenden: Strg+C", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer beendet.", flush=True)


if __name__ == "__main__":
    main()
