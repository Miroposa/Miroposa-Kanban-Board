# Technikdokument – Miroposa Kanban Board

Dieses Dokument beschreibt, wie die Anwendung architektonisch aufgebaut ist und wie Daten zwischen Browser, lokalen Servern und Dateien fließen.

## 1. Ziel und Randbedingungen

- **Lokal only:** Kein Cloud-Backend; alles unter `127.0.0.1`
- **Datei = Wahrheit:** Board-Zustand liegt in JSON-Dateien auf der Festplatte
- **Zwei Server-Rollen:**
  1. **Manager** (`manager_server.py`) – Boards verwalten und starten
  2. **Board-Server** (`kanban_server.py`) – ein Board bedienen und speichern
- **Stack:** Python-Standardbibliothek (`ThreadingHTTPServer`) + statische HTML/JS/CSS im Browser
- **Zielplattform:** Windows (Starter als `.bat` / `.ps1`, Desktop-`.lnk`)

---

## 2. Gesamtarchitektur

```text
┌─────────────────────┐     startet      ┌──────────────────────────┐
│  Manager (8760)     │ ───────────────► │  Board-Server (z.B. 8765)│
│  manager_server.py  │                  │  kanban_server.py        │
│  manager.html       │                  │  *-kanban.html           │
└─────────┬───────────┘                  └────────────┬─────────────┘
          │                                           │
          │ manager-registry.json                     │ PUT JSON
          │ icons/, template/                         ▼
          ▼                              ┌──────────────────────────┐
   new-board.py                          │  Board-Ordner            │
   (Kopie aus template/)                 │  *.json, flipcharts/,    │
                                         │  attachments/, config    │
                                         └──────────────────────────┘
```

1. Der Manager listet bekannte Boards, legt neue aus der Vorlage an und startet Board-Prozesse.
2. Jedes Board hat einen eigenen Port und einen eigenen Prozess.
3. Die Browser-UI lädt die HTML-Seite vom Board-Server und speichert Änderungen per HTTP (`PUT`/`POST`) zurück in Dateien.

---

## 3. Projektstruktur (relevant)

| Pfad | Rolle |
|------|--------|
| `kanban-kit/manager_server.py` | Manager-HTTP-Server, Port **8760** |
| `kanban-kit/manager.html` | Manager-UI |
| `kanban-kit/new-board.py` | Board aus Vorlage erzeugen (CLI + Bibliothek) |
| `kanban-kit/template/` | Vorlage: HTML, Server, Seed-JSON, Starter |
| `kanban-kit/theme_lib.*`, `i18n_lib.js`, `theme_shared.css` | Gemeinsame Libs (eine Quelle) |
| `kanban-kit/sync-janamathics.py` | Template → `brainstorm/` synchronisieren |
| `brainstorm/` | Produktiv-/Beispielboard „Janamathics“ |
| `boards/` | Optionaler Repo-Ordner für Boards |

Shared Libs liegen im Kit-Root und werden beim Anlegen eines Boards mitkopiert (nicht doppelt unter `template/` gepflegt).

---

## 4. Board-Konfiguration

Jedes Board hat eine `board.config.json`, z. B.:

```json
{
  "title": "Janamathics – Kanban & Brainstorm",
  "slug": "janamathics",
  "boardHtml": "janamathics-kanban.html",
  "boardJson": "janamathics-kanban.json",
  "flipchartJson": "janamathics-flipchart.json",
  "port": 8765,
  "source": "janamathics-kanban",
  "theme": { "bg": "#1f3d2f", "accent": "#e2a53a", "lang": "auto", "...": "..." }
}
```

Der Board-Server liest diese Datei beim Start und leitet daraus Dateipfade, Port und Theme ab.

### Board-Datenmodell (Kanban-JSON)

Vereinfachte Struktur der Autosave-Datei (`*-kanban.json`):

```json
{
  "columns": [
    { "id": "brainstorm", "title": "Brainstorm", "hint": "...", "color": "yellow" }
  ],
  "cards": [
    {
      "id": "c1",
      "column": "brainstorm",
      "title": "Erste Idee",
      "notes": "...",
      "due": null,
      "attachments": []
    }
  ]
}
```

