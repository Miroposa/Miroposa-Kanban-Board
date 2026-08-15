# -*- coding: utf-8 -*-
"""Board-Export als Excel (.xlsx), Word (.docx) und PDF – nur Standardbibliothek."""
from __future__ import annotations

import io
import re
import zipfile
from datetime import datetime
from typing import Any
from xml.sax.saxutils import escape


def _safe_filename(title: str, ext: str) -> str:
    base = str(title or "Kanban")
    base = (
        base.replace("–", "-")
        .replace("—", "-")
        .replace("ä", "ae")
        .replace("ö", "oe")
        .replace("ü", "ue")
        .replace("Ä", "Ae")
        .replace("Ö", "Oe")
        .replace("Ü", "Ue")
        .replace("ß", "ss")
    )
    base = re.sub(r"[^\w.\- ()\[\]]+", " ", base, flags=re.ASCII)
    base = re.sub(r"\s+", " ", base).strip(" ._") or "Kanban"
    # HTTP-Header nur Latin-1/ASCII – Dateiname sicher halten
    base = base.encode("ascii", "ignore").decode("ascii").strip(" ._") or "Kanban"
    return f"{base[:80]}.{ext.lstrip('.')}"


def _flatten_rows(data: dict[str, Any]) -> tuple[list[str], list[list[str]]]:
    columns = [c for c in (data.get("columns") or []) if isinstance(c, dict) and c.get("id")]
    col_title = {str(c["id"]): str(c.get("title") or c["id"]) for c in columns}
    order = {str(c["id"]): i for i, c in enumerate(columns)}
    cards = [c for c in (data.get("cards") or []) if isinstance(c, dict)]
    cards.sort(
        key=lambda c: (
            order.get(str(c.get("column") or ""), 999),
            str(c.get("dueDate") or "9999"),
            str(c.get("title") or "").lower(),
        )
    )
    headers = ["Spalte", "Titel", "Notizen", "Fällig am", "Wiederholung", "Milestone", "Erledigt am", "Farbe", "Anhänge", "Erstellt"]
    rows: list[list[str]] = []
    milestones = {
        str(m["id"]): str(m.get("title") or m["id"])
        for m in (data.get("milestones") or [])
        if isinstance(m, dict) and m.get("id")
    }
    for card in cards:
        atts = card.get("attachments") or []
        att_names = []
        if isinstance(atts, list):
            for a in atts:
                if isinstance(a, dict) and a.get("name"):
                    att_names.append(str(a["name"]))
        rec = card.get("recurrence") if isinstance(card.get("recurrence"), dict) else {}
        rows.append(
            [
                col_title.get(str(card.get("column") or ""), str(card.get("column") or "")),
                str(card.get("title") or ""),
                str(card.get("notes") or ""),
                str(card.get("dueDate") or ""),
                str((rec or {}).get("every") or ""),
                milestones.get(str(card.get("milestoneId") or ""), str(card.get("milestoneId") or "")),
                str(card.get("completedAt") or ""),
                str(card.get("color") or "none"),
                ", ".join(att_names),
                str(card.get("createdAt") or ""),
            ]
        )
    return headers, rows


