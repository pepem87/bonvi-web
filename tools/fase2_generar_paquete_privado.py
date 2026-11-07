#!/usr/bin/env python3
"""Fase 2 BON VI: generar, auditar y empaquetar un catálogo PRIVADO.

No tiene funciones de despliegue, Git push, SQL de escritura ni acceso a los
módulos Streamlit. Reutiliza las reglas de un checkout original en SOLO LECTURA.

Requiere un DATABASE_URL privado para lectura real, o --snapshot para ensayo.
Guarda las ejecuciones fuera de ambos repositorios sin reemplazar anteriores.
"""
import argparse
import hashlib
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from zipfile import ZIP_DEFLATED, ZipFile

PRODUCTS = re.compile(r"const products=(\[.*?\]);\s*const aliases=", re.DOTALL)
FIELDS = {
    "codigo", "nombre", "familia", "categoria", "presentacion", "marca",
    "tipo", "uxb", "precio", "unitario", "imagen", "imagen_categoria",
    "icono_categoria", "slug",
}
PRIVATE_MARKERS = ("costo_unitario", "precio_comercio_unit", "DATABASE_URL=")


def load_public_html(path):
    html = Path(path).read_text(encoding="utf-8")
    found = PRODUCTS.search(html)
    if not found or "noindex,nofollow" not in html:
        raise ValueError("Falta el listado público o la protección noindex")
    items = json.loads(found.group(1))
    if not isinstance(items, list) or not items:
        raise ValueError("Catálogo vacío o mal formado")
    by_code = {}
    for item in items:
        if not isinstance(item, dict) or set(item) - FIELDS:
            raise ValueError("La ficha tiene campos no públicos")
        code = str(item.get("codigo") or "").strip()
        slug = str(item.get("slug") or "")
        if not code or code in by_code or not re.fullmatch(r"[a-z0-9-]+", slug):
            raise ValueError("SKU duplicado, vacío o ruta inválida")
        if item.get("tipo") not in ("bulto", "unidad"):
            raise ValueError("Modalidad no autorizada: " + code)
        qty, unit, price = (item.get(n) for n in ("uxb", "unitario", "precio"))
        if any(isinstance(x, bool) or not isinstance(x, (int, float))
               or not math.isfinite(x) or x <= 0 for x in (qty, unit, price)):
            raise ValueError("Precio/UXB inválido: " + code)
        if int(qty) != qty or (item["tipo"] == "unidad" and qty != 1):
            raise ValueError("UxB incoherente: " + code)
        expected = unit * (qty if item["tipo"] == "bulto" else 1)
        if abs(price - expected) > 0.011:
            raise ValueError("Precio de venta incoherente: " + code)
        by_code[code] = item
    if any(x in html for x in PRIVATE_MARKERS):
        raise ValueError("El HTML podría contener campos o credenciales privados")
    return by_code


def compare_approved(old, new):
    before, after = set(old), set(new)
    common = sorted(before & after)
    changed_price, changed_mode, changed_identity, changed_other = [], [], [], []
    for code in common:
        a, b = old[code], new[code]
        if a["unitario"] != b["unitario"] or a["precio"] != b["precio"]:
            changed_price.append(code)
        if (a["tipo"], a["uxb"]) != (b["tipo"], b["uxb"]):
            changed_mode.append(code)
        if any(a.get(k) != b.get(k) for k in ("nombre", "familia", "categoria")):
            changed_identity.append(code)
        if a != b and not any(code in group for group in
                              (changed_price, changed_mode, changed_identity)):
            changed_other.append(code)
    added = sorted(after - before)
    removed = sorted(before - after)
    count_changed = bool(added or removed or changed_price or changed_mode or
                         changed_identity or changed_other)
    return {
        "estado": "CAMBIOS_PARA_REVISAR" if count_changed else "IGUAL_A_APROBADO",
        "publicacion_autorizada": False,
        "anterior": len(old), "nuevo": len(new),
        "altas": len(added), "bajas": len(removed),
        "cambios_precio": len(changed_price),
        "cambios_modalidad_uxb": len(changed_mode),
        "cambios_nombre_familia_categoria": len(changed_identity),
        "otros_cambios_visibles": len(changed_other),
        "ejemplos": {
            "altas": added[:20], "bajas": removed[:20],
            "precios": changed_price[:20], "modalidad": changed_mode[:20],
            "clasificacion": changed_identity[:20],
        },
    }