Fehlt die Datei beim ersten Start, schreibt der Server einen **Seed** (Standardspalten + Willkommenskarte).

### Flipcharts

- Format: **Excalidraw**-kompatibles JSON (`type`, `elements`, `appState`, `files`, …)
- Global: Datei aus `flipchartJson` in der Config
- Pro Karte: `flipcharts/<cardId>.json`

---

## 5. Board-Server (`kanban_server.py`)

### Start

```text
python kanban_server.py [port]
```

Ohne Argument: Port aus `board.config.json`.  
Bindet ausschließlich an `127.0.0.1`.

Beim Start:

1. Config laden und validieren  
2. Fehlende Daten-/Flipchart-Dateien aus Seed anlegen  
3. Ordner `flipcharts/` und `attachments/` sicherstellen  
4. `ThreadingHTTPServer` starten  

Statische Dateien (HTML, JS, CSS, Anhänge) werden aus dem Board-Ordner ausgeliefert (`SimpleHTTPRequestHandler` mit `directory=Board-Root`).

### Wichtige HTTP-Endpunkte

| Methode | Pfad | Zweck |
|---------|------|--------|
| `GET` | `/` oder `/index.html` | Redirect auf `boardHtml` |
| `GET`/`PUT` | `/api/board` bzw. `/{boardJson}` | Board-JSON lesen / speichern |
| `GET`/`PUT` | `/api/flipchart` bzw. `/{flipchartJson}` | Globales Flipchart |
| `GET`/`PUT` | `/flipcharts/<id>.json` | Karten-Flipchart |
| `GET` | `/api/flipchart-index` | IDs/Counts befüllter Flipcharts |
| `GET`/`POST` | `/api/theme` | Theme lesen / in Config schreiben |
| `POST`/`PUT` | `/api/attachments` | Anhang hochladen (JSON+Base64 oder Binär) |
| `DELETE` | `/api/attachments` | Anhang löschen |
| `POST` | `/api/export` | Export erzeugen (`export_lib`) |

Autosave in der UI: bei Änderungen sendet das Frontend typischerweise ein `PUT` mit dem kompletten Board-Objekt; der Server schreibt atomar die JSON-Datei (Overwrite der gesamten Datei).

### Anhänge

- Maximale Größe: **40 MB**
- Speicherung unter `attachments/` als `a_<uuid>_<safeName>`
- Metadaten (id, name, url, mime, size, addedAt) gehen zurück an die UI und werden in der Karte referenziert
- Pfadauflösung verhindert Directory-Traversal (`relative_to` auf dem Attachments-Ordner)

### Export

`export_lib.build_export(format, state, title)` erzeugt Bytes + Dateiname + MIME-Type.  
Fehlt die Lib oder eine Abhängigkeit, schlägt der Export mit einer klaren Fehlermeldung fehl.

---

## 6. Manager-Server (`manager_server.py`)

### Start

Port standardmäßig **8760**. Liefert `manager.html` und eine JSON-API.

### Aufgaben

- Boards scannen (Standard-Root, Extra-Pfade, bekanntes Janamathics unter `brainstorm/`)
- Neues Board erzeugen über `new-board.py` (`create_board`)
- Board-Prozess starten/überwachen (`subprocess`), Port belegen
- Theme-/Speicherort-Einstellungen in `manager-registry.json` persistieren
- Icons aus `icons/catalog.json` bzw. Upload
- Karten zwischen Boards kopieren (`/api/cards/copy`)
- Ordner-/Bilddialoge (Windows-Picker) und Desktop-Verknüpfung anlegen

### Auszug API

| Methode | Pfad | Zweck |
|---------|------|--------|
| `GET` | `/api/boards` | Board-Liste |
| `POST` | `/api/boards` | Neues Board anlegen |
| `POST` | `/api/boards/open` | Board-Server starten + URL |
| `POST` | `/api/boards/delete` | Board entfernen |
| `POST` | `/api/cards/copy` | Karte in Zielboard schreiben |
| `GET`/`POST` | Settings-Endpunkte | Root, Theme, Shortcut, … |