def export_xlsx(data: dict[str, Any], title: str = "Kanban") -> tuple[bytes, str, str]:
    headers, rows = _flatten_rows(data)
    shared = [headers] + rows
    # shared strings
    sst_items = []
    for row in shared:
        for cell in row:
            sst_items.append(str(cell))
    # unique map for shared strings
    uniq: list[str] = []
    index: dict[str, int] = {}
    for s in sst_items:
        if s not in index:
            index[s] = len(uniq)
            uniq.append(s)

    def si(text: str) -> int:
        return index[text]

    sheet_rows = []
    for r_i, row in enumerate(shared, start=1):
        cells = []
        for c_i, val in enumerate(row):
            col = ""
            n = c_i
            while True:
                col = chr(ord("A") + (n % 26)) + col
                n = n // 26 - 1
                if n < 0:
                    break
            cells.append(f'<c r="{col}{r_i}" t="s"><v>{si(str(val))}</v></c>')
        sheet_rows.append(f'<row r="{r_i}">' + "".join(cells) + "</row>")

    sst_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        f'count="{len(sst_items)}" uniqueCount="{len(uniq)}">'
        + "".join(f"<si><t>{escape(s)}</t></si>" for s in uniq)
        + "</sst>"
    )
    sheet_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        "<sheetData>"
        + "".join(sheet_rows)
        + "</sheetData></worksheet>"
    )
    workbook_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<sheets><sheet name="Kanban" sheetId="1" r:id="rId1"/></sheets></workbook>'
    )
    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        '<Override PartName="/xl/sharedStrings.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/>'
        "</Types>"
    )
    rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
        "</Relationships>"
    )
    wb_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
        '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings" Target="sharedStrings.xml"/>'
        "</Relationships>"
    )

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", rels)
        zf.writestr("xl/workbook.xml", workbook_xml)
        zf.writestr("xl/_rels/workbook.xml.rels", wb_rels)
        zf.writestr("xl/worksheets/sheet1.xml", sheet_xml)
        zf.writestr("xl/sharedStrings.xml", sst_xml)
    return (
        buf.getvalue(),
        _safe_filename(title, "xlsx"),
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


def _row_fields(row: list[str]) -> dict[str, str]:
    """Robuste Zuordnung der Flatten-Zeile (auch bei älteren 7-Spalten-Layouts)."""
    # headers: Spalte, Titel, Notizen, Fällig am, Wiederholung, Milestone, Erledigt am, Farbe, Anhänge, Erstellt
    vals = list(row) + [""] * 10
    return {
        "col": vals[0],
        "title": vals[1],
        "notes": vals[2],
        "due": vals[3],
        "recurrence": vals[4] if len(row) > 7 else "",
        "milestone": vals[5] if len(row) > 7 else "",
        "completed": vals[6] if len(row) > 7 else "",
        "color": vals[7] if len(row) > 7 else vals[4],
        "atts": vals[8] if len(row) > 7 else vals[5],
        "created": vals[9] if len(row) > 7 else vals[6],
    }


def export_docx(data: dict[str, Any], title: str = "Kanban") -> tuple[bytes, str, str]:
    headers, rows = _flatten_rows(data)
    stamp = datetime.now().strftime("%d.%m.%Y %H:%M")

    def p(text: str, bold: bool = False) -> str:
        run = escape(text).replace("\n", "</w:t><w:br/><w:t>")
        rpr = "<w:rPr><w:b/></w:rPr>" if bold else ""
        return f"<w:p><w:r>{rpr}<w:t xml:space=\"preserve\">{run}</w:t></w:r></w:p>"

    body = [p(str(title or "Kanban Board"), bold=True), p(f"Exportiert am {stamp}")]
    body.append(p(""))
    for row in rows:
        f = _row_fields(row)
        body.append(p(f"[{f['col']}] {f['title']}", bold=True))
        if f["due"]:
            body.append(p(f"Fällig: {f['due']}"))
        if f["notes"]:
            body.append(p(f["notes"]))
        meta = []
        if f["recurrence"]:
            meta.append(f"Wiederholung: {f['recurrence']}")
        if f["milestone"]:
            meta.append(f"Ziel: {f['milestone']}")
        if f["completed"]:
            meta.append(f"Erledigt: {f['completed']}")
        if f["color"] and f["color"] != "none":
            meta.append(f"Farbe: {f['color']}")
        if f["atts"]:
            meta.append(f"Dateien: {f['atts']}")
        if f["created"]:
            meta.append(f"Erstellt: {f['created']}")
        if meta:
            body.append(p(" · ".join(meta)))
        body.append(p(""))

    document_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        "<w:body>"
        + "".join(body)
        + "</w:body></w:document>"
    )
    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        "</Types>"
    )
    rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
        "</Relationships>"
    )
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", rels)
        zf.writestr("word/document.xml", document_xml)
    return (
        buf.getvalue(),
        _safe_filename(title, "docx"),
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


def export_odt(data: dict[str, Any], title: str = "Kanban") -> tuple[bytes, str, str]:
    """LibreOffice Writer (.odt) – OpenDocument Text als ZIP."""
    _headers, rows = _flatten_rows(data)
    stamp = datetime.now().strftime("%d.%m.%Y %H:%M")

    def para(text: str, style: str = "Standard") -> str:
        # Zeilenumbrüche als <text:line-break/>
        parts = escape(str(text)).split("\n")
        inner = "<text:line-break/>".join(parts)
        return f'<text:p text:style-name="{style}">{inner}</text:p>'

    body_parts = [
        para(str(title or "Kanban Board"), "Heading"),
        para(f"Exportiert am {stamp}"),
        para(""),
    ]
    for row in rows:
        f = _row_fields(row)
        body_parts.append(para(f"[{f['col']}] {f['title']}", "Heading"))
        if f["due"]:
            body_parts.append(para(f"Fällig: {f['due']}"))
        if f["notes"]:
            body_parts.append(para(f["notes"]))
        meta = []
        if f["recurrence"]:
            meta.append(f"Wiederholung: {f['recurrence']}")
        if f["milestone"]:
            meta.append(f"Ziel: {f['milestone']}")
        if f["completed"]:
            meta.append(f"Erledigt: {f['completed']}")
        if f["color"] and f["color"] != "none":
            meta.append(f"Farbe: {f['color']}")
        if f["atts"]:
            meta.append(f"Dateien: {f['atts']}")
        if f["created"]:
            meta.append(f"Erstellt: {f['created']}")
        if meta:
            body_parts.append(para(" · ".join(meta)))
        body_parts.append(para(""))

    content_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<office:document-content xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
        'xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0" '
        'xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0" '
        'xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0" '
        'office:version="1.2">'
        "<office:automatic-styles>"
        '<style:style style:name="Heading" style:family="paragraph">'
        '<style:text-properties fo:font-weight="bold"/>'
        "</style:style>"
        "</office:automatic-styles>"
        "<office:body><office:text>"
        + "".join(body_parts)
        + "</office:text></office:body></office:document-content>"
    )
    manifest = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<manifest:manifest xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0" manifest:version="1.2">'
        '<manifest:file-entry manifest:full-path="/" manifest:version="1.2" '
        'manifest:media-type="application/vnd.oasis.opendocument.text"/>'
        '<manifest:file-entry manifest:full-path="content.xml" manifest:media-type="text/xml"/>'
        "</manifest:manifest>"
    )
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        # mimetype must be first and stored uncompressed
        zf.writestr(
            "mimetype",
            "application/vnd.oasis.opendocument.text",
            compress_type=zipfile.ZIP_STORED,
        )
        zf.writestr("META-INF/manifest.xml", manifest)
        zf.writestr("content.xml", content_xml)
    return (
        buf.getvalue(),
        _safe_filename(title, "odt"),
        "application/vnd.oasis.opendocument.text",
    )


