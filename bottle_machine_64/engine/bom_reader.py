"""
BOM reader: CSV or XLSX, indented SolidWorks-style (ITEM NO. 1, 1.1, 1.2.1 ...).

Strict: if a required column is missing it raises BomError naming the columns it
found, so the user can fix the export and upload again. Nothing is guessed.
"""
import csv
import os
import re

COLUMN_ALIASES = {
    "item": ["item no.", "item no", "item number", "item", "level"],
    "part_number": ["part number", "part no.", "part no", "partnumber", "part #", "pn"],
    "description": ["description", "part name", "name"],
    "qty": ["qty.", "qty", "quantity"],
    "material": ["material"],
}
REQUIRED = ["item", "part_number", "description", "qty"]


class BomError(Exception):
    pass


def _norm(h):
    return re.sub(r"\s+", " ", str(h or "").strip().lower())


def _read_rows(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".csv":
        for enc in ("utf-8-sig", "latin-1"):
            try:
                with open(path, newline="", encoding=enc) as f:
                    return list(csv.reader(f))
            except UnicodeDecodeError:
                continue
        raise BomError("The BOM file could not be decoded as text.")
    if ext in (".xlsx", ".xlsm"):
        try:
            import openpyxl
        except ImportError:
            raise BomError("Excel support is not installed; save the BOM as CSV.")
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        ws = wb.worksheets[0]
        return [[("" if c is None else c) for c in row] for row in ws.iter_rows(values_only=True)]
    raise BomError(f"BOM must be .csv or .xlsx (got '{ext or 'no extension'}').")


def read(path):
    rows = _read_rows(path)
    rows = [r for r in rows if any(str(c).strip() for c in r)]
    if not rows:
        raise BomError("The BOM file is empty.")
    header = [_norm(h) for h in rows[0]]
    col = {}
    for key, aliases in COLUMN_ALIASES.items():
        for a in aliases:
            if a in header:
                col[key] = header.index(a)
                break
    missing = [k for k in REQUIRED if k not in col]
    if missing:
        raise BomError("The BOM is missing required column(s): "
                       + ", ".join(m.replace("_", " ") for m in missing)
                       + f". Columns found: {', '.join(h for h in header if h) or 'none'}.")

    items = []
    for n, r in enumerate(rows[1:], start=2):
        def cell(k):
            i = col.get(k)
            return str(r[i]).strip() if i is not None and i < len(r) else ""
        pn, item = cell("part_number"), cell("item")
        if not pn:
            raise BomError(f"BOM row {n} has no part number.")
        try:
            qty = int(float(cell("qty")))
        except ValueError:
            raise BomError(f"BOM row {n} ({pn}): quantity '{cell('qty')}' is not a number.")
        items.append({"item": item, "level": item.count(".") + 1, "part_number": pn,
                      "description": cell("description"), "material": cell("material"), "qty": qty})
    pns = [i["part_number"] for i in items]
    dup = sorted({p for p in pns if pns.count(p) > 1})
    if dup:
        raise BomError("These part numbers appear on more than one BOM row: " + ", ".join(dup)
                       + ". Combine them into one row with the total quantity.")
    for i, it in enumerate(items):
        it["is_assembly"] = i + 1 < len(items) and items[i + 1]["item"].startswith(it["item"] + ".")
    return {"columns_found": [h for h in header if h], "rows": items}
