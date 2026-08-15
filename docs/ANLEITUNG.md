# Anleitung – Miroposa Kanban Board

Schritt für die tägliche Nutzung: Manager starten, Boards bedienen, Daten sichern.

## 1. Erste Schritte

### Manager starten

1. Doppelklick auf `kanban-kit/Kanban Manager oeffnen.bat`
2. Browser: http://127.0.0.1:8760/manager.html
3. Optional: Desktop-Verknüpfung **Kanban-Manager** im Manager anlegen

### Python prüfen

```powershell
python --version
```

Python 3.10+ muss im PATH sein.

### Board öffnen – immer über Starter

| Weg | Wann |
|-----|------|
| Manager → Board öffnen | Übersicht über alle Boards |
| `Kanban oeffnen.bat` im Board-Ordner | Direktes Öffnen |
| Desktop-Verknüpfung | Schnellzugriff |

Nicht die `.html` per Doppelklick öffnen (`file://`).

Server beenden: **Beenden** im Board, `Kanban Server beenden.bat`, oder im Manager alle Server stoppen.

---

## 2. Manager

- **Neues Board** – Name, Speicherort, Icon
- **Öffnen** – startet Board-Server + Browser
- **Aktualisieren** – UI/Server aus der Vorlage (Karten & Anhänge bleiben)
- **Löschen** – Janamathics ist geschützt
- **Suche** – Karten über alle bekannten Boards
- **Einstellungen** – Theme, Schrift, Sprache (DE / EN / auto), Standard-Speicherort
- **Icon** – Vorrat oder eigene Bilddatei; Desktop-Verknüpfung

Standard-Ablage: `Downloads/<board-name>/`.

---

## 3. Board bedienen

### Ansichten & Toolbar

- **Board / Woche / Monat** – Kalender-Navigation (← → Heute)
- **Statistik** – Übersicht (gesamt, erledigt, überfällig, Spalten)
- **Farbschema-Filter** und **Fälligkeits-Filter** (überfällig / heute / 7 Tage / ohne)
- **Suche** – lokal; Treffer in anderen Boards, wenn der Manager läuft
- **Milestones** – Ziele anlegen, filtern, Fortschritt sehen
- **↶ / ↷** – Undo/Redo (auch Strg+Z / Strg+Y)
- **Beenden** – speichern und Server stoppen

### Spalten

Typische Startspalten: Brainstorm, Backlog, Als Nächstes, Umgesetzt (Namen können abweichen).

- **+ Spalte** – Titel, Hinweis, Farbe, optional als Erledigt-Spalte
- **⠿** – Spalte verschieben · Bearbeiten · **🗑** löschen (Karten umlagern; ≥1 Spalte bleibt)

### Karten

| Aktion | So geht’s |
|--------|-----------|
| Neue Idee | **+ Idee** → Text → **Anlegen & platzieren** → Spalte/Karte |
| Verschieben | Ziehen (auch auf andere Karten) |
| Bearbeiten | Doppelklick oder ✎ |
| Löschen | Auf der Karte / im Dialog (optional Anhänge & Flipchart mitlöschen) |
| Tastatur | `N` neue Idee, `Esc` Platzieren/Flipchart abbrechen |

Im Editor:

- Titel, Notizen, Farbe, Spalte
- **Checklisten** – Checkpoint einfügen, per Klick abhaken
- **Fällig am** + optional **Wiederholung** (täglich / wöchentlich / monatlich)
- **Milestone** zuweisen
- **Anhänge** – Dateien (max. 40 MB), liegen unter `attachments/`
- **⧉ Kopieren** – in ein anderes Board (Manager muss laufen; Anhänge & Flipchart können mit)
- Bei kopierten Karten: Link zum Original möglich

### Flipcharts

- Toolbar **Flipchart** = globales Whiteboard  
- Button auf der Karte = Flipchart nur zu dieser Karte  
- Dateien: `*-flipchart.json` bzw. `flipcharts/<karten-id>.json`  
- Braucht einmalig Netz für die Excalidraw-Bibliothek (CDN)

### Themes & Sprache

**Einstellungen:** Hintergrund, Akzent, Winkel, Lichtflecken, Schrift, Sprache (DE/EN/auto). Presets verfügbar.

### Export

- JSON, Excel (XLSX), Word (DOCX), LibreOffice (ODT), PDF, PNG  
- **Versionen…** – frühere Stände auflisten und wiederherstellen  
- **Verwaiste Dateien…** – ungenutzte Anhänge/Flipcharts aufräumen  

### Import

- **JSON** – gesamtes Board ersetzen  
- **CSV** – Karten anhängen  

---

## 4. Janamathics

Pfad: `brainstorm/` · Port **8765** · Datei: `janamathics-kanban.json`

Öffnen über Manager, `brainstorm/Kanban oeffnen.bat` oder Desktop-Verknüpfung.

Nach Template-Updates im Kit:

```powershell
python kanban-kit/sync-janamathics.py
```

(JSON, Flipcharts und Anhänge bleiben erhalten.)

---

## 5. Neues Board (CLI)

```powershell
python kanban-kit/new-board.py --name "Mein Spiel"
```

Optionen u. a. `--out`, `--port`, `--force`, `--update`. Details: [../kanban-kit/README.md](../kanban-kit/README.md).

---

## 6. Daten & Backup

| Datei / Ordner | Inhalt |
|----------------|--------|
| `*-kanban.json` | Spalten, Karten, Milestones (Autosave) |
| `*-flipchart.json` | Globales Flipchart |
| `flipcharts/` | Flipcharts pro Karte |
| `attachments/` | Hochgeladene Dateien |
| `versions/` | Automatische Zwischenstände (Keep ~30) |
| `backups/` | Tägliche Zip-Snapshots (Keep ~14) |
| `board.config.json` | Titel, Port, Theme, Dateinamen |

**Manuelles Backup:** gesamten Board-Ordner kopieren.

---

## 7. Häufige Probleme

| Problem | Lösung |
|---------|--------|
| Seite lädt nicht | Starter erneut; Port belegt → `Kanban Server beenden.bat` |
| Änderungen weg | War `file://` – immer `.bat` / Manager nutzen |
| Python nicht gefunden | Installieren und PATH setzen |
| Manager findet Board nicht | Speicherort / Extra-Pfad prüfen |
| Flipchart leer / Fehler | Internet für CDN; Server muss laufen |
| Export schlägt fehl | Board-Server neu starten; `export_lib.py` im Board-Ordner |

---

## 8. Weiterlesen

- [TECHNIK.md](TECHNIK.md) – Architektur & APIs  
- [../README.md](../README.md) – Überblick  
