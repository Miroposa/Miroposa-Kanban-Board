/* Gemeinsame Theme-Logik für Manager und Boards */
(function (global) {
  const FONT_OPTIONS = [
    {
      id: "segoe",
      label: "Segoe UI",
      css: '"Segoe UI", Candara, Calibri, "Trebuchet MS", sans-serif',
      excalidraw: 2,
    },
    {
      id: "verdana",
      label: "Verdana",
      css: 'Verdana, Geneva, Tahoma, sans-serif',
      excalidraw: 2,
    },
    {
      id: "trebuchet",
      label: "Trebuchet",
      css: '"Trebuchet MS", "Lucida Grande", Helvetica, sans-serif',
      excalidraw: 2,
    },
    {
      id: "georgia",
      label: "Georgia",
      css: 'Georgia, "Times New Roman", Times, serif',
      excalidraw: 1,
    },
    {
      id: "garamond",
      label: "Garamond",
      css: 'Garamond, "Palatino Linotype", Palatino, serif',
      excalidraw: 1,
    },
    {
      id: "comic",
      label: "Handschrift",
      css: '"Segoe Print", "Comic Sans MS", cursive',
      excalidraw: 1,
    },
    {
      id: "consolas",
      label: "Consolas",
      css: 'Consolas, "Courier New", monospace',
      excalidraw: 3,
    },
    {
      id: "arial",
      label: "Arial",
      css: 'Arial, Helvetica, sans-serif',
      excalidraw: 2,
    },
  ];

  const DEFAULT_THEME = {
    bg: "#1f3d2f",
    bg2: "#274c3a",
    accent: "#e2a53a",
    chalk: "#e8f0e6",
    angle: 160,
    spots: true,
    font: "segoe",
    lang: "auto",
  };

  const THEME_PRESETS = [
    {
      id: "forest",
      label: "Waldgrün",
      theme: { bg: "#1f3d2f", bg2: "#274c3a", accent: "#e2a53a", chalk: "#e8f0e6", angle: 160, spots: true },
    },
    {
      id: "ocean",
      label: "Ozean",
      theme: { bg: "#1a3348", bg2: "#234a63", accent: "#5eb3c4", chalk: "#e6f2f5", angle: 150, spots: true },
    },
    {
      id: "dusk",
      label: "Abendrot",
      theme: { bg: "#3a2428", bg2: "#5a3038", accent: "#e08a5a", chalk: "#f5ebe8", angle: 145, spots: true },
    },
    {
      id: "slate",
      label: "Schiefer",
      theme: { bg: "#2a3038", bg2: "#3a4450", accent: "#c4a574", chalk: "#eef1f4", angle: 170, spots: true },
    },
    {
      id: "sand",
      label: "Sand",
      theme: { bg: "#3d3428", bg2: "#564736", accent: "#d4a84b", chalk: "#f7f1e6", angle: 155, spots: true },
    },
    {
      id: "night",
      label: "Nachtblau",
      theme: { bg: "#141c33", bg2: "#1e2a4a", accent: "#7b9cff", chalk: "#e8ecf8", angle: 165, spots: true },
    },
  ];

  function asHex(value, fallback) {
    if (typeof value !== "string") return fallback;
    let s = value.trim();
    if (s.length === 4 && s[0] === "#") {
      s = "#" + s[1] + s[1] + s[2] + s[2] + s[3] + s[3];
    }
    if (/^#[0-9a-fA-F]{6}$/.test(s)) return s.toLowerCase();
    return fallback;
  }

  function getFontOption(fontId) {
    return FONT_OPTIONS.find((f) => f.id === fontId) || FONT_OPTIONS[0];
  }

  function normalizeTheme(raw) {
    const data = raw && typeof raw === "object" ? raw : {};
    let angle = parseInt(data.angle, 10);
    if (Number.isNaN(angle)) angle = DEFAULT_THEME.angle;
    angle = Math.max(0, Math.min(360, angle));
    let spots = data.spots;
    if (typeof spots === "string") {
      spots = ["1", "true", "yes", "on"].includes(spots.trim().toLowerCase());
    } else {
      spots = spots == null ? DEFAULT_THEME.spots : !!spots;
    }
    const fontId = typeof data.font === "string" ? data.font.trim() : DEFAULT_THEME.font;
    const font = getFontOption(fontId).id;
    let lang = typeof data.lang === "string" ? data.lang.trim().toLowerCase() : DEFAULT_THEME.lang;
    if (lang !== "auto" && lang !== "de" && lang !== "en") lang = DEFAULT_THEME.lang;
    return {
      bg: asHex(data.bg, DEFAULT_THEME.bg),
      bg2: asHex(data.bg2, DEFAULT_THEME.bg2),
      accent: asHex(data.accent, DEFAULT_THEME.accent),
      chalk: asHex(data.chalk, DEFAULT_THEME.chalk),
      angle: angle,
      spots: spots,
      font: font,
      lang: lang,
    };
  }

  function applyTheme(theme, rootEl) {
    const t = normalizeTheme(theme);
    const root = rootEl || document.documentElement;
    const font = getFontOption(t.font);
    root.style.setProperty("--bg", t.bg);
    root.style.setProperty("--bg-2", t.bg2);
    root.style.setProperty("--accent", t.accent);
    root.style.setProperty("--chalk", t.chalk);
    root.style.setProperty("--bg-angle", t.angle + "deg");
    root.style.setProperty("--bg-spots", t.spots ? "1" : "0");
    root.style.setProperty("--font", font.css);
    root.classList.toggle("theme-no-spots", !t.spots);
    if (document.body) document.body.style.fontFamily = font.css;
    return t;
  }

  function getExcalidrawFontFamily(theme) {
    const t = normalizeTheme(theme);
    return getFontOption(t.font).excalidraw;
  }

  function settingsDialogHtml() {
    const fontOptions = FONT_OPTIONS.map((f) => {
      const label =
        f.id === "comic" && global.KanbanI18n
          ? global.KanbanI18n.t("font.comic")
          : f.label;
      return (
        '<option value="' +
        f.id +
        '" style="font-family:' +
        f.css.replace(/"/g, "&quot;") +
        '">' +
        label +
        "</option>"
      );
    }).join("");
    return (
      '<form method="dialog" class="dialog-body theme-form" id="theme-form">' +
      '<h3 data-i18n="settings.title">Einstellungen</h3>' +
      '<div class="theme-presets" id="theme-presets"></div>' +
      '<div class="theme-grid">' +
      '<label><span data-i18n="settings.bg1">Hintergrund 1</span><input type="color" id="theme-bg" /></label>' +
      '<label><span data-i18n="settings.bg2">Hintergrund 2</span><input type="color" id="theme-bg2" /></label>' +
      '<label><span data-i18n="settings.accent">Akzent</span><input type="color" id="theme-accent" /></label>' +
      '<label><span data-i18n="settings.text">Text</span><input type="color" id="theme-chalk" /></label>' +
      "</div>" +
      '<label class="theme-font"><span data-i18n="settings.font">Schriftart</span>' +
      '<select id="theme-font">' +
      fontOptions +
      "</select></label>" +
      '<p class="theme-font-hint" data-i18n="settings.fontHint">Gilt für Board/Manager; im Flipchart als Standard-Stiftart.</p>' +
      '<label class="theme-font"><span data-i18n="settings.lang">Sprache</span>' +
      '<select id="theme-lang">' +
      '<option value="auto" data-i18n="lang.auto">Automatisch (System)</option>' +
      '<option value="de" data-i18n="lang.de">Deutsch</option>' +
      '<option value="en" data-i18n="lang.en">English</option>' +
      "</select></label>" +
      '<p class="theme-font-hint" data-i18n="settings.langHint">„Automatisch“ nutzt die System-/Browsersprache.</p>' +
      '<label class="theme-angle"><span data-i18n="settings.angle">Verlaufswinkel</span>' +
      '<div class="theme-angle-row">' +
      '<input type="range" id="theme-angle" min="0" max="360" step="1" />' +
      '<span id="theme-angle-val">160°</span>' +
      "</div></label>" +
      '<label class="theme-check"><input type="checkbox" id="theme-spots" /> <span data-i18n="settings.spots">Lichtflecken</span></label>' +
      '<div class="dialog-actions">' +
      '<button type="button" class="secondary" id="theme-reset" data-i18n="settings.reset">Standard</button>' +
      '<button type="button" class="secondary" id="theme-cancel" value="cancel" data-i18n="settings.cancel">Abbrechen</button>' +
      '<button type="submit" id="theme-save" value="default" data-i18n="settings.save">Speichern</button>' +
      "</div></form>"
    );
  }

  function localizePresets() {
    const i18n = global.KanbanI18n;
    return THEME_PRESETS.map((p) => ({
      id: p.id,
      label: i18n ? i18n.t("preset." + p.id) : p.label,
      theme: p.theme,
    }));
  }

  function bindThemeDialog(opts) {
    const dialog = opts.dialog;
    const form = dialog.querySelector("#theme-form");
    const presetsEl = dialog.querySelector("#theme-presets");
    const fieldBg = dialog.querySelector("#theme-bg");
    const fieldBg2 = dialog.querySelector("#theme-bg2");
    const fieldAccent = dialog.querySelector("#theme-accent");
    const fieldChalk = dialog.querySelector("#theme-chalk");
    const fieldFont = dialog.querySelector("#theme-font");
    const fieldLang = dialog.querySelector("#theme-lang");
    const fieldAngle = dialog.querySelector("#theme-angle");
    const angleVal = dialog.querySelector("#theme-angle-val");
    const fieldSpots = dialog.querySelector("#theme-spots");
    let draft = normalizeTheme(opts.initial);
    let selectedPreset = "";

    function refreshI18n() {
      if (global.KanbanI18n) {
        global.KanbanI18n.setLang(draft.lang || "auto");
        global.KanbanI18n.applyToDom(dialog);
        // Font option "comic" label
        const comicOpt = fieldFont.querySelector('option[value="comic"]');
        if (comicOpt) comicOpt.textContent = global.KanbanI18n.t("font.comic");
      }
      if (typeof opts.onLangChange === "function") opts.onLangChange(draft.lang || "auto");
      rebuildPresets();
    }

    function fillForm(theme) {
      draft = normalizeTheme(theme);
      fieldBg.value = draft.bg;
      fieldBg2.value = draft.bg2;
      fieldAccent.value = draft.accent;
      fieldChalk.value = draft.chalk;
      fieldFont.value = draft.font;
      fieldFont.style.fontFamily = getFontOption(draft.font).css;
      fieldLang.value = draft.lang || "auto";
      fieldAngle.value = String(draft.angle);
      angleVal.textContent = draft.angle + "°";
      fieldSpots.checked = !!draft.spots;
      refreshI18n();
      syncPresetButtons();
      applyTheme(draft);
      if (typeof opts.onPreview === "function") opts.onPreview(draft);
    }

    function readForm() {
      return normalizeTheme({
        bg: fieldBg.value,
        bg2: fieldBg2.value,
        accent: fieldAccent.value,
        chalk: fieldChalk.value,
        font: fieldFont.value,
        lang: fieldLang.value,
        angle: fieldAngle.value,
        spots: fieldSpots.checked,
      });
    }

    function syncPresetButtons() {
      presetsEl.querySelectorAll(".theme-preset").forEach((btn) => {
        const p = THEME_PRESETS.find((x) => x.id === btn.dataset.id);
        const match =
          p &&
          p.theme.bg === draft.bg &&
          p.theme.bg2 === draft.bg2 &&
          p.theme.accent === draft.accent &&
          p.theme.chalk === draft.chalk &&
          Number(p.theme.angle) === Number(draft.angle) &&
          !!p.theme.spots === !!draft.spots;
        btn.classList.toggle("selected", !!match);
        if (match) selectedPreset = p.id;
      });
    }

    function rebuildPresets() {
      presetsEl.innerHTML = "";
      localizePresets().forEach((p) => {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "theme-preset";
        btn.dataset.id = p.id;
        btn.title = p.label;
        btn.innerHTML =
          '<span class="swatch" style="background:linear-gradient(135deg,' +
          p.theme.bg +
          "," +
          p.theme.bg2 +
          ')"></span><span>' +
          p.label +
          "</span>";
        btn.addEventListener("click", () => {
          selectedPreset = p.id;
          fillForm(Object.assign({}, p.theme, { font: draft.font, lang: draft.lang }));
        });
        presetsEl.appendChild(btn);
      });
      syncPresetButtons();
    }

    function preview() {
      draft = readForm();
      fieldFont.style.fontFamily = getFontOption(draft.font).css;
      selectedPreset = "";
      if (global.KanbanI18n) {
        global.KanbanI18n.setLang(draft.lang || "auto");
        global.KanbanI18n.applyToDom(dialog);
        if (typeof opts.onLangChange === "function") opts.onLangChange(draft.lang || "auto");
      }
      syncPresetButtons();
      applyTheme(draft);
      if (typeof opts.onPreview === "function") opts.onPreview(draft);
    }

    rebuildPresets();

    fieldBg.addEventListener("input", preview);
    fieldBg2.addEventListener("input", preview);
    fieldAccent.addEventListener("input", preview);
    fieldChalk.addEventListener("input", preview);
    fieldFont.addEventListener("change", preview);
    fieldLang.addEventListener("change", () => {
      preview();
      rebuildPresets();
      refreshI18n();
    });
    fieldAngle.addEventListener("input", () => {
      angleVal.textContent = fieldAngle.value + "°";
      preview();
    });
    fieldSpots.addEventListener("change", preview);

    dialog.querySelector("#theme-reset").addEventListener("click", () => {
      selectedPreset = "forest";
      fillForm(DEFAULT_THEME);
    });

    dialog.querySelector("#theme-cancel").addEventListener("click", () => {
      applyTheme(opts.initial);
      if (global.KanbanI18n) {
        global.KanbanI18n.setLang(normalizeTheme(opts.initial).lang || "auto");
        if (typeof opts.onLangChange === "function") {
          opts.onLangChange(normalizeTheme(opts.initial).lang || "auto");
        }
      }
      if (typeof opts.onCancel === "function") opts.onCancel(normalizeTheme(opts.initial));
      dialog.close();
    });

    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const theme = readForm();
      try {
        await opts.onSave(theme);
        opts.initial = theme;
        dialog.close();
      } catch (err) {
        alert(err.message || String(err));
      }
    });

    dialog.addEventListener("close", () => {
      applyTheme(opts.initial);
      if (global.KanbanI18n) {
        global.KanbanI18n.setLang(normalizeTheme(opts.initial).lang || "auto");
        if (typeof opts.onLangChange === "function") {
          opts.onLangChange(normalizeTheme(opts.initial).lang || "auto");
        }
      }
      if (typeof opts.onCancel === "function") opts.onCancel(normalizeTheme(opts.initial));
    });

    return {
      open(initial) {
        opts.initial = normalizeTheme(initial || opts.initial || DEFAULT_THEME);
        fillForm(opts.initial);
        if (typeof dialog.showModal === "function") dialog.showModal();
        else dialog.setAttribute("open", "");
      },
      getDraft: () => draft,
    };
  }

  global.KanbanTheme = {
    DEFAULT_THEME: DEFAULT_THEME,
    THEME_PRESETS: THEME_PRESETS,
    FONT_OPTIONS: FONT_OPTIONS,
    normalizeTheme: normalizeTheme,
    applyTheme: applyTheme,
    getFontOption: getFontOption,
    getExcalidrawFontFamily: getExcalidrawFontFamily,
    settingsDialogHtml: settingsDialogHtml,
    bindThemeDialog: bindThemeDialog,
  };
})(window);