def audit_package(folder, reference_html):
    root = Path(folder)
    index = root / "index.html"
    products = load_public_html(index)
    reference = load_public_html(reference_html)
    missing = []
    for p in products.values():
        path = root / "productos" / p["slug"] / "index.html"
        if not path.is_file() or "noindex" not in path.read_text(encoding="utf-8"):
            missing.append(p["codigo"])
    actual_pages = len(list((root / "productos").glob("*/index.html")))
    if missing or actual_pages != len(products):
        raise ValueError(f"Fichas ausentes o sobrantes: {missing[:5]}; total={actual_pages}")
    pdf = root / "catalogo-personas.pdf"
    if not pdf.exists() or pdf.stat().st_size < 1024 or pdf.open("rb").read(5) != b"%PDF-":
        raise ValueError("El PDF original regenerado falta o no es válido")
    # Validar estructura real del PDF, no solo la cabecera de 5 bytes.
    from pypdf import PdfReader
    try:
        reader = PdfReader(str(pdf), strict=True)
        pdf_pages = len(reader.pages)
    except Exception as error:
        raise ValueError("El PDF no puede abrirse correctamente") from error
    if pdf_pages < 1:
        raise ValueError("El PDF generado no tiene páginas")
    # Control exhaustivo: cada SKU y ambos precios deben figurar en el PDF.
    # El generador original dispone el código en una línea independiente.
    pdf_text = "\n".join(page.extract_text() or "" for page in reader.pages)
    matches = [(m.group(1), m.start(), m.end())
               for m in re.finditer(r"(?m)^\s*(\d{1,5})\s*$", pdf_text)
               if m.group(1) in products]
    if len(matches) != len(products) or {m[0] for m in matches} != set(products):
        raise ValueError("El PDF no contiene exactamente todos los códigos del catálogo")
    price_errors = []
    for i, (code, _, end) in enumerate(matches):
        next_start = matches[i + 1][1] if i + 1 < len(matches) else len(pdf_text)
        row_text = pdf_text[end:next_start]
        for field in ("unitario", "precio"):
            expected = "$ " + format(products[code][field], ",.0f").replace(",", ".")
            if expected not in row_text:
                price_errors.append(code + ": " + field)
    if price_errors:
        raise ValueError("Precios del PDF divergentes: " + ", ".join(price_errors[:10]))
    control = json.loads((root / "control-privado.json").read_text(encoding="utf-8"))
    if control.get("productos") != len(products) or control.get("errores"):
        raise ValueError("Falla el control del generador original")
    if not isinstance(control.get("pdf_productos"), int) or control["pdf_productos"] < len(products):
        raise ValueError("Cantidad incorrecta en la fuente del PDF")
    required = {
        "assets/logo_bon_vi_mercat.png", "assets/web_mockup.png",
        *("assets/button_icons/" + x + ".webp" for x in
          ("vinos", "champagnes", "cervezas", "jugos", "whiskys",
           "aperitivos", "aceites", "otros")),
    }
    absent = sorted(name for name in required if not (root / name).is_file())
    if absent:
        raise ValueError("Faltan ilustraciones aprobadas: " + ", ".join(absent))
    result = compare_approved(reference, products)
    result.update({
        "integridad": "OK",
        "pdf_bytes": pdf.stat().st_size,
        "pdf_paginas": pdf_pages,
        "precios_pdf_verificados": len(products) * 2,
        "pdf_productos_fuente": control["pdf_productos"],
        "fichas_verificadas": actual_pages,
        "vigencia": control.get("vigencia", ""),
        "destino_publico": None,
    })
    return result


