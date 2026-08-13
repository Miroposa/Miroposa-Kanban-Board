# Janamathics – Kanban & Brainstorm

Lokales Board: Ideen notieren, Prioritäten ziehen, Fortschritt tracken.

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
| **URL** | http://127.0.0.1:8765/janamathics-kanban.html (Server muss laufen) |

## Spalten

1. **Umgesetzt** – was schon im Spiel steckt  
2. **Brainstorm** – freie Ideen  
3. **Backlog** – später / geparkt  
4. **Als Nächstes** – konkrete Prioritäten  

Spalte löschen: 🗑 oben rechts in der Spaltenüberschrift.  
Karten darin werden in eine andere Spalte verschoben. Mindestens eine Spalte bleibt.

## Speichern

Automatisch bei jeder Änderung in `janamathics-kanban.json`.  
Oben steht dann z. B. `✓ … · Datei: janamathics-kanban.json`.

## Bedienung

- **+ Idee** → Text → **Anlegen & platzieren** → auf Spalte/Karte klicken  
- Karten **ziehen** (auch auf andere Karten)  
- **Löschen** auf der Karte oder im Bearbeiten-Dialog  
- **Flipchart** oben = allgemeines Board · auf jeder Karte **Flipchart** = Ideen/Beispiele zu genau dieser Karte  
- Karten-Flipcharts liegen unter `brainstorm/flipcharts/`  
- Spalte mit **+ Spalte** anlegen · mit **🗑** löschen · mit **⠿** verschieben  
- **Doppelklick** / ✎ bearbeiten · `N` neue Idee · `Esc` Platzieren abbrechen  
- **Export/Import** optional als Backup-Kopie  
- **Reset** stellt den Startinhalt wieder her  
