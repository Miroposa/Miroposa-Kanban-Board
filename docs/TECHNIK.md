# Technikdokument – Miroposa Kanban Board

Architektur, Datenfluss und Implementierungsdetails der lokalen Kanban-/Brainstorm-App.

## 1. Ziel und Randbedingungen

- **Lokal only:** nur `127.0.0.1`, kein Cloud-Backend
- **Datei = Wahrheit:** Board-Zustand in JSON (+ Anhänge, Versionen, Backups)
- **Zwei Server-Rollen:**
  1. **Manager** (`manager_server.py`, Port **8760**) – Boards verwalten und starten
  2. **Board-Server** (`kanban_server.py`, z. B. **8765**) – ein Board bedienen und speichern
- **Stack:** Python-Stdlib (`ThreadingHTTPServer`) + Single-Page HTML/JS/CSS (kein Build)
- **Export:** XLSX/DOCX/ODT/PDF rein mit Stdlib (`export_lib.py`, ZIP/XML bzw. einfaches PDF)
- **Flipchart:** Excalidraw 0.17.x per CDN (React) – Online beim ersten Laden nötig
- **Zielplattform:** Windows (`.bat` / `.ps1`, Desktop-`.lnk`)

---

## 2. Gesamtarchitektur

```text
┌─────────────────────┐     startet      ┌──────────────────────────┐
│  Manager (8760)     │ ───────────────► │  Board-Server (z.B. 8765)│
│  manager_server.py  │                  │  kanban_server.py        │
│  manager.html       │  cards/search    │  *-kanban.html           │
│                     │  cards/copy      │                          │
└─────────┬───────────┘                  └────────────┬─────────────┘
          │                                           │
          │ manager-registry.json                     │ PUT JSON + Snapshots
          │ icons/, template/, shared libs            ▼
          ▼                              ┌──────────────────────────┐
   new-board.py / sync-janamathics.py    │  Board-Ordner            │
                                         │  *.json, flipcharts/,    │
                                         │  attachments/, versions/,│
                                         │  backups/, config        │
                                         └──────────────────────────┘
```

1. Manager scannt Boards, legt aus Vorlage an, startet Prozesse, vermittelt Suche/Copy.
2. Jedes Board = eigener Port + Prozess.
3. Browser-UI speichert per HTTP; Server schreibt Dateien und legt bei Bedarf Versionen/Backups an.

---

## 3. Projektstruktur

| Pfad | Rolle |
|------|--------|
| `kanban-kit/manager_server.py` | Manager-HTTP-Server (**8760**) |
| `kanban-kit/manager.html` | Manager-UI |
| `kanban-kit/new-board.py` | Board erzeugen / aktualisieren (CLI + Lib) |
| `kanban-kit/sync-janamathics.py` | Template → `brainstorm/` (Daten bleiben) |
| `kanban-kit/template/` | Vorlage: HTML, Server, Seed, Starter, `export_lib.py` |
| `kanban-kit/theme_lib.*`, `i18n_lib.js`, `theme_shared.css` | **Shared Libs** (eine Quelle; beim Create/Sync kopiert) |
| `kanban-kit/generate_icons.py` | Icon-Vorrat erzeugen |
| `brainstorm/` | Janamathics-Board |
| `boards/` | Optionaler Scan-Pfad im Repo |

Shared Libs liegen **nicht** mehr dauerhaft unter `template/` – nur im Kit-Root und in erzeugten Boards.

---

## 4. Konfiguration und Datenmodell

### `board.config.json`

Pflichtfelder u. a.: `title`, `slug`, `boardHtml`, `boardJson`, `flipchartJson`, `port`.  
Optional: `source`, `boardDir`, `theme` (`bg`, `bg2`, `accent`, `chalk`, `angle`, `spots`, `font`, `lang`).

### Kanban-JSON (`*-kanban.json`)

```json
{
  "columns": [
    { "id": "brainstorm", "title": "Brainstorm", "hint": "...", "color": "yellow", "done": false }
  ],
  "cards": [
    {
      "id": "c1",
      "column": "brainstorm",
      "title": "Erste Idee",
      "notes": "...",
      "due": null,
      "color": null,
      "attachments": [],
      "recurrence": null,
      "milestoneId": null,
      "createdAt": "...",
      "completedAt": null,
      "sourceLink": null
    }
  ],
  "milestones": []
}
```