def generate(args):
    approved = Path(args.aprobado_html).resolve()
    original = Path(args.streamlit_dir).resolve()
    output_root = Path(args.salida_raiz).resolve()
    repo = Path(__file__).resolve().parents[1]
    if not approved.is_file() or not original.is_dir():
        raise ValueError("Faltan el índice aprobado o la copia local del catálogo Streamlit")
    reference = json.loads((repo / "tools" / "fase2_referencia_aprobada.json").read_text(encoding="utf-8"))
    def digest(path):
        sha = hashlib.sha256()
        with Path(path).open("rb") as handle:
            for part in iter(lambda: handle.read(1024 * 1024), b""):
                sha.update(part)
        return sha.hexdigest()
    if digest(approved) != reference["sha256_index_aprobado"]:
        raise ValueError("El index.html no es la copia de Fase 1 aprobada; no regenerar")
    if args.aprobado_pdf:
        approved_pdf = Path(args.aprobado_pdf).resolve()
        if not approved_pdf.is_file() or digest(approved_pdf) != reference["sha256_pdf_aprobado"]:
            raise ValueError("El PDF de referencia no coincide con la versión aprobada")
    # Nunca crear artefactos dentro del repositorio web ni del proyecto interno.
    if (output_root == repo or repo in output_root.parents or
            output_root == original or original in output_root.parents or
            original == output_root.parent):
        raise ValueError("La salida debe estar fuera de ambos repositorios")
    if not args.snapshot and not os.environ.get("DATABASE_URL"):
        raise ValueError("Definí DATABASE_URL (lectura) o --snapshot para prueba offline")
    output_root.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    working = Path(tempfile.mkdtemp(prefix="bonvi-f2-" + timestamp + "-", dir=output_root))
    generated = working / "catalogo"
    cmd = [
        sys.executable,
        str(repo / "tools" / "generar_catalogo_integrado.py"),
        "--streamlit-dir", str(original),
        "--output", str(generated),
    ]
    if args.snapshot:
        cmd += ["--snapshot", str(Path(args.snapshot).resolve())]
    subprocess.run(cmd, check=True)
    report = audit_package(generated, approved)
    report["modo"] = "snapshot-privado" if args.snapshot else "supabase-solo-lectura"
    report_file = working / "reporte-fase2.json"
    report_file.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    archive = working / "catalogo-web-privado.zip"
    with ZipFile(archive, "w", compression=ZIP_DEFLATED, compresslevel=6) as zipout:
        for file in sorted(generated.rglob("*")):
            if file.is_file() and not file.is_symlink():
                zipout.write(file, file.relative_to(generated))
        zipout.write(report_file, "reporte-fase2.json")
    with ZipFile(archive) as z:
        invalid = z.testzip()
        if invalid:
            raise ValueError("Archivo ZIP dañado: " + invalid)
        if "index.html" not in z.namelist() or "catalogo-personas.pdf" not in z.namelist():
            raise ValueError("Paquete sin catálogo o PDF")
    print(json.dumps({
        "estado": report["estado"],
        "productos": report["nuevo"],
        "fichas": report["fichas_verificadas"],
        "reporte": str(report_file),
        "zip": str(archive),
        "publicado": False,
    }, ensure_ascii=False, indent=2))
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--aprobado-html", required=True, help="index.html aprobado, inmutable")
    p.add_argument("--aprobado-pdf", help="PDF aprobado para verificar integridad de la referencia")
    p.add_argument("--streamlit-dir", required=True, help="Checkout ORIGINAL solo de lectura")
    p.add_argument("--salida-raiz", required=True, help="Directorio privado externo a ambos repositorios")
    p.add_argument("--snapshot", help="JSON de pruebas privado (si se omite, lectura real DATABASE_URL)")
    args = p.parse_args()
    try:
        generate(args)
    except (OSError, ValueError, subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        p.exit(2, f"FASE 2 BLOQUEADA: {exc}\n")


if __name__ == "__main__":
    main()
