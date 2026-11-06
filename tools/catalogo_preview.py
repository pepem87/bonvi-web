#!/usr/bin/env python3
"""Generador de catálogo SEO BON VI. Solo lectura, sin despliegue.

Requiere psycopg2-binary y DATABASE_URL de un entorno privado. Nunca colocar
DATABASE_URL ni el resultado generado en un repositorio público sin revisión.
"""
import argparse
import html
import json
import os
from pathlib import Path
import re
import tempfile
import unicodedata
from urllib.parse import quote

BASE_URL = "https://bonvimercat.com.ar"
WHATSAPP = "5492216816892"
QUERY = """
SELECT codigo, producto, familia, presentacion, uxb, modalidad,
       precio_persona_unit, activo
FROM public.productos
WHERE activo = 1 AND precio_persona_unit > 0
ORDER BY familia, producto, codigo
"""

def slug(value):
    value = unicodedata.normalize("NFKD", str(value))
    value = "".join(c for c in value if not unicodedata.combining(c))
    value = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return value or "producto"

def format_price(value):
    return "$ " + f"{float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def make_page(item):
    title = html.escape(item["producto"])
    family = html.escape(item["familia"] or "Productos")
    presentation = html.escape(item["presentacion"] or "")
    modality = html.escape(item["modalidad"] or "")
    url = BASE_URL + "/productos/" + item["slug"] + "/"
    description = html.escape(f"{item['producto']} en BON VI MERCAT, La Plata. Consultá disponibilidad y condiciones de venta por WhatsApp.", quote=True)
    message = quote(f"Hola BON VI, quiero consultar por {item['producto']} (código {item['codigo']}).")
    price = format_price(item["precio_persona_unit"])
    # El precio almacenado es unitario. No afirmamos que sea precio final
    # por bulto: modalidad y UXB requieren validación comercial previa.
    return f"""<!doctype html>
<html lang="es-AR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>{title} | BON VI MERCAT La Plata</title>
<meta name="description" content="{description}">
<link rel="canonical" href="{html.escape(url, quote=True)}">
<style>body{{font-family:system-ui,sans-serif;background:#f4eddf;color:#173d31;margin:0}}
main{{max-width:720px;margin:5vh auto;padding:30px;background:#fffaf1;border-radius:20px}}
a{{color:#173d31}}.cta{{display:inline-block;padding:14px 20px;background:#173d31;color:white;border-radius:8px}}
small{{color:#555}}</style></head><body><main>
<p><a href="/">BON VI MERCAT</a> / {family}</p>
<h1>{title}</h1>
<p>{presentation}</p>
<p><strong>Precio de referencia por unidad: {html.escape(price)}</strong></p>
<p><small>Modalidad registrada: {modality or "Consultar"}.
Precio y presentación sujetos a confirmación. Publicación de prueba, no apta para producción.</small></p>
<p><a class="cta" href="https://wa.me/{WHATSAPP}?text={message}">Consultar por WhatsApp</a></p>
</main></body></html>"""

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, help="Directorio local PRIVADO de previsualización")
    parser.add_argument("--limit", type=int, default=20, help="Máximo de productos para prueba")
    args = parser.parse_args()
    if args.limit < 1 or args.limit > 1000:
        parser.error("--limit debe estar entre 1 y 1000")
    if not os.getenv("DATABASE_URL"):
        parser.error("Falta DATABASE_URL; configurar solo en entorno privado")
    output = Path(args.output).resolve()
    if output == Path.cwd().resolve() or Path.cwd().resolve() in output.parents:
        parser.error("El destino debe estar FUERA del repositorio para evitar publicar datos")
    if output.exists() and any(output.iterdir()):
        parser.error("El destino debe estar vacío; no se sobrescriben archivos")
    import psycopg2
    with psycopg2.connect(os.environ["DATABASE_URL"], connect_timeout=12) as conn:
        conn.set_session(readonly=True, autocommit=False)
        with conn.cursor() as cur:
            cur.execute(QUERY)
            names = [col[0] for col in cur.description]
            rows = [dict(zip(names, row)) for row in cur.fetchmany(args.limit)]
    output.mkdir(parents=True, exist_ok=True)
    manifest = []
    for item in rows:
        item["slug"] = f"{slug(item['producto'])}-{item['codigo']}"
        folder = output / "productos" / item["slug"]
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "index.html").write_text(make_page(item), encoding="utf-8")
        manifest.append({"codigo": item["codigo"], "slug": item["slug"],
                         "nombre": item["producto"], "familia": item["familia"],
                         "precio_referencia_unitario": float(item["precio_persona_unit"])})
    (output / "manifest-preview.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Previsualización privada generada: {len(manifest)} productos en {output}")
    print("NO PUBLICAR: páginas noindex y precios/modalidades pendientes de validación.")

if __name__ == "__main__":
    main()