Laufende Board-Prozesse werden intern in einem Dict gehalten; Öffnen startet ggf. einen neuen `kanban_server.py`-Prozess im jeweiligen Board-Ordner.

---

## 7. Board anlegen (`new-board.py`)

Ablauf grob:

1. Namen → **Slug** (`slugify`, Umlaute → ae/oe/ue)  
2. Freien Port wählen (`collect_used_ports` / `next_free_port`)  
3. Zielordner anlegen (Standard: `~/Downloads/<slug>/`)  
4. Dateien aus `template/` kopieren und Platzhalter ersetzen (`{{TITLE}}`, Port, Dateinamen, …)  
5. Shared Libs aus dem Kit-Root mitkopieren  
6. `board.config.json` schreiben  

Das Ergebnis ist ein **autarkes** Board-Verzeichnis: eigener Server, eigene Starter-Skripte, eigene Daten.

---

## 8. Frontend (Board-HTML)

Die Board-UI (`template/board.html` bzw. `*-kanban.html`) ist eine Single-Page-App ohne Build-Step:

- Zustand in JavaScript (Spalten, Karten, UI-Modi)
- Persistenz über `fetch` gegen die Board-API
- Themes über CSS-Variablen / `theme_lib.js` und `theme_shared.css`
- Texte über `i18n_lib.js` (DE/EN)
- Flipchart-Einbindung (Excalidraw-kompatibel)

Der Manager (`manager.html`) spricht nur mit Port 8760.

---

## 9. Starter-Skripte (Windows)

`Kanban oeffnen.bat` / `.ps1` bzw. Manager-Starter typischerweise:

1. Prüfen, ob der Port schon belegt ist  
2. Alten Prozess ggf. beenden  
3. `python …_server.py` starten (Log-Datei möglich)  
4. Browser mit der lokalen URL öffnen  

So ist sichergestellt, dass immer der aktuelle Server (mit Schreib-API) läuft – nicht nur eine statische HTML-Datei.

---

## 10. Sync Template → Janamathics

```text
python kanban-kit/sync-janamathics.py
```

Kopiert UI, Server und Libs aus dem Kit nach `brainstorm/`, lässt Board-JSON, Flipcharts und Anhänge unberührt. So bleibt Janamathics feature-seitig am Template ausgerichtet, ohne Datenverlust.

---

## 11. Sicherheit (bewusst lokal)

- Nur Loopback (`127.0.0.1`) – kein LAN-/Internet-Listener
- Keine Authentifizierung (reicht für Einzelplatz)
- CORS auf `*` für lokale Fetch-Aufrufe
- Dateinamen von Uploads werden bereinigt; Speichern nur unter `attachments/`

Nicht für öffentliches Hosting ausgelegt.

---

## 12. Erweiterungen / Pflege

| Änderung | Wo |
|----------|-----|
| UI/Logik aller neuen Boards | `kanban-kit/template/board.html` |
| Board-API | `kanban-kit/template/kanban_server.py` |
| Manager-UI/API | `manager.html` / `manager_server.py` |
| Theme/i18n | Kit-Root-Libs, dann Boards neu anlegen oder sync |
| Janamathics angleichen | `sync-janamathics.py` |
| Icons erzeugen | `python kanban-kit/generate_icons.py` |

Nach Template-Änderungen bestehende Boards nicht automatisch updaten – nur neue Boards oder gezielter Sync (wie bei Janamathics).

---

## 13. Abhängigkeiten

**Pflicht:** Python 3.10+ (Standardbibliothek reicht für Server und Kernfunktion).

**Optional** (Export / erweiterte Formate): je nach Inhalt von `export_lib.py` (z. B. Bibliotheken für Office/PDF). Fehlen sie, bleibt das Board nutzbar; nur betroffene Exportwege melden Fehler.

---

## 14. Verwandte Doku

- [ANLEITUNG.md](ANLEITUNG.md) – Bedienung  
- [../README.md](../README.md) – Überblick  
- [../kanban-kit/README.md](../kanban-kit/README.md) – Kit & Manager  
- [../brainstorm/README.md](../brainstorm/README.md) – Janamathics  
