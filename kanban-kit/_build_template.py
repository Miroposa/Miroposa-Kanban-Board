# -*- coding: utf-8 -*-
"""Einmalig: Janamathics-HTML → parametrisierte Vorlage. Wird vom Kit nicht zur Laufzeit gebraucht."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT.parent / "brainstorm" / "janamathics-kanban.html"
OUT = ROOT / "template" / "board.html"


def main() -> None:
    text = SRC.read_text(encoding="utf-8")

    text = text.replace("Janamathics – Kanban &amp; Brainstorm", "__BOARD_TITLE__")
    text = text.replace("Janamathics – Kanban & Brainstorm", "__BOARD_TITLE__")

    text = text.replace("janamathics-kanban-v1", "__STORAGE_KEY__")
    text = text.replace("janamathics-kanban-handles", "__FILE_HANDLE_DB__")
    text = text.replace("janamathics-kanban.json", "__BOARD_JSON__")
    text = text.replace("janamathics-flipchart.json", "__FLIPCHART_JSON__")
    text = text.replace("janamathics-flipchart-v1:", "__FLIPCHART_LS_PREFIX__")
    text = text.replace("janamathics-kanban", "__BOARD_SOURCE__")

    text = text.replace(
        "Speicherung: <code>docs/brainstorm/__BOARD_JSON__</code>",
        "Speicherung: <code>__BOARD_DIR__/__BOARD_JSON__</code>",
    )
    text = text.replace("Was schon im Spiel steckt", "Was schon fertig ist")

    text = text.replace(
        "⚠ HTML direkt geöffnet – Speichern ist unzuverlässig. Bitte „Janamathics Kanban“ / BAT nutzen.",
        "⚠ HTML direkt geöffnet – Speichern ist unzuverlässig. Bitte „Kanban öffnen.bat“ nutzen.",
    )
    text = text.replace(
        "Bitte das Board über die Desktop-Verknüpfung „Janamathics Kanban“ öffnen.\n\n"
        + "Nur dann wird zuverlässig in die Datei gespeichert:\n"
        + "docs/brainstorm/__BOARD_JSON__",
        "Bitte das Board über „Kanban oeffnen.bat“ (oder die Desktop-Verknüpfung) öffnen.\n\n"
        + "Nur dann wird zuverlässig in die Datei gespeichert:\n"
        + "__BOARD_DIR__/__BOARD_JSON__",
    )

    new_seed = """const SEED_CARDS = [
      { id: "c1", column: "brainstorm", title: "Willkommen – erste Idee notieren", notes: "Diese Karte kannst du löschen oder umbenennen." },
    ];"""
    text, n = re.subn(r"const SEED_CARDS = \[.*?\];", new_seed, text, count=1, flags=re.S)
    if n != 1:
        raise SystemExit(f"SEED_CARDS ersetzen fehlgeschlagen (n={n})")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    (OUT.parent / "flipcharts").mkdir(exist_ok=True)
    OUT.write_text(text, encoding="utf-8")

    left = "janamathics" in text.lower()
    print(f"geschrieben: {OUT}")
    print(f"janamathics-Reste: {left}")
    for key in (
        "__BOARD_TITLE__",
        "__STORAGE_KEY__",
        "__BOARD_JSON__",
        "__FLIPCHART_JSON__",
        "__BOARD_DIR__",
        "__BOARD_SOURCE__",
    ):
        print(f"  {key}: {text.count(key)}")


if __name__ == "__main__":
    main()
