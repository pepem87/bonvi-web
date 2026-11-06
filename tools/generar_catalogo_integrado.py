#!/usr/bin/env python3
"""Generación PRIVADA desde Streamlit original y Supabase (solo SELECT).

Uso desde checkout local con ambos repositorios:
  DATABASE_URL=... python tools/generar_catalogo_integrado.py \
    --streamlit-dir /ruta/Bonvi-Mercat/BON_VI_MERCAT_Proyecto_v7_3_ONLINE/BON_VI_MERCAT_REAL_v7_3_ONLINE \
    --output /ruta/privada/vista-nueva

No desplegar ni subir salida al repositorio sin revisión de precios y PDF.
"""
import argparse
import json
import os
from pathlib import Path
from puente_catalogo_streamlit import load_rules, adapt_rows, verify_against_original
from catalogo_indice import write_preview

SQL_PDF = """
SELECT codigo, producto, familia, presentacion, uxb,
       modalidad, precio_persona_unit, activo, rol, orden_l7
FROM public.productos
WHERE activo = 1 AND UPPER(COALESCE(rol,'')) NOT LIKE '%BLOQUEADO%'
ORDER BY COALESCE((SELECT MIN(p2.orden_l7) FROM public.productos p2
                   WHERE p2.activo=1 AND COALESCE(p2.familia,'')=COALESCE(productos.familia,'')),999999),
         COALESCE(orden_l7,999999), codigo
"""

SQL = """
SELECT codigo, producto, familia, presentacion, uxb,
       modalidad, precio_persona_unit, activo, rol, orden_l7
FROM public.productos
WHERE activo = 1
  AND UPPER(COALESCE(rol,'')) NOT LIKE '%BLOQUEADO%'
  AND COALESCE(precio_persona_unit,0) > 0
ORDER BY COALESCE(orden_l7,999999), codigo
"""

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--streamlit-dir", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--snapshot", help="JSON privado con productos y vigencia; alternativa sin credenciales")
    parser.add_argument("--imagenes", help="JSON privado codigo -> URL HTTPS verificada, opcional")
    args = parser.parse_args()
    original = Path(args.streamlit_dir).resolve()
    output = Path(args.output).resolve()
    if not original.is_dir():
        parser.error("Falta el checkout del proyecto original")
    if output.exists() and any(output.iterdir()):
        parser.error("La carpeta de salida debe estar vacía")
    if not args.snapshot and not os.environ.get("DATABASE_URL"):
        parser.error("Se necesita DATABASE_URL o --snapshot privado")
    if Path.cwd().resolve() in output.parents or original in output.parents:
        parser.error("No generar datos dentro de los repositorios")
    rules = load_rules(original)
    if args.snapshot:
        snapshot = Path(args.snapshot).resolve()
        if not snapshot.is_file():
            parser.error("El snapshot privado no existe")
        payload = json.loads(snapshot.read_text(encoding="utf-8"))
        rows = payload["catalogo"]
        pdf_source_rows = payload["pdf"]
        vigencia = str(payload.get("vigencia") or "")
    else:
        import psycopg2
        conn = psycopg2.connect(os.environ["DATABASE_URL"], connect_timeout=12)
        try:
            conn.set_session(readonly=True, autocommit=False)
            with conn.cursor() as cur:
                cur.execute(SQL)
                names = [c[0] for c in cur.description]
                rows = [dict(zip(names, r)) for r in cur.fetchall()]
                cur.execute("SELECT valor FROM public.parametros WHERE clave='vigencia_catalogo' LIMIT 1")
                result = cur.fetchone()
                vigencia = str(result[0]) if result else ""
                cur.execute(SQL_PDF)
                pdf_names = [c[0] for c in cur.description]
                pdf_source_rows = [dict(zip(pdf_names, r)) for r in cur.fetchall()]
        finally:
            conn.close()
    report = verify_against_original(rows, rules)
    if report["errores"]:
        raise RuntimeError("No generar: " + "; ".join(report["errores"][:10]))
    adapted = adapt_rows(rows, rules)
    if len(adapted) != len(rows):
        raise RuntimeError("Diferencia de cobertura entre SQL y reglas Streamlit")
    # El PDF se genera con la misma función y archivos del proyecto original.
    import sys
    sys.path.insert(0, str(original))
    from pdf_catalogo import generate_catalog_pdf
    # PDF original: conserva su propio orden por familia y precios cero.
    pdf_rows = []
    for r in pdf_source_rows:
        item = dict(r)
        fam = str(item.get("familia") or "").upper()
        if "PEDI" in fam and "UNID" in fam:
            item["modalidad"] = "UNIDAD"
        item["precio_unitario"] = item.get("precio_persona_unit") or 0
        pdf_rows.append(item)
    pdf = generate_catalog_pdf(
        pdf_rows, "PERSONA", vigencia,
        next((p for p in [original / "assets" / name for name in
              ("logo_bon_vi_mercat.png", "logo.png", "BON_VI_MERCAT.png",
               "bon_vi_logo.png", "logo_bonvi.png")] if p.exists()), None),
        original / "assets",
    )
    if not pdf.startswith(b"%PDF-"):
        raise RuntimeError("El generador original no produjo un PDF válido")
    output.mkdir(parents=True, exist_ok=True)
    (output / "catalogo-personas.pdf").write_bytes(pdf)
    # Asignación estricta por código, sin búsquedas automáticas ni fotografías erróneas.
    if args.imagenes:
        mapping = json.loads(Path(args.imagenes).read_text(encoding="utf-8"))
        if not isinstance(mapping, dict):
            raise ValueError("El manifiesto de imágenes debe ser un objeto JSON")
        valid_codes = {str(row["codigo"]) for row in adapted}
        unknown = set(mapping) - valid_codes
        if unknown:
            raise ValueError(f"Imágenes con códigos desconocidos: {sorted(unknown)[:5]}")
        for row in adapted:
            row["imagen_verificada"] = mapping.get(str(row["codigo"]), "")
    # Los metadatos públicos se construyen con las reglas de Streamlit.
    for r in adapted:
        r["categoria"] = r["categoria_publica"]
        r["marca"] = r["marca_publica"]
        r["precio_persona_unit"] = r["precio_unitario"]
    # Genera índice, fichas y PDF en la misma carpeta privada.
    # write_preview exige carpeta vacía: usar subdirectorio temporal.
    import tempfile
    import shutil
    with tempfile.TemporaryDirectory(prefix="bonvi-private-") as tmp:
        write_preview(adapted, tmp, pdf_path="catalogo-personas.pdf")
        for item in Path(tmp).iterdir():
            shutil.move(str(item), str(output / item.name))
    (output / "control-privado.json").write_text(
        json.dumps({"productos":len(adapted),"vigencia":vigencia,
                    "errores":report["errores"],"pdf_bytes":len(pdf),"pdf_productos":len(pdf_rows)},
                   ensure_ascii=False,indent=2),encoding="utf-8")
    print("Generación PRIVADA terminada:",len(adapted),"productos. Revisar antes de publicar.")

if __name__ == "__main__":
    main()
