"""Puente de SOLO LECTURA a las reglas vigentes del catálogo público Streamlit.

No reimplementa clasificación ni modifica archivos originales. Requiere copia
local autorizada de pdf_catalogo.py y pages/0_📲_Catalogo_publico.py.
La salida es PRIVADA hasta validación y aprobación de publicación.
"""
import ast
import json
import re
import unicodedata
from pathlib import Path

PDF_FUNCS = {"_category_norm", "_category_word", "_category_starts", "_macro_category"}
PAGE_FUNCS = {"normalize_text", "public_category", "public_brand",
              "displayed_sale_price", "filter_price_value",
              "matches_public_category", "price_filter_matches"}
PAGE_CONSTANTS = {"CATEGORY_TITLES", "OTHER_PUBLIC_CATEGORIES",
                  "KNOWN_BRAND_PREFIXES", "PRICE_OPTIONS", "PRICE_BASIS_OPTIONS",
                  "POPULAR_CATEGORIES", "SORT_OPTIONS", "SEARCH_CATEGORY_ALIASES",
                  "CATEGORY_PLACEHOLDERS", "FALLBACK_CATEGORY_PNG", "BUTTON_ICON_FILES", "CATEGORY_ICONS"}


def _extract(source, functions, constants=frozenset()):
    tree = ast.parse(Path(source).read_text(encoding="utf-8"), filename=str(source))
    selected = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in functions:
            selected.append(node)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if any(isinstance(t, ast.Name) and t.id in constants for t in targets):
                selected.append(node)
    return ast.Module(body=selected, type_ignores=[])


def load_rules(streamlit_dir):
    """Carga exactamente las funciones originales sin ejecutar Streamlit."""
    root = Path(streamlit_dir)
    pdf = root / "pdf_catalogo.py"
    page = root / "pages" / "0_📲_Catalogo_publico.py"
    if not pdf.is_file() or not page.is_file():
        raise FileNotFoundError("Faltan archivos originales de Streamlit")
    scope = {"re": re, "unicodedata": unicodedata}
    for source, functions, constants in (
        (pdf, PDF_FUNCS, frozenset()),
        (page, PAGE_FUNCS, PAGE_CONSTANTS),
    ):
        code = compile(_extract(source, functions, constants), str(source), "exec")
        exec(code, scope)
    for fn in PDF_FUNCS | PAGE_FUNCS:
        if fn not in scope:
            raise RuntimeError("Regla original faltante: " + fn)
    return scope


def adapt_rows(rows, rules):
    """Respeta exclusiones, excepción PEDI POR UNIDAD y orden L7."""
    result = []
    for row in rows:
        if str(row.get("activo", 1)) not in {"1", "True", "true"}:
            continue
        if "BLOQUEADO" in str(row.get("rol") or "").upper():
            continue
        unit = float(row.get("precio_persona_unit") or 0)
        if unit <= 0:
            continue
        item = dict(row)
        family = str(item.get("familia") or "")
        product = str(item.get("producto") or "")
        modality = str(item.get("modalidad") or "UNIDAD").upper()
        if "PEDI" in family.upper() and "UNID" in family.upper():
            modality = "UNIDAD"
        item["modalidad"] = modality
        item["precio_unitario"] = unit
        item["categoria_publica"] = rules["public_category"](family, product)
        item["marca_publica"] = rules["public_brand"](product)
        item["precio_mostrado"] = rules["displayed_sale_price"](item)
        result.append(item)
    return sorted(result, key=lambda x: (
        float(999999 if x.get("orden_l7") is None else x["orden_l7"]), str(x.get("codigo") or "")))


def export_private_json(rows, rules, destination):
    """Sólo campos visibles al consumidor. Nunca exporta costos ni márgenes."""
    safe = []
    for item in adapt_rows(rows, rules):
        safe.append({
            "codigo": str(item["codigo"]),
            "producto": str(item["producto"]),
            "familia": str(item.get("familia") or ""),
            "presentacion": str(item.get("presentacion") or ""),
            "uxb": item.get("uxb") or 1,
            "modalidad": item["modalidad"],
            "precio_persona_unit": item["precio_unitario"],
            "categoria": item["categoria_publica"],
            "marca": item["marca_publica"],
            "orden_l7": item.get("orden_l7"),
        })
    output = Path(destination)
    if output.exists():
        raise FileExistsError("No se sobrescriben exportaciones previas")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(safe, ensure_ascii=False, indent=2), encoding="utf-8")
    return len(safe)

def verify_against_original(rows, rules):
    """Chequeos de invariantes antes de permitir una exportación pública."""
    catalog = adapt_rows(rows, rules)
    errors = []
    seen = set()
    for p in catalog:
        code = str(p["codigo"])
        if code in seen:
            errors.append("Código repetido: " + code)
        seen.add(code)
        expected = rules["public_category"](p.get("familia"), p.get("producto"))
        if p["categoria_publica"] != expected:
            errors.append("Categoría divergente: " + code)
        if p["precio_mostrado"] != rules["displayed_sale_price"](p):
            errors.append("Precio divergente: " + code)
        if float(p["precio_unitario"]) <= 0:
            errors.append("Precio no positivo: " + code)
    return {"productos": len(catalog), "errores": errors}
