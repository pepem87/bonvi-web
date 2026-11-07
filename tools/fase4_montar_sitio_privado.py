#!/usr/bin/env python3
"""Fase 4 BON VI: montar un SITIO DE ENSAYO local sin desplegar.

Uso:
 python tools/fase4_montar_sitio_privado.py --web-root /checkouts/bonvi-web-main \
   --catalog-zip /privado/BONVI_Fase3_SEO_Privado_1541.zip --output /privado/ensayo-fase4

Requiere el checkout del sitio de PRODUCCIÓN como entrada inmutable. No escribe
en ese checkout ni en la base, y nunca publica. Salida nueva: ZIP del sitio
integrado de prueba, manifest y sitemap candidato FUERA del ZIP.
"""
import argparse
import hashlib
from html.parser import HTMLParser
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET
from zipfile import ZipFile, ZIP_DEFLATED

BASE = "https://bonvimercat.com.ar"
STREAMLIT = "https://bonvi-mercat-6qpnhhbkm35bv8pcrywzmq.streamlit.app/Catalogo_publico"
LANDING = {
    "index.html": {
        "": "catalogo/index.html",
        "VINOS": "catalogo/index.html?categoria=VINOS",
        "CERVEZAS": "catalogo/index.html?categoria=CERVEZAS",
        "WHISKYS": "catalogo/index.html?categoria=WHISKYS",
        "APERITIVOS": "catalogo/index.html?categoria=APERITIVOS",
        "ACEITES": "catalogo/index.html?categoria=ACEITES",
        "OTROS": "catalogo/index.html?categoria=OTROS",
    },
    "vinos-la-plata/index.html": {"VINOS": "../catalogo/index.html?categoria=VINOS"},
    "cervezas-la-plata/index.html": {"CERVEZAS": "../catalogo/index.html?categoria=CERVEZAS"},
    "whisky-la-plata/index.html": {"WHISKYS": "../catalogo/index.html?categoria=WHISKYS"},
    "gin-la-plata/index.html": {"APERITIVOS": "../catalogo/index.html?categoria=APERITIVOS"},
    "aceites-y-acetos-la-plata/index.html": {"ACEITES": "../catalogo/index.html?categoria=ACEITES"},
}
ALLOWED_WEB = ("index.html", "robots.txt", "sitemap.xml", "CNAME")
MAIN_DIRS = ("assets", "vinos-la-plata", "cervezas-la-plata", "gin-la-plata",
             "whisky-la-plata", "aceites-y-acetos-la-plata")
PAGES = {"index.html", "catalogo/index.html"}


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for part in iter(lambda: f.read(1024 * 1024), b""):
            h.update(part)
    return h.hexdigest()


def static_refs(html):
    """Solo referencias estáticas HTML; excluye valores creados por JavaScript."""
    class Parser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.refs = []
        def handle_starttag(self, tag, attrs):
            if tag in ("a", "img", "script", "link", "source"):
                d = dict(attrs)
                candidate = d.get("href") if tag in ("a", "link") else d.get("src")
                if candidate:
                    # canonical apunta a un futuro destino externo; no enlace local.
                    if tag == "link" and d.get("rel") == "canonical":
                        return
                    self.refs.append(candidate)
    p = Parser()
    p.feed(html)
    return p.refs


def safe_zip_members(z):
    paths = []
    for meta in z.infolist():
        name = meta.filename
        p = PurePosixPath(name)
        if not name or p.is_absolute() or ".." in p.parts or "\\" in name:
            raise ValueError("El ZIP privado contiene una ruta insegura")
        if name.endswith("/"):
            continue
        if name.startswith(".") or any(part.startswith(".") for part in p.parts):
            raise ValueError("Archivo oculto no autorizado en el catálogo")
        if (meta.external_attr >> 16) & 0o170000 == 0o120000:
            raise ValueError("El catálogo contiene enlace simbólico")
        paths.append(name)
    if len(paths) != len(set(paths)):
        raise ValueError("Archivos duplicados en el ZIP")
    return paths


