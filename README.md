# Miroposa Kanban Board

Lokale Kanban- und Brainstorm-App für Windows: Ideen notieren, priorisieren, mit Flipcharts skizzieren und den Fortschritt tracken – alles speichert auf der Festplatte, ohne Cloud.

## Was steckt drin?

| Teil | Beschreibung |
|------|----------------|
| **Kanban-Manager** | Zentrale Oberfläche: Boards anlegen, öffnen, löschen, Themes & Speicherort |
| **Board-Vorlage** (`kanban-kit/`) | Wiederverwendbares Grundgerüst für neue Boards |
| **Janamathics** (`brainstorm/`) | Beispiel-/Arbeitsboard (Port 8765) |

Jedes Board läuft als eigener lokaler Python-Server und speichert Karten, Flipcharts und Anhänge als Dateien im Board-Ordner.

## Voraussetzungen

- **Windows** (Batch-/PowerShell-Starter und Desktop-Verknüpfungen)
- **Python 3.10+** im PATH (`python --version`)
- Moderner Browser (Chrome, Edge, Firefox)

Optionale Export-Formate (Excel/Word/PDF) benötigen ggf. zusätzliche Python-Pakete – siehe [docs/TECHNIK.md](docs/TECHNIK.md).

## Schnellstart

1. Doppelklick auf `kanban-kit/Kanban Manager oeffnen.bat`  
   (oder Desktop-Verknüpfung **Kanban-Manager**, im Manager oben rechts anlegen)
2. Browser öffnet: http://127.0.0.1:8760/manager.html
3. Neues Board anlegen **oder** Janamathics öffnen

Janamathics direkt:

- `brainstorm/Kanban oeffnen.bat`
- URL: http://127.0.0.1:8765/janamathics-kanban.html

> **Wichtig:** HTML-Dateien nicht per Doppelklick (`file://`) öffnen – dann gibt es kein Autosave auf die Festplatte. Immer über die `.bat`-Datei oder den Manager starten.

## Dokumentation

| Dokument | Inhalt |
|----------|--------|
| [docs/ANLEITUNG.md](docs/ANLEITUNG.md) | Bedienung: Karten, Spalten, Flipcharts, Export, Themes |
| [docs/TECHNIK.md](docs/TECHNIK.md) | Architektur, Dateiformate, APIs, Server-Ablauf |

Kurzinfos auch in:

- [kanban-kit/README.md](kanban-kit/README.md) – Manager & Vorlage
- [brainstorm/README.md](brainstorm/README.md) – Janamathics-Board

## Ordnerstruktur

```text
Kanban Board/
├── README.md                 ← diese Datei
├── docs/
│   ├── ANLEITUNG.md          ← Benutzerhandbuch
│   └── TECHNIK.md            ← technische Beschreibung
├── kanban-kit/               ← Manager + Vorlage + Icons
│   ├── manager.html
│   ├── manager_server.py     ← Port 8760
│   ├── new-board.py
│   ├── template/             ← Vorlage für neue Boards
│   └── icons/
├── brainstorm/               ← Janamathics-Board (Port 8765)
└── boards/                   ← optionaler Boards-Ordner im Repo
```

Neue Boards landen standardmäßig unter `Downloads/<name>/` (im Manager änderbar).

## Features (Kurzüberblick)

- Spalten und Karten per Drag & Drop
- Notizen, Fälligkeitsdatum, Anhänge
- Globales Flipchart + Flipchart pro Karte (Excalidraw)
- Themes, Schrift, Sprache DE/EN
- Export (JSON, Excel, Word, PDF, PNG – je nach verfügbaren Libs)
- Karten zwischen Boards kopieren (über den Manager)
- Desktop-Verknüpfungen mit Icon

## Lizenz / Nutzung

Privates Projekt von Miroposa. Nur für autorisierte Nutzung vorgesehen.
