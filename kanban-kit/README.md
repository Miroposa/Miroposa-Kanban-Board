# Kanban-Kit – Grundgerüst + lokaler Manager

Wiederverwendbare Vorlage aus dem Janamathics Kanban & Brainstorm Board.
Boards legst du am einfachsten über die **Manager-Oberfläche** an.

## Manager öffnen

Doppelklick:

`docs/kanban-kit/Kanban Manager oeffnen.bat`

Oder Desktop-Verknüpfung **„Kanban-Manager“** (im Manager oben rechts anlegen / erneuern).

URL: http://127.0.0.1:8760/manager.html

> **Hinweis:** Eine `.exe` bringt hier wenig Vorteil – der Manager startet ohnehin nur den lokalen Python-Server und den Browser. Eine Desktop-Verknüpfung (`.lnk`) mit Icon verhält sich wie ein Programm, ohne Extra-Build, Antivirus-Warnungen oder Neuverpacken bei Updates.

Dort kannst du:

- neues Board mit Namen anlegen
- **Speicherort wählen** (Ordnerdialog oder Pfad eingeben)
- **Icon wählen** aus dem Vorrat (`icons/`) oder eigenes PNG/JPG/ICO
- **Einstellungen** für Hintergrund, Schrift, Sprache (DE/EN, automatisch nach System)
- Standard-Speicherort speichern („Als Standard“)
- vorhandene Boards öffnen (Server startet automatisch)
- Boards löschen (nicht Janamathics)

Neue Boards erben das aktuelle Manager-Theme.
Icon-Vorrat neu erzeugen: `python docs/kanban-kit/generate_icons.py`

## CLI (optional)

```powershell
python docs/kanban-kit/new-board.py --name "Mein Spiel"
```

## Was liegt in einem Board?

| Datei | Rolle |
|-------|--------|
| `board.config.json` | Titel, Dateinamen, Port |
| `*-kanban.html` | UI (Kanban + Flipchart) |
| `*-kanban.json` | Autosave der Karten/Spalten |
| `*-flipchart.json` | Globales Excalidraw-Flipchart |
| `flipcharts/` | Flipcharts pro Karte |
| `kanban_server.py` | Lokaler Server + Schreib-API |
| `Kanban oeffnen.bat` | Startet Server und Browser |

Standard-Ablage: `Downloads/<slug>/` (änderbar im Manager)

## Vorlage anpassen

- UI/Logik: `template/board.html`
- Server: `template/kanban_server.py`
- Startinhalt: `template/board.json`
- Manager-UI: `manager.html`
- Nach Sync mit Janamathics: `python _build_template.py`

## Janamathics

Das bestehende Board unter `brainstorm/` bleibt unberührt (Port **8765**) und erscheint im Manager als Projekt-Board.