def make_noindex(document):
    if 'content="noindex,nofollow"' in document:
        return document
    changed, hits = re.subn(
        r'<meta\s+name="robots"\s+content="[^"]*"\s*/?>',
        '<meta name="robots" content="noindex,nofollow">',
        document, count=1, flags=re.I,
    )
    if not hits:
        changed, hits = re.subn(r"(<head\b[^>]*>)",
                                r'\1\n<meta name="robots" content="noindex,nofollow">',
                                document, count=1, flags=re.I)
    if hits != 1:
        raise ValueError("HTML sin cabecera para mantener noindex")
    return changed


def patch_links(page, source):
    updated = source
    total = 0
    for category, dest in LANDING[page].items():
        old = STREAMLIT + (("?categoria=" + category) if category else "")
        # Reemplazo exacto del valor href, sin alterar texto ni el resto del sitio.
        expression = 'href="' + old + '"'
        count = updated.count(expression)
        expected = 2 if page == "index.html" and category == "" else 1
        if count != expected:
            raise ValueError(f"Enlace de {page}, categoría {category}: {count} en lugar de {expected}")
        updated = updated.replace(expression, 'href="' + dest + '"')
        total += count
    if STREAMLIT in updated:
        raise ValueError("Persisten enlaces de catálogo antiguo en " + page)
    return updated, total


