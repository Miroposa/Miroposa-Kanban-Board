# Anleitung – Miroposa Kanban Board

Schritt für die tägliche Nutzung: Manager starten, Boards bedienen, Daten sichern.

## 1. Erste Schritte

### Manager starten

1. Doppelklick auf `kanban-kit/Kanban Manager oeffnen.bat`
2. Der Browser öffnet den Manager unter http://127.0.0.1:8760/manager.html
3. Optional: Desktop-Verknüpfung **Kanban-Manager** über den Button im Manager anlegen

### Python prüfen

Falls der Start fehlschlägt:

```powershell
python --version
```

Python 3.10 oder neuer muss installiert und im PATH sein.

### Board öffnen – immer über Starter

| Weg | Wann |
|-----|------|
| Manager → Board öffnen | Übersicht über alle Boards |
| `Kanban oeffnen.bat` im Board-Ordner | Direktes Öffnen eines Boards |
| Desktop-Verknüpfung | Schnellzugriff |

Nicht die `.html`-Datei per Doppelklick öffnen. Ohne lokalen Server speichert der Browser nur flüchtig (z. B. im Speicher) – der Stand geht leicht verloren.

---

## 2. Manager-Oberfläche

Im Manager kannst du:

- **Neues Board anlegen** – Name, Speicherort, Icon
- **Boards öffnen** – startet den Board-Server und den Browser
- **Boards löschen** – entfernt den Eintrag (Janamathics ist geschützt)
- **Speicherort** wählen und als Standard speichern
- **Einstellungen** – Hintergrund/Theme, Schrift, Sprache (DE / EN / automatisch)
- **Icon** aus dem Vorrat oder eigene Bilddatei setzen

Standard-Ablage für neue Boards: `Downloads/<board-name>/`.

---

## 3. Board bedienen

### Spalten

Typische Startspalten (Namen können abweichen):

1. **Brainstorm** – freie Ideen  
2. **Backlog** – später / geparkt  
3. **Als Nächstes** – konkrete Prioritäten  
4. **Umgesetzt** – erledigt  

Weitere Aktionen:

- **+ Spalte** – neue Spalte anlegen  
- **⠿** – Spalte verschieben  
- **🗑** – Spalte löschen (Karten werden in eine andere Spalte verschoben; mindestens eine Spalte bleibt)

### Karten

| Aktion | So geht’s |
|--------|-----------|
| Neue Idee | **+ Idee** → Text → **Anlegen & platzieren** → Spalte/Karte anklicken |
| Verschieben | Karte ziehen (auch auf andere Karten) |
| Bearbeiten | Doppelklick oder ✎ |
| Löschen | Auf der Karte oder im Bearbeiten-Dialog |
| Tastatur | `N` = neue Idee, `Esc` = Platzieren abbrechen |

### Notizen, Fälligkeit, Anhänge

Im Karteneditor:

- **Notizen** – längerer Text
- **Fällig am** – Datum setzen; in der Toolbar nach Fälligkeit filtern
- **Anhänge** – Bilder oder Dateien hochladen (liegen im Board-Ordner unter `attachments/`)

### Flipcharts

- **Flipchart** oben in der Toolbar = allgemeines Board-Whiteboard  
- **Flipchart** auf einer Karte = Skizzen nur zu dieser Karte  

Karten-Flipcharts liegen unter `flipcharts/` im Board-Ordner.

### Themes & Sprache

Unter **Einstellungen** im Board (oder im Manager für neue Boards):

- Hintergrundfarben, Akzent, Kreide-Look
- Schriftart
- Sprache: Deutsch, Englisch oder automatisch nach System

### Export

Über das **Export**-Menü (soweit verfügbar):

- JSON  
- Excel  
- Word  
- PDF  
- PNG  

### Karte in ein anderes Board kopieren

Im Karteneditor **⧉ Kopieren** – der Manager muss laufen, damit Ziel-Boards erreichbar sind.

### Reset

**Reset** stellt den Startinhalt (Seed) des Boards wieder her. Bestehende Karten gehen dabei verloren – nur nutzen, wenn du wirklich neu anfangen willst.

---

## 4. Janamathics (Beispielboard)

Pfad: `brainstorm/`  
Port: **8765**  
Datei: `brainstorm/janamathics-kanban.json`

Öffnen:

- Manager → Janamathics  
- oder `brainstorm/Kanban oeffnen.bat`  
- oder Desktop-Verknüpfung **Janamathics Kanban**

Autosave schreibt bei jeder Änderung in die JSON-Datei. Oben erscheint z. B. `✓ … · Datei: janamathics-kanban.json`.

---

## 5. Neues Board (CLI, optional)

```powershell
python kanban-kit/new-board.py --name "Mein Spiel"
```

Danach erscheint das Board im Manager (je nach Speicherort). Details: [../kanban-kit/README.md](../kanban-kit/README.md).

---

## 6. Daten & Backup

Pro Board typischerweise:

| Datei / Ordner | Inhalt |
|----------------|--------|
| `*-kanban.json` | Spalten und Karten (Autosave) |
| `*-flipchart.json` | Globales Flipchart |
| `flipcharts/` | Flipcharts pro Karte |
| `attachments/` | Hochgeladene Dateien |
| `board.config.json` | Titel, Port, Theme, Dateinamen |

**Backup:** Board-Ordner komplett kopieren (inkl. JSON, Flipcharts, Anhänge).

---

## 7. Häufige Probleme

| Problem | Lösung |
|---------|--------|
| Seite lädt nicht / Fehler | Starter erneut ausführen; Port evtl. noch belegt – `.bat` beendet den alten Prozess oft selbst |
| Änderungen weg | Board war über `file://` geöffnet – immer `.bat` / Manager nutzen |
| Python nicht gefunden | Python installieren und „Add to PATH“ aktivieren |
| Manager findet Board nicht | Speicherort prüfen; Extra-Pfad im Manager bzw. Registry |
| Export schlägt fehl | Siehe Abhängigkeiten in [TECHNIK.md](TECHNIK.md) |

Server beenden: Fenster mit dem Server schließen oder im Terminal `Strg+C`.

---

## 8. Weiterlesen

- [TECHNIK.md](TECHNIK.md) – wie Server, APIs und Dateien zusammenspielen  
- [../README.md](../README.md) – Projektüberblick  
