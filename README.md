# Miroposa Kanban Board

Lokale Kanban- und Brainstorm-App für Windows: Ideen notieren, priorisieren, mit Flipcharts skizzieren und den Fortschritt tracken – alles speichert auf der Festplatte, ohne Cloud.

## Was steckt drin?

| Teil | Beschreibung |
|------|----------------|
| **Kanban-Manager** | Boards anlegen, öffnen, aktualisieren, löschen; Suche; Themes; Icons; Speicherort |
| **Board-Vorlage** (`kanban-kit/`) | Wiederverwendbares Grundgerüst für neue Boards |
| **Janamathics** (`brainstorm/`) | Beispiel-/Arbeitsboard (Port **8765**) |

Jedes Board läuft als eigener lokaler Python-Server und speichert Karten, Flipcharts, Anhänge, Versionen und Backups als Dateien im Board-Ordner.

## Voraussetzungen

- **Windows** (Batch-/PowerShell-Starter und Desktop-Verknüpfungen)
- **Python 3.10+** im PATH (`python --version`)
- Moderner Browser (Chrome, Edge, Firefox)
- Für Flipcharts: Internet einmalig nötig (Excalidraw per CDN)

Export (Excel/Word/ODT/PDF) läuft über die **Python-Standardbibliothek** – keine Extra-Pakete nötig. Details: [docs/TECHNIK.md](docs/TECHNIK.md).

## Schnellstart

1. Doppelklick auf `kanban-kit/Kanban Manager oeffnen.bat`  
   (oder Desktop-Verknüpfung **Kanban-Manager**, im Manager anlegen)
2. Browser öffnet: http://127.0.0.1:8760/manager.html
3. Neues Board anlegen **oder** Janamathics öffnen

Janamathics direkt:

- `brainstorm/Kanban oeffnen.bat`
- URL: http://127.0.0.1:8765/janamathics-kanban.html

Server beenden: `Kanban Server beenden.bat` im Kit bzw. Board-Ordner, oder im Board **Beenden**.

> **Wichtig:** HTML-Dateien nicht per Doppelklick (`file://`) öffnen – dann gibt es kein zuverlässiges Autosave. Immer über `.bat` oder Manager starten.

## Dokumentation

| Dokument | Inhalt |
|----------|--------|
| [docs/ANLEITUNG.md](docs/ANLEITUNG.md) | Bedienung: Karten, Filter, Kalender, Export/Import, Versionen |
| [docs/TECHNIK.md](docs/TECHNIK.md) | Architektur, Dateiformate, APIs, Server-Ablauf |

Kurzinfos auch in:

- [kanban-kit/README.md](kanban-kit/README.md) – Manager & Vorlage
- [brainstorm/README.md](brainstorm/README.md) – Janamathics-Board

## Ordnerstruktur

```text
Kanban Board/
├── README.md
├── docs/
│   ├── ANLEITUNG.md
│   └── TECHNIK.md
├── kanban-kit/                 ← Manager + Vorlage + Shared Libs + Icons
│   ├── manager.html / manager_server.py   (Port 8760)
│   ├── new-board.py / sync-janamathics.py
│   ├── theme_lib.* / i18n_lib.js / theme_shared.css
│   ├── template/               ← Vorlage für neue Boards
│   └── icons/
├── brainstorm/                 ← Janamathics (Port 8765)
└── boards/                     ← optionaler Boards-Ordner im Repo
```

Neue Boards landen standardmäßig unter `Downloads/<name>/` (im Manager änderbar), Ports ab **8766**.

## Features (Überblick)

**Manager**

- Boards anlegen, öffnen, aus Vorlage aktualisieren, löschen (Janamathics geschützt)
- Icon-Vorrat oder eigenes Bild, Desktop-Verknüpfungen
- Theme/Schrift/Sprache, Standard-Speicherort
- Karten-Suche über alle Boards, Karte Board→Board kopieren
- Alle Board-Server beenden / Manager-Shutdown

**Board**

- Spalten & Karten per Drag & Drop (CRUD, Farben, Done-Spalte)
- Notizen mit Checklisten, Fälligkeit, Wiederholung (täglich/wöchentlich/monatlich)
- Anhänge (max. 40 MB), globales Flipchart + Flipchart pro Karte (Excalidraw)
- Filter: Farbe, Fälligkeit; Suche (lokal + andere Boards)
- Ansichten: Board / Woche / Monat; Milestones; Statistik
- Undo/Redo (Strg+Z/Y), Speichern & Beenden
- Export: JSON, XLSX, DOCX, ODT, PDF, PNG
- Import: JSON (ersetzen), CSV (Karten anhängen)
- Versionen wiederherstellen, verwaiste Anhänge/Flipcharts aufräumen
- Themes, 8 Schriften, Sprache DE/EN/auto

## Lizenz / Nutzung

Privates Projekt von Miroposa. Nur für autorisierte Nutzung vorgesehen.
