# -*- coding: utf-8 -*-
"""Mini-Server für Janamathics Kanban: Dateien + JSON-Autosave auf Festplatte."""
from __future__ import annotations

import json
import re
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_FILE = ROOT / "janamathics-kanban.json"
FLIPCHART_FILE = ROOT / "janamathics-flipchart.json"
FLIPCHART_DIR = ROOT / "flipcharts"
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8765

FLIPCHART_SEED = {
    "type": "excalidraw",
    "version": 2,
    "source": "janamathics-kanban",
    "elements": [],
    "appState": {"viewBackgroundColor": "#f7f3e8", "gridSize": None},
    "files": {},
}

SEED = {
    "columns": [
        {"id": "ist", "title": "Umgesetzt", "hint": "Was schon im Spiel steckt", "color": "green"},
        {"id": "brainstorm", "title": "Brainstorm", "hint": "Freie Ideen", "color": "yellow"},
        {"id": "backlog", "title": "Backlog", "hint": "Irgendwann / geparkt", "color": "orange"},
        {"id": "next", "title": "Als Nächstes", "hint": "Konkrete Prioritäten", "color": "blue"},
    ],
    "cards": [
        {"id": "c1", "column": "ist", "title": "2D Godot 4.7 – Janamathics", "notes": ""},
        {"id": "c2", "column": "ist", "title": "Outdoor: Schule, Straße, Parallax", "notes": ""},
        {"id": "c3", "column": "ist", "title": "Player: laufen, springen, Animationen", "notes": ""},
        {"id": "c4", "column": "ist", "title": "Schultür → Klassenzimmer (Verweil-Delay)", "notes": ""},
        {"id": "c5", "column": "ist", "title": "Mathe-Quiz: +/−, Level, Leben, Highscore", "notes": ""},
        {"id": "c6", "column": "ist", "title": "Früchte & Blumen sammeln (Respawn)", "notes": ""},
        {"id": "c7", "column": "ist", "title": "Spielplatz: Schaukel, Rutsche, Federwippe", "notes": ""},
        {"id": "c8", "column": "ist", "title": "HUD: Score + Herzen (global)", "notes": ""},
        {"id": "c9", "column": "ist", "title": "GameState Autoload über Szenen", "notes": ""},
        {"id": "b1", "column": "brainstorm", "title": "Rückweg Klassenzimmer → Außenwelt", "notes": ""},
        {"id": "b2", "column": "brainstorm", "title": "Mehr Karten: Wald, Park, Stadt", "notes": ""},
        {"id": "b3", "column": "brainstorm", "title": "NPCs / Freunde zum Quatschen", "notes": ""},
        {"id": "b4", "column": "brainstorm", "title": "Geheimwege & versteckte Sammelobjekte", "notes": ""},
        {"id": "b5", "column": "brainstorm", "title": "Tageszeit / Wetter", "notes": ""},
        {"id": "b6", "column": "brainstorm", "title": "Mehr Rechenarten: × ÷ Brüche?", "notes": ""},
        {"id": "b7", "column": "brainstorm", "title": "Themenwelten: Geld, Uhr, Geometrie", "notes": ""},
        {"id": "b8", "column": "brainstorm", "title": "Belohnungen sichtbar in der Welt", "notes": ""},
        {"id": "b9", "column": "brainstorm", "title": "Lehrer-NPC / Hilfe bei Fehlern", "notes": ""},
        {"id": "b10", "column": "brainstorm", "title": "Speichern / Fortschritt laden", "notes": ""},
        {"id": "b11", "column": "brainstorm", "title": "Hauptmenü + Einstellungen", "notes": ""},
        {"id": "b12", "column": "brainstorm", "title": "Achievements / Sammelbuch", "notes": ""},
        {
            "id": "b13",
            "column": "brainstorm",
            "title": "Offene Fragen: Zielgruppe? Story oder Sandbox? Mobile?",
            "notes": "Zum Brainstormen offen lassen",
        },
        {
            "id": "n1",
            "column": "next",
            "title": "Rückweg aus dem Klassenzimmer",
            "notes": "Sinnvoller nächster Baustein laut Architektur",
        },
        {"id": "n2", "column": "backlog", "title": "Controller-Support", "notes": ""},
        {"id": "n3", "column": "backlog", "title": "Mehrsprachigkeit DE/EN", "notes": ""},
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
        self.send_header("Access-Control-Allow-Methods", "GET, PUT, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

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
        return path in ("/janamathics-kanban.json", "/api/board")

    def _is_global_flipchart(self, path: str) -> bool:
        return path in ("/janamathics-flipchart.json", "/api/flipchart")

    def _card_flipchart_file(self, path: str) -> Path | None:
        m = re.fullmatch(r"/flipcharts/([A-Za-z0-9_-]+)\.json", path)
        if not m:
            return None
        FLIPCHART_DIR.mkdir(exist_ok=True)
        return FLIPCHART_DIR / (m.group(1) + ".json")

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, PUT, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _is_flipchart_index(self, path: str) -> bool:
        return path in ("/api/flipchart-index", "/flipchart-index.json")

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

    def do_PUT(self) -> None:
        path = self.path.split("?", 1)[0]
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        try:
            data = json.loads(raw.decode("utf-8"))
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
    print(f"Kanban-Server: http://127.0.0.1:{PORT}/janamathics-kanban.html", flush=True)
    print(f"Speicherdatei: {DATA_FILE}", flush=True)
    print(f"Flipchart: {FLIPCHART_FILE}", flush=True)
    print(f"Karten-Flipcharts: {FLIPCHART_DIR}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