def build(web_root, catalog_zip, output):
    web_root, catalog_zip, output = (Path(web_root).resolve(), Path(catalog_zip).resolve(),
                                     Path(output).resolve())
    if output.exists():
        raise ValueError("El directorio de salida ya existe; no se sobrescribe")
    if output == web_root or web_root in output.parents or output in web_root.parents:
        raise ValueError("La salida debe estar aislada del repositorio de la web")
    if not catalog_zip.is_file():
        raise FileNotFoundError("Falta ZIP aprobado de Fase 3")
    if not (web_root / "index.html").is_file():
        raise FileNotFoundError("Falta la portada real de la web")
    for name in ("sitemap.xml", "robots.txt", "CNAME"):
        if not (web_root / name).is_file():
            raise ValueError("Falta el archivo de producción: " + name)
    with ZipFile(catalog_zip) as z:
        members = safe_zip_members(z)
        filenames = set(members)
        if "index.html" not in filenames or "catalogo-personas.pdf" not in filenames:
            raise ValueError("ZIP sin catálogo o PDF")
        category_pages = sorted(x for x in filenames if re.fullmatch(r"categorias/[^/]+/index\.html", x))
        product_pages = sorted(x for x in filenames if re.fullmatch(r"productos/[^/]+/index\.html", x))
        if len(category_pages) != 16 or len(product_pages) != 1541:
            raise ValueError("La Fase 3 requiere 16 categorías y 1541 fichas")
        for name in (["index.html"] + category_pages + product_pages):
            if 'content="noindex,nofollow"' not in z.read(name).decode("utf-8"):
                raise ValueError("Página privada sin noindex: " + name)
        output.mkdir(parents=True)
        site = output / "sitio"
        site.mkdir()
        # Conservar exactamente solo recursos públicos conocidos del sitio real.
        for name in ALLOWED_WEB:
            if name != "CNAME":
                shutil.copy2(web_root / name, site / name)
        for folder in MAIN_DIRS:
            src = web_root / folder
            if not src.is_dir():
                raise ValueError("Carpeta de la web existente faltante: " + folder)
            shutil.copytree(src, site / folder, symlinks=False)
        catalog = site / "catalogo"
        catalog.mkdir()
        for name in members:
            target = catalog / name
            target.parent.mkdir(parents=True, exist_ok=True)
            with z.open(name) as source, target.open("wb") as dest:
                shutil.copyfileobj(source, dest)

    changes = {}
    for page in LANDING:
        path = site / page
        before = path.read_text(encoding="utf-8")
        after, count = patch_links(page, before)
        path.write_text(make_noindex(after), encoding="utf-8")
        changes[page] = count
    # Un aviso visible evita confundir la copia de ensayo con el sitio real.
    notice = output / "LEEME-NO-PUBLICAR.txt"
    notice.write_text(
        "BON VI MERCAT - ENSAYO FASE 4. NO PUBLICAR NI SUBIR ESTE ZIP.\n"
        "El CNAME se excluyó intencionalmente. Todas las páginas de prueba usan noindex.\n"
        "El sitemap candidato se encuentra fuera del ZIP de ensayo.\n",
        encoding="utf-8",
    )
    # Preparación de sitemap para lanzamiento: no se activa en esta fase.
    ns = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
    root = ET.parse(web_root / "sitemap.xml").getroot()
    old_urls = {x.findtext(ns + "loc") for x in root.findall(ns + "url")}
    original_url_count = len(old_urls)
    all_paths = ["catalogo/"] + [f"catalogo/{p[:-10]}" for p in category_pages + product_pages]
    new_urls = [BASE + "/" + p for p in all_paths]
    if len(set(new_urls)) != 1558 or any(x in old_urls for x in new_urls):
        raise ValueError("Conflicto en el sitemap propuesto")
    for url in new_urls:
        el = ET.SubElement(root, ns + "url")
        ET.SubElement(el, ns + "loc").text = url
    candidate = output / "sitemap-CANDIDATO-SOLO-PARA-REVISION.xml"
    ET.register_namespace("", "http://www.sitemaps.org/schemas/sitemap/0.9")
    candidate.write_bytes(ET.tostring(root, encoding="utf-8", xml_declaration=True))
    if len(root.findall(ns + "url")) != original_url_count + 1558:
        raise ValueError("Cantidad incorrecta de direcciones propuestas")

    # Control de enlaces locales: una ruta debe existir dentro del ZIP montado.
    unresolved = []
    for page in (["index.html"] + list(LANDING.keys())[1:]
                 + ["catalogo/index.html"]
                 + ["catalogo/" + x for x in category_pages + product_pages]):
        file = site / page
        content = file.read_text(encoding="utf-8")
        if 'content="noindex,nofollow"' not in content:
            raise ValueError("Una página de ensayo carece de noindex: " + page)
        for href in static_refs(content):
            parsed = urlsplit(href)
            if parsed.scheme or parsed.netloc or href.startswith("#") or href.startswith("//"):
                continue
            rel = unquote(parsed.path)
            if not rel:
                continue
            if rel.startswith("/"):
                target = site / rel.lstrip("/")
            else:
                target = file.parent / rel
            target = target.resolve()
            if site not in target.parents and target != site:
                unresolved.append((page, href, "fuera del sitio"))
            elif target.is_dir():
                if not (target / "index.html").exists():
                    unresolved.append((page, href, "carpeta sin index"))
            elif not target.is_file():
                unresolved.append((page, href, "no existe"))
    if unresolved:
        raise ValueError("Enlaces internos rotos: " + repr(unresolved[:10]))

    # La portada y sitemap originales siguen intactos en el repositorio fuente.
    input_hashes = {name: sha256(web_root / name) for name in ("index.html", "robots.txt", "sitemap.xml")}
    report = {
        "estado": "ENSAYO_VERIFICADO",
        "publicado": False,
        "despliegue_autorizado": False,
        "enlaces_streamlit_sustituidos": sum(changes.values()),
        "enlaces_por_pagina": changes,
        "fichas_catalogo": len(product_pages),
        "paginas_categorias": len(category_pages),
        "paginas_catalogo": len(product_pages) + len(category_pages) + 1,
        "sitemap_existentes": original_url_count,
        "sitemap_candidato_total": original_url_count + 1558,
        "enlaces_internos_rotos": 0,
        "hashes_entrada_web": input_hashes,
    }
    (output / "informe-fase4.json").write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n",encoding="utf-8")
    archive = output / "BONVI_Fase4_Ensayo_Privado_NO_PUBLICAR.zip"
    with ZipFile(archive, "w", ZIP_DEFLATED, compresslevel=6) as packed:
        for f in sorted(site.rglob("*")):
            if f.is_file():
                packed.write(f, f.relative_to(site))
    with ZipFile(archive) as z:
        if z.testzip():
            raise ValueError("ZIP de ensayo no superó la prueba de integridad")
    if input_hashes != {name: sha256(web_root / name) for name in input_hashes}:
        raise ValueError("La fuente del sitio cambió durante el ensayo")
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--web-root",required=True)
    p.add_argument("--catalog-zip",required=True)
    p.add_argument("--output",required=True)
    a=p.parse_args()
    print(json.dumps(build(a.web_root,a.catalog_zip,a.output),ensure_ascii=False,indent=2))


if __name__ == "__main__":
    main()
