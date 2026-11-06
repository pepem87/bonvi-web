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
from catalogo_precios import public_offer

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
    """Ficha de prueba: precio del bulto principal y unitario como referencia."""
    offer = public_offer(item["modalidad"], item["uxb"], item["precio_persona_unit"])
    title = html.escape(str(item["producto"]))
    family = html.escape(str(item["familia"] or "Productos"))
    presentation = html.escape(str(item["presentacion"] or ""))
    url = BASE_URL + "/productos/" + item["slug"] + "/"
    description = html.escape(f"{item['producto']} en BON VI MERCAT, La Plata. Consultá disponibilidad.", quote=True)
    price = format_price(offer["precio_total"])
    unit = format_price(offer["precio_unitario_referencia"])
    if offer["tipo"] == "bulto":
        condition = f"Venta por bulto · {offer['cantidad']} unidades"
        reference = f'<p class="reference">Referencia: {unit} por unidad</p>'
    else:
        condition = "Venta por unidad"
        reference = ""
    whatsapp = f"https://wa.me/{WHATSAPP}"
    instagram = "https://www.instagram.com/bonvimercat/"
    return f"""<!doctype html>
<html lang="es-AR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>{title} | BON VI MERCAT La Plata</title>
<meta name="description" content="{description}">
<link rel="canonical" href="{html.escape(url, quote=True)}">
<style>
:root{{--green:#173d31;--cream:#f4eddf;--gold:#d5b983}}
*{{box-sizing:border-box}}body{{font-family:Georgia,serif;background:var(--cream);color:var(--green);margin:0}}
header{{background:var(--green);color:white;padding:18px max(20px,calc((100vw - 960px)/2));display:flex;justify-content:space-between;align-items:center;gap:12px}}
.brand{{font-weight:bold;letter-spacing:2px;color:white;text-decoration:none}}
nav{{display:flex;gap:15px}}nav a{{color:white;text-decoration:none;font:14px system-ui,sans-serif}}
main{{max-width:760px;margin:45px auto;padding:35px;background:#fffaf1;border:1px solid #e4dccd;border-radius:16px}}
.crumb{{font:13px system-ui,sans-serif;color:#68766c}}h1{{font-size:clamp(26px,5vw,40px);margin-bottom:10px}}
.condition{{font:15px system-ui,sans-serif;color:#54665a}}
.price{{font:bold 38px Georgia,serif;margin:22px 0 3px}}
.reference{{font:13px system-ui,sans-serif;color:#6b756d;margin:0}}
.notice{{font:12px system-ui,sans-serif;color:#73776e;margin-top:32px}}
.floating{{position:fixed;bottom:22px;right:18px;display:flex;flex-direction:column;gap:10px}}
.floating a{{display:grid;place-items:center;width:52px;height:52px;border-radius:50%;color:white;text-decoration:none;font:700 19px system-ui,sans-serif;box-shadow:0 3px 13px #0003}}
.wa{{background:#238b5b}}.ig{{background:linear-gradient(135deg,#7342be,#c73583,#e6a34c)}}
footer{{background:var(--green);color:white;padding:24px;text-align:center;font:14px system-ui,sans-serif}}
footer a{{color:white;margin:0 10px}}
@media(max-width:600px){{main{{margin:15px;padding:22px}}header{{padding:16px}}nav{{gap:8px}}}}
</style></head><body>
<header><a class="brand" href="/">BON VI MERCAT</a><nav aria-label="Redes sociales"><a href="{whatsapp}" aria-label="WhatsApp">WhatsApp</a><a href="{instagram}" aria-label="Instagram">Instagram</a></nav></header>
<main><p class="crumb">Catálogo / {family}</p><h1>{title}</h1>
<p>{presentation}</p><p class="condition">{condition}</p>
<p class="price">{price}</p>{reference}
<p class="notice">Vista previa privada. Precio y disponibilidad sujetos a confirmación. No publicar sin validar.</p></main>
<aside class="floating" aria-label="Contacto y redes"><a class="ig" href="{instagram}" target="_blank" rel="noopener noreferrer" aria-label="Seguir en Instagram">IG</a><a class="wa" href="{whatsapp}" target="_blank" rel="noopener noreferrer" aria-label="Consultar por WhatsApp">WA</a></aside>
<footer>BON VI MERCAT · La Plata<br><a href="{whatsapp}">WhatsApp</a><a href="{instagram}">Instagram</a></footer>
</body></html>"""

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
