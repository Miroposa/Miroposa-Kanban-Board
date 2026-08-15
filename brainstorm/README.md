# Janamathics – Kanban & Brainstorm

Lokales Board: Ideen notieren, Prioritäten ziehen, Fortschritt tracken.  
Feature-Stand entspricht dem **Kanban-Kit-Template** (Anhänge, Multi-Export, Copy, Due-Date-Filter, Themes, i18n).

## Wo wird gespeichert?

**Datei im Projekt:**

`brainstorm/janamathics-kanban.json`

Jede Änderung wird dorthin geschrieben – **wenn** du das Board über die Desktop-Verknüpfung oder `Kanban oeffnen.bat` öffnest.

Nicht die HTML-Datei per Doppelklick öffnen (`file://`) – dann landet der Stand nur im Browser und geht leicht verloren.

## Schnell öffnen

| Weg | So geht’s |
|-----|-----------|
| **Desktop** | Verknüpfung **Janamathics Kanban** |
| **Batch** | `brainstorm/Kanban oeffnen.bat` |
| **Manager** | Kanban-Manager → Janamathics öffnen |
| **URL** | http://127.0.0.1:8765/janamathics-kanban.html (Server muss laufen) |

## Spalten

1. **Umgesetzt** – was schon im Spiel steckt  
2. **Brainstorm** – freie Ideen  
3. **Backlog** – später / geparkt  
4. **Als Nächstes** – konkrete Prioritäten  

(weitere Spalten kannst du selbst anlegen)

Spalte löschen: 🗑 oben rechts in der Spaltenüberschrift.  
Karten darin werden in eine andere Spalte verschoben. Mindestens eine Spalte bleibt.

## Speichern

Automatisch bei jeder Änderung in `janamathics-kanban.json`.  
Oben steht dann z. B. `✓ … · Datei: janamathics-kanban.json`.  
Anhänge liegen unter `brainstorm/attachments/`.

## Bedienung

- **+ Idee** → Text → **Anlegen & platzieren** → auf Spalte/Karte klicken  
- Karten **ziehen** (auch auf andere Karten)  
- **Löschen** auf der Karte oder im Bearbeiten-Dialog  
- **Fällig am** + Due-Date-Filter in der Toolbar  
- **Anhänge** im Karteneditor (Bilder/Dateien)  
- **Export**-Menü: JSON, Excel, Word, PDF, PNG  
- **⧉ Kopieren** im Editor → Karte in ein anderes Board (Manager muss laufen)  
- **Flipchart** oben = allgemeines Board · auf jeder Karte **Flipchart** = Ideen zu dieser Karte  
- Karten-Flipcharts: `brainstorm/flipcharts/`  
- Spalte mit **+ Spalte** anlegen · mit **🗑** löschen · mit **⠿** verschieben  
- **Doppelklick** / ✎ bearbeiten · `N` neue Idee · `Esc` Platzieren abbrechen  
- **Einstellungen** für Hintergrund/Theme  
- **Reset** stellt den Startinhalt (Seed) wieder her  

## Template angleichen

Nach Feature-Updates im Kit:

```text
python kanban-kit/sync-janamathics.py
```

Überschreibt UI/Server/Libs in `brainstorm/`, lässt JSON und Flipcharts unberührt.