def _pdf_escape(text: str) -> str:
    return (
        str(text)
        .replace("\\", "\\\\")
        .replace("(", "\\(")
        .replace(")", "\\)")
        .replace("\r", "")
        .encode("latin-1", "replace")
        .decode("latin-1")
    )


def export_pdf(data: dict[str, Any], title: str = "Kanban") -> tuple[bytes, str, str]:
    headers, rows = _flatten_rows(data)
    stamp = datetime.now().strftime("%d.%m.%Y %H:%M")
    lines: list[str] = [str(title or "Kanban Board"), f"Exportiert am {stamp}", ""]
    for row in rows:
        f = _row_fields(row)
        lines.append(f"[{f['col']}] {f['title']}")
        if f["due"]:
            lines.append(f"  Faellig: {f['due']}")
        if f["notes"]:
            for part in str(f["notes"]).splitlines() or [""]:
                lines.append(f"  {part}")
        meta = []
        if f["recurrence"]:
            meta.append(f"Wiederholung: {f['recurrence']}")
        if f["milestone"]:
            meta.append(f"Ziel: {f['milestone']}")
        if f["completed"]:
            meta.append(f"Erledigt: {f['completed']}")
        if f["color"] and f["color"] != "none":
            meta.append(f"Farbe: {f['color']}")
        if f["atts"]:
            meta.append(f"Dateien: {f['atts']}")
        if f["created"]:
            meta.append(f"Erstellt: {f['created']}")
        if meta:
            lines.append("  " + " | ".join(meta))
        lines.append("")

    # paginate ~55 lines
    pages_lines: list[list[str]] = []
    chunk: list[str] = []
    for line in lines:
        chunk.append(line[:110])
        if len(chunk) >= 55:
            pages_lines.append(chunk)
            chunk = []
    if chunk:
        pages_lines.append(chunk)
    if not pages_lines:
        pages_lines = [[str(title or "Kanban")]]

    objects: list[bytes] = []
    # 1 catalog, 2 pages tree, then page + content pairs
    kids = []
    content_objs = []

    for page_lines in pages_lines:
        y = 800
        content = ["BT", "/F1 11 Tf", "14 TL", "50 800 Td"]
        first = True
        for line in page_lines:
            txt = _pdf_escape(line)
            if first:
                content.append(f"({txt}) Tj")
                first = False
            else:
                content.append("T*")
                content.append(f"({txt}) Tj")
            y -= 14
        content.append("ET")
        stream = "\n".join(content).encode("latin-1", "replace")
        content_objs.append(stream)

    # object numbers:
    # 1: Catalog
    # 2: Pages
    # 3: Font
    # then for each page: page_obj, content_obj
    font_obj = 3
    page_obj_nums = []
    raw_objects: dict[int, bytes] = {}
    raw_objects[3] = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"

    next_id = 4
    for stream in content_objs:
        content_id = next_id
        page_id = next_id + 1
        next_id += 2
        raw_objects[content_id] = (
            f"<< /Length {len(stream)} >>\nstream\n".encode("latin-1")
            + stream
            + b"\nendstream"
        )
        raw_objects[page_id] = (
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
            f"/Contents {content_id} 0 R /Resources << /Font << /F1 {font_obj} 0 R >> >> >>"
        ).encode("latin-1")
        page_obj_nums.append(page_id)

    kids_str = " ".join(f"{n} 0 R" for n in page_obj_nums)
    raw_objects[2] = (
        f"<< /Type /Pages /Kids [{kids_str}] /Count {len(page_obj_nums)} >>"
    ).encode("latin-1")
    raw_objects[1] = b"<< /Type /Catalog /Pages 2 0 R >>"

    out = bytearray(b"%PDF-1.4\n")
    offsets = {0: 0}
    max_id = max(raw_objects)
    for obj_id in range(1, max_id + 1):
        offsets[obj_id] = len(out)
        out.extend(f"{obj_id} 0 obj\n".encode("latin-1"))
        out.extend(raw_objects[obj_id])
        out.extend(b"\nendobj\n")
    xref_pos = len(out)
    out.extend(f"xref\n0 {max_id + 1}\n".encode("latin-1"))
    out.extend(b"0000000000 65535 f \n")
    for obj_id in range(1, max_id + 1):
        out.extend(f"{offsets[obj_id]:010d} 00000 n \n".encode("latin-1"))
    out.extend(
        f"trailer\n<< /Size {max_id + 1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n".encode(
            "latin-1"
        )
    )
    return bytes(out), _safe_filename(title, "pdf"), "application/pdf"


def build_export(
    fmt: str,
    data: dict[str, Any],
    title: str = "Kanban",
) -> tuple[bytes, str, str]:
    kind = str(fmt or "").strip().lower()
    if kind in ("xlsx", "excel", "xls"):
        return export_xlsx(data, title)
    if kind in ("docx", "word", "doc"):
        return export_docx(data, title)
    if kind in ("odt", "opendocument", "libreoffice"):
        return export_odt(data, title)
    if kind == "pdf":
        return export_pdf(data, title)
    if kind == "json":
        raw = __import__("json").dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        return raw, _safe_filename(title, "json"), "application/json"
    raise ValueError(f"Unbekanntes Exportformat: {fmt}")
