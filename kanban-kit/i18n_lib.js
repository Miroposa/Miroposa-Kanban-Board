/* i18n: Deutsch / Englisch + Systemerkennung */
(function (global) {
  const STRINGS = {
    de: {
      "app.title": "Kanban-Manager",
      "app.subtitle": "Lokale Boards anlegen, öffnen und verwalten.",
      "btn.refresh": "Aktualisieren",
      "btn.settings": "Einstellungen",
      "btn.desktopShortcut": "Desktop-Verknüpfung",
      "btn.create": "Board erstellen",
      "btn.open": "Öffnen",
      "btn.delete": "Löschen",
      "btn.icon": "Icon",
      "btn.pickFolder": "Ordner wählen",
      "btn.saveRoot": "Als Standard",
      "btn.pickImage": "Eigenes Bild",
      "btn.clearIcon": "Entfernen",
      "section.newBoard": "Neues Board",
      "section.yourBoards": "Deine Boards",
      "field.projectName": "Projektname",
      "field.slug": "Kurzname (Ordner)",
      "field.port": "Port",
      "field.storage": "Speicherort",
      "field.icon": "Icon (Desktop-Verknüpfung)",
      "ph.projectName": "z. B. Mein Kanban Board",
      "ph.slug": "wird aus dem Namen erzeugt",
      "ph.storage": "Ordner, in dem das Board angelegt wird",
      "ph.icon": "Vorrat wählen oder eigenes Bild…",
      "ph.port": "auto",
      "check.openAfter": "Danach öffnen",
      "check.desktop": "Desktop-Verknüpfung",
      "check.force": "Überschreiben, falls vorhanden",
      "empty.boards": "Noch keine Boards – links eines anlegen.",
      "empty.loading": "Lade Boards…",
      "empty.boardSearch": "Kein Board passt zur Suche.",
      "ph.boardSearch": "Boards suchen (Name, Port, Pfad)…",
      "badge.project": "Projekt",
      "badge.on": "läuft",
      "badge.off": "aus",
      "meta.hintLoading": "Standardordner wird geladen…",
      "path.hint": "Wird angelegt unter: {path}",
      "status.themeSaved": "Hintergrund gespeichert.",
      "status.rootSaved": "Standard-Speicherort gespeichert.",
      "status.shortcutCreated": "Desktop-Verknüpfung erstellt.",
      "status.creating": "Erstelle Board…",
      "status.pickFolder": "Ordnerdialog öffnen…",
      "status.pickImage": "Bildauswahl öffnen…",
      "status.cancelled": "Auswahl abgebrochen.",
      "status.iconSet": "Icon gesetzt.",
      "status.iconOwn": "Eigenes Icon gesetzt.",
      "status.iconCleared": "Icon entfernt.",
      "status.folderSet": "Speicherort gesetzt.",
      "confirm.delete": "Board \"{name}\" wirklich löschen?",
      "err.api": "Manager-API nicht erreichbar. Bitte über „Kanban Manager oeffnen.bat“ starten.",
      "cards": "Karten",
      "settings.title": "Einstellungen",
      "settings.bg1": "Hintergrund 1",
      "settings.bg2": "Hintergrund 2",
      "settings.accent": "Akzent",
      "settings.text": "Text",
      "settings.font": "Schriftart",
      "settings.fontHint": "Gilt für Board/Manager; im Flipchart als Standard-Stiftart.",
      "settings.angle": "Verlaufswinkel",
      "settings.spots": "Lichtflecken",
      "settings.lang": "Sprache",
      "settings.langHint": "„Automatisch“ nutzt die System-/Browsersprache.",
      "settings.reset": "Standard",
      "settings.cancel": "Abbrechen",
      "settings.save": "Speichern",
      "lang.auto": "Automatisch (System)",
      "lang.de": "Deutsch",
      "lang.en": "English",
      "preset.forest": "Waldgrün",
      "preset.ocean": "Ozean",
      "preset.dusk": "Abendrot",
      "preset.slate": "Schiefer",
      "preset.sand": "Sand",
      "preset.night": "Nachtblau",
      "font.comic": "Handschrift",
      "board.subtitle": "Änderungen werden automatisch gespeichert.",
      "board.search": "Karten suchen…",
      "board.colorFilter": "Farbe",
      "board.colorAll": "Alle",
      "board.dueFilter": "Fälligkeit",
      "board.dueOverdue": "Überfällig",
      "board.dueToday": "Heute",
      "board.dueWeek": "7 Tage",
      "board.dueNone": "Ohne Datum",
      "board.addIdea": "+ Idee",
      "board.addColumn": "+ Spalte",
      "board.flipchart": "Flipchart",
      "board.export": "Export",
      "board.import": "Import",
      "board.settings": "Einstellungen",
      "board.statusAuto": "✓ Speichert automatisch in Datei",
      "board.placeHint": "Idee angelegt – jetzt auf eine Spalte oder Karte klicken",
      "board.cancelPlace": "Abbrechen (Esc)",
      "board.flipBack": "← Zurück zum Kanban",
      "board.footerSave": "Speicherung",
      "board.saveDate": "Aktuelles Speicherdatum",
      "board.saveStand": "Änderungen werden automatisch gespeichert: Stand",
      "board.undo": "Zurück",
      "board.redo": "Vor",
      "board.dragHere": "Zieh Ideen hierher oder + Idee",
    },
    en: {
      "app.title": "Kanban Manager",
      "app.subtitle": "Create, open, and manage local boards.",
      "btn.refresh": "Refresh",
      "btn.settings": "Settings",
      "btn.desktopShortcut": "Desktop shortcut",
      "btn.create": "Create board",
      "btn.open": "Open",
      "btn.delete": "Delete",
      "btn.icon": "Icon",
      "btn.pickFolder": "Choose folder",
      "btn.saveRoot": "Set as default",
      "btn.pickImage": "Custom image",
      "btn.clearIcon": "Remove",
      "section.newBoard": "New board",
      "section.yourBoards": "Your boards",
      "field.projectName": "Project name",
      "field.slug": "Short name (folder)",
      "field.port": "Port",
      "field.storage": "Storage location",
      "field.icon": "Icon (desktop shortcut)",
      "ph.projectName": "e.g. My Kanban Board",
      "ph.slug": "generated from the name",
      "ph.storage": "Folder where the board will be created",
      "ph.icon": "Pick from library or your own image…",
      "ph.port": "auto",
      "check.openAfter": "Open afterwards",
      "check.desktop": "Desktop shortcut",
      "check.force": "Overwrite if it exists",
      "empty.boards": "No boards yet – create one on the left.",
      "empty.loading": "Loading boards…",
      "empty.boardSearch": "No board matches your search.",
      "ph.boardSearch": "Search boards (name, port, path)…",
      "badge.project": "Project",
      "badge.on": "running",
      "badge.off": "off",
      "meta.hintLoading": "Loading default folder…",
      "path.hint": "Will be created at: {path}",
      "status.themeSaved": "Background saved.",
      "status.rootSaved": "Default storage location saved.",
      "status.shortcutCreated": "Desktop shortcut created.",
      "status.creating": "Creating board…",
      "status.pickFolder": "Opening folder dialog…",
      "status.pickImage": "Opening image picker…",
      "status.cancelled": "Selection cancelled.",
      "status.iconSet": "Icon set.",
      "status.iconOwn": "Custom icon set.",
      "status.iconCleared": "Icon removed.",
      "status.folderSet": "Storage location set.",
      "confirm.delete": "Really delete board \"{name}\"?",
      "err.api": "Manager API unreachable. Please start via “Kanban Manager oeffnen.bat”.",
      "cards": "cards",
      "settings.title": "Settings",
      "settings.bg1": "Background 1",
      "settings.bg2": "Background 2",
      "settings.accent": "Accent",
      "settings.text": "Text",
      "settings.font": "Font",
      "settings.fontHint": "Applies to board/manager; used as default pen style in the flipchart.",
      "settings.angle": "Gradient angle",
      "settings.spots": "Light spots",
      "settings.lang": "Language",
      "settings.langHint": "“Automatic” follows your system/browser language.",
      "settings.reset": "Defaults",
      "settings.cancel": "Cancel",
      "settings.save": "Save",
      "lang.auto": "Automatic (system)",
      "lang.de": "Deutsch",
      "lang.en": "English",
      "preset.forest": "Forest",
      "preset.ocean": "Ocean",
      "preset.dusk": "Dusk",
      "preset.slate": "Slate",
      "preset.sand": "Sand",
      "preset.night": "Night blue",
      "font.comic": "Handwriting",
      "board.subtitle": "Changes are saved automatically.",
      "board.search": "Search cards…",
      "board.colorFilter": "Color",
      "board.colorAll": "All",
      "board.dueFilter": "Due date",
      "board.dueOverdue": "Overdue",
      "board.dueToday": "Today",
      "board.dueWeek": "7 days",
      "board.dueNone": "No date",
      "board.addIdea": "+ Idea",
      "board.addColumn": "+ Column",
      "board.flipchart": "Flipchart",
      "board.export": "Export",
      "board.import": "Import",
      "board.settings": "Settings",
      "board.statusAuto": "✓ Saving automatically to file",
      "board.placeHint": "Idea created – now click a column or card",
      "board.cancelPlace": "Cancel (Esc)",
      "board.flipBack": "← Back to Kanban",
      "board.footerSave": "Storage",
      "board.saveDate": "Last saved",
      "board.saveStand": "Changes are saved automatically: as of",
      "board.undo": "Undo",
      "board.redo": "Redo",
      "board.dragHere": "Drag ideas here or + Idea",
    },
  };

  let currentLang = "de";

  function detectSystemLang() {
    const list = [];
    try {
      if (Array.isArray(navigator.languages)) list.push(...navigator.languages);
      if (navigator.language) list.push(navigator.language);
    } catch {
      /* ignore */
    }
    for (const raw of list) {
      const l = String(raw || "").toLowerCase();
      if (l.startsWith("de")) return "de";
      if (l.startsWith("en")) return "en";
    }
    return "en";
  }

  function normalizeLangMode(value) {
    const v = String(value || "auto").trim().toLowerCase();
    if (v === "de" || v === "en" || v === "auto") return v;
    return "auto";
  }

  function resolveLang(mode) {
    const m = normalizeLangMode(mode);
    if (m === "auto") return detectSystemLang();
    return m;
  }

  function setLang(mode) {
    currentLang = resolveLang(mode);
    try {
      document.documentElement.lang = currentLang;
    } catch {
      /* ignore */
    }
    return currentLang;
  }

  function getLang() {
    return currentLang;
  }

  function t(key, vars) {
    const pack = STRINGS[currentLang] || STRINGS.en;
    let s = pack[key] || (STRINGS.de[key] || key);
    if (vars && typeof vars === "object") {
      Object.keys(vars).forEach((k) => {
        s = s.replace(new RegExp("\\{" + k + "\\}", "g"), String(vars[k]));
      });
    }
    return s;
  }

  function applyToDom(root) {
    const scope = root || document;
    scope.querySelectorAll("[data-i18n]").forEach((el) => {
      const key = el.getAttribute("data-i18n");
      if (!key) return;
      el.textContent = t(key);
    });
    scope.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
      const key = el.getAttribute("data-i18n-placeholder");
      if (!key) return;
      el.setAttribute("placeholder", t(key));
    });
    scope.querySelectorAll("[data-i18n-title]").forEach((el) => {
      const key = el.getAttribute("data-i18n-title");
      if (!key) return;
      el.setAttribute("title", t(key));
    });
    const titleEl = document.querySelector("title[data-i18n]");
    if (titleEl) titleEl.textContent = t(titleEl.getAttribute("data-i18n"));
  }

  function excalidrawLangCode() {
    return currentLang === "de" ? "de-DE" : "en";
  }

  global.KanbanI18n = {
    STRINGS: STRINGS,
    detectSystemLang: detectSystemLang,
    normalizeLangMode: normalizeLangMode,
    resolveLang: resolveLang,
    setLang: setLang,
    getLang: getLang,
    t: t,
    applyToDom: applyToDom,
    excalidrawLangCode: excalidrawLangCode,
  };
})(window);