Fehlt die Datei: Server schreibt **Seed** (Standardspalten + Willkommenskarte).

### Flipcharts

Excalidraw-JSON (`elements`, `appState`, `files`, …). Global laut Config; pro Karte `flipcharts/<cardId>.json`. Index: `/api/flipchart-index`.

### Anhänge

Unter `attachments/` als `a_<uuid>_<safeName>`, max. **40 MB**. Metadaten in der Karte (`id`, `name`, `stored`, `url`, `mime`, `size`, `addedAt`).

### Versionen & Backups

| Ordner | Verhalten |
|--------|-----------|
| `versions/` | Snapshot vor Überschreiben des Board-JSON; Keep ~30 |
| `backups/` | Tägliches Zip des Board-Stands; Keep ~14 |

---

## 5. Board-Server (`kanban_server.py`)

### Start

```text
python kanban_server.py [port]
```

Port sonst aus Config; Bind nur `127.0.0.1`. Legt fehlende Seed-Dateien und Ordner `flipcharts/`, `attachments/`, `versions/`, `backups/` an. Statische Auslieferung aus dem Board-Root.

### HTTP-Endpunkte

| Methode | Pfad | Zweck |
|---------|------|--------|
| `GET` | `/`, `/index.html` | Redirect auf `boardHtml` |
| `GET`/`PUT` | `/api/board`, `/{boardJson}` | Board lesen / speichern (+ Version/Backup) |
| `GET`/`PUT` | `/api/flipchart`, `/{flipchartJson}` | Globales Flipchart |
| `GET`/`PUT` | `/flipcharts/<id>.json` | Karten-Flipchart |
| `GET` | `/api/flipchart-index` | Befüllte Flipchart-IDs/Counts |
| `GET`/`POST` | `/api/theme` | Theme lesen / in Config schreiben |
| `POST`/`PUT`/`DELETE` | `/api/attachments` | Upload (JSON+Base64 oder Binär) / Löschen |
| `POST` | `/api/export` | `export_lib.build_export` (xlsx/docx/odt/pdf) |
| `GET` | `/api/versions` | Versionen listen |
| `POST` | `/api/versions/restore` | Version wiederherstellen |
| `GET`/`POST` | `/api/cleanup/orphans` | Orphans melden / löschen |
| `POST` | `/api/shutdown` | Server beenden |

Autosave: UI sendet vollständiges Board-Objekt per `PUT`; Server überschreibt die JSON-Datei.

### Export

`export_lib.build_export(format, state, title)` → `(bytes, filename, mime)`. Formate: **xlsx**, **docx**, **odt**, **pdf** (alles Stdlib). JSON/PNG werden clientseitig erzeugt.

---

## 6. Manager-Server (`manager_server.py`)

Port **8760**. Persistenz: `manager-registry.json` (`boardsRoot`, `extraPaths[]`, `theme`).

### Aufgaben

- Boards scannen: Downloads-Root, Extra-Pfade, `boards/`, festes Janamathics unter `brainstorm/`
- Anlegen / Aktualisieren über `new-board.py` (`create_board`, `update_board_at`)
- Prozesse starten/überwachen; Presence für offene Boards
- Icons (`icons/catalog.json`), Desktop-Shortcuts, Windows-Picker
- Karten-Suche und Kopie Board→Board (inkl. Anhänge/Flipchart, `sourceLink`)
- Shutdown aller Board-Server / Manager

### API (Auszug)

| Methode | Pfad | Zweck |
|---------|------|--------|
| `GET` | `/api/boards` | Liste |
| `GET` | `/api/boards/meta`, `/api/meta` | Metadaten |
| `GET` | `/api/cards/search` | Suche über Boards |
| `GET` | `/api/icons`, `/api/boards/icon` | Icons |
| `POST` | `/api/boards` | Anlegen |
| `POST` | `/api/boards/open` | Starten |
| `POST` | `/api/boards/update` | Vorlage auf bestehendes Board |
| `POST` | `/api/boards/delete` | Löschen |
| `POST` | `/api/boards/set-icon` | Icon setzen |
| `POST` | `/api/boards/presence` | Presence / Reload-Hint |
| `POST` | `/api/cards/copy` | Karte kopieren |
| `POST` | `/api/pick-folder`, `/api/pick-image` | Dialoge |
| `POST` | `/api/settings/*` | Root, Theme, Manager-Shortcut |
| `POST` | `/api/slugify` | Slug vorschlagen |
| `POST` | `/api/shutdown` | Alles beenden |

---

## 7. Board anlegen / aktualisieren (`new-board.py`)

1. Name → Slug (`slugify`)
2. Freier Port (Standard ab **8766**, Janamathics **8765**, Manager **8760**)
3. Zielordner (Default: `~/Downloads/<slug>/`)
4. Template-Dateien kopieren, Platzhalter ersetzen (`__BOARD_*__` u. a.)
5. Shared Libs aus Kit-Root mitkopieren
6. `board.config.json` schreiben

CLI: `--name`, `--slug`, `--out`, `--port`, `--force`, `--update`.  
`update_board_at` erneuert UI/Server/Libs, lässt Nutzerdaten.

Ergebnis: autarkes Board-Verzeichnis inkl. Starter (`Kanban oeffnen.*`, `Kanban Server beenden.*`).

---

## 8. Frontend (Board-HTML)

`template/board.html` → in Boards als `*-kanban.html`. Ohne Build-Step.

Wesentliche Fähigkeiten:

- Spalten-CRUD, Drag, Done-Erkennung; Karten mit Farbe, Due, Recurrence, Milestone, Checklisten, Anhänge
- Ansichten Board / Woche / Monat; Filter; Statistik; Milestone-Leiste
- Undo/Redo (~80 Schritte); Import JSON/CSV; Export-Menü inkl. Versionen & Orphan-Cleanup
- Themes/`theme_lib.js` + `theme_shared.css`; i18n DE/EN/`auto`
- Flipchart-Overlay (Excalidraw CDN); Copy-Dialog gegen Manager-API
- localStorage-Fallback + Warnung bei `file://`

---

## 9. Starter-Skripte (Windows)

`Kanban oeffnen.bat/.ps1`: Port freigeben → Server starten → Browser öffnen.  
`Kanban Server beenden.bat/.ps1`: Prozess auf dem Board-/Manager-Port beenden.  
Manager-Äquivalent analog; optional Desktop-`.lnk` mit Icon.

---

## 10. Sync Template → Janamathics

```text
python kanban-kit/sync-janamathics.py
```

Kopiert UI, Server, Libs, Export/Starter nach `brainstorm/`. Unberührt: Board-JSON, Flipcharts, Anhänge, Versionen/Backups. Optional Smoke-Marker am Skriptende.

---

## 11. Sicherheit

- Nur Loopback; keine Auth (Einzelplatz)
- CORS `*` für lokale Fetch-Aufrufe
- Upload-Dateinamen bereinigt; Speichern nur unter `attachments/`
- Nicht für öffentliches Hosting gedacht

---

## 12. Pflege

| Änderung | Wo |
|----------|-----|
| UI/Logik neuer Boards | `kanban-kit/template/board.html` |
| Board-API | `kanban-kit/template/kanban_server.py` |
| Exportformate | `kanban-kit/template/export_lib.py` |
| Manager | `manager.html` / `manager_server.py` |
| Theme/i18n | Kit-Root-Libs → Create/Update/Sync |
| Janamathics angleichen | `sync-janamathics.py` |
| Icons | `generate_icons.py` |

Bestehende Boards ohne Update/Sync bleiben auf altem Stand.

---

## 13. Abhängigkeiten

**Pflicht:** Python 3.10+ (Stdlib reicht für Server, Export, Kernfunktion).

**Optional:** Pillow nur für `generate_icons.py`. Flipchart-CDN braucht Netz.

---

## 14. Verwandte Doku

- [ANLEITUNG.md](ANLEITUNG.md) – Bedienung  
- [../README.md](../README.md) – Überblick  
- [../kanban-kit/README.md](../kanban-kit/README.md) – Kit & Manager  
- [../brainstorm/README.md](../brainstorm/README.md) – Janamathics  
