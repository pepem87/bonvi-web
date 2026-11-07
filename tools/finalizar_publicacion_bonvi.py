#!/usr/bin/env python3
"""Final BON VI catalog switch: prepare web edits in a LOCAL checkout only.

Preconditions: /catalogo already published and externally checked.
Does not push, access Supabase, change Streamlit, or deploy itself.
"""
import argparse
from collections import Counter
from datetime import date
import hashlib
from pathlib import Path
import re
import xml.etree.ElementTree as ET

HOST = "https://bonvimercat.com.ar"
OLD = "https://bonvi-mercat-6qpnhhbkm35bv8pcrywzmq.streamlit.app/Catalogo_publico"
PRODUCT_PAGE = re.compile(r"productos/[^/]+/index\.html$")
CATEGORY_PAGE = re.compile(r"categorias/[^/]+/index\.html$")
CNAME = "bonvimercat.com.ar"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def change_exact(source, before, after, count=1):
    actual = source.count(before)
    if actual != count:
        raise ValueError(f"Unexpected occurrence of {before!r}: {actual} vs {count}")
    return source.replace(before, after)


def patch_main(site):
    landing = site / "index.html"
    content = landing.read_text("utf-8")
    mappings = {
        "VINOS": "catalogo/?categoria=VINOS",
        "CERVEZAS": "catalogo/?categoria=CERVEZAS",
        "WHISKYS": "catalogo/?categoria=WHISKYS",
        "APERITIVOS": "catalogo/?categoria=APERITIVOS",
        "ACEITES": "catalogo/?categoria=ACEITES",
        "OTROS": "catalogo/?categoria=OTROS",
    }
    for category, target in mappings.items():
        content = change_exact(content, 'href="' + OLD + '?categoria=' + category + '"',
                               'href="' + target + '"')
    content = change_exact(content, 'href="' + OLD + '"', 'href="catalogo/"', count=2)
    if OLD in content:
        raise ValueError("Old Streamlit catalog link remains in main homepage")
    landing.write_text(content, "utf-8")
    subpages = {
        "vinos-la-plata/index.html": ("VINOS", "../catalogo/?categoria=VINOS"),
        "cervezas-la-plata/index.html": ("CERVEZAS", "../catalogo/?categoria=CERVEZAS"),
        "whisky-la-plata/index.html": ("WHISKYS", "../catalogo/?categoria=WHISKYS"),
        "gin-la-plata/index.html": ("APERITIVOS", "../catalogo/?categoria=APERITIVOS"),
        "aceites-y-acetos-la-plata/index.html": ("ACEITES", "../catalogo/?categoria=ACEITES"),
    }
    for name, (category, destination) in subpages.items():
        path = site / name
        content = path.read_text("utf-8")
        content = change_exact(content,
                               'href="' + OLD + '?categoria=' + category + '"',
                               'href="' + destination + '"')
        if OLD in content:
            raise ValueError("Old Streamlit catalog link remains in " + name)
        path.write_text(content, "utf-8")
    return 8 + len(subpages)


def activate_catalog(site):
    catalog = site / "catalogo"
    if not catalog.is_dir() or not (catalog / "catalogo-personas.pdf").is_file():
        raise ValueError("Staged /catalogo/ missing")
    pages = sorted(catalog.rglob("index.html"))
    prods = [p for p in pages if PRODUCT_PAGE.search(p.relative_to(catalog).as_posix())]
    cats = [p for p in pages if CATEGORY_PAGE.search(p.relative_to(catalog).as_posix())]
    if len(prods) != 1541 or len(cats) != 16 or len(pages) != 1558:
        raise ValueError(f"Catalog coverage changed {len(prods)}/{len(cats)}/{len(pages)}")
    originals = {"pdf": digest(catalog / "catalogo-personas.pdf"),
                 "logo": digest(catalog / "assets/logo_bon_vi_mercat.png"),
                 "background": digest(catalog / "assets/web_mockup.png")}
    if originals["pdf"] != "6a8f2a3256b1bf6119228be130ad1e60e48d80aaee451912d861178d7fb2c120":
        raise ValueError("Original PDF changed")
    urls = []
    for p in pages:
        text = p.read_text("utf-8")
        text = change_exact(text, 'content="noindex,nofollow"', 'content="index,follow"')
        if "Vista previa privada" in text or "No publicar sin validar" in text:
            raise ValueError("Private preview label remains in " + str(p))
        canonical = re.findall(r'<link rel="canonical" href="([^"]+)"', text)
        if len(canonical) != 1 or not canonical[0].startswith(HOST + "/catalogo/"):
            raise ValueError("Invalid canonical in " + str(p))
        urls.append(canonical[0])
        p.write_text(text, "utf-8")
    if len(set(urls)) != 1558:
        raise ValueError("Duplicate canonical URLs")
    if originals != {"pdf": digest(catalog / "catalogo-personas.pdf"),
                     "logo": digest(catalog / "assets/logo_bon_vi_mercat.png"),
                     "background": digest(catalog / "assets/web_mockup.png")}:
        raise ValueError("Static original images or PDF altered")
    return urls


def merge_sitemap(site, new_urls):
    path = site / "sitemap.xml"
    data = path.read_bytes()
    namespace = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
    doc = ET.fromstring(data)
    if doc.tag != namespace + "urlset":
        raise ValueError("Unexpected current sitemap")
    existing = []
    for element in doc.findall(namespace + "url"):
        val = element.findtext(namespace + "loc")
        if not val or not val.startswith(HOST + "/"):
            raise ValueError("Untrusted sitemap entry")
        existing.append(val)
    if len(existing) != 6 and len(existing) != 7:
        raise ValueError("Expected original homepage and five SEO pages, got " + str(len(existing)))
    if len(set(existing)) != len(existing):
        raise ValueError("Duplicate existing sitemap entry")
    if set(existing).intersection(new_urls):
        raise ValueError("Catalog URLs conflict with current sitemap")
    for value in new_urls:
        entry = ET.SubElement(doc, namespace + "url")
        ET.SubElement(entry, namespace + "loc").text = value
        ET.SubElement(entry, namespace + "lastmod").text = date.today().isoformat()
    ET.register_namespace("", "http://www.sitemaps.org/schemas/sitemap/0.9")
    ET.ElementTree(doc).write(path, encoding="utf-8", xml_declaration=True)
    roundtrip = ET.parse(path).getroot()
    items = roundtrip.findall(namespace + "url")
    if len(items) != len(existing) + 1558:
        raise ValueError("Sitemap coverage mismatch")
    return len(existing), len(items)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--site", required=True)
    args = p.parse_args()
    root = Path(args.site).resolve()
    if not (root / "CNAME").is_file() or (root / "CNAME").read_text("utf-8").strip() != CNAME:
        raise ValueError("Original CNAME missing")
    if "Sitemap: " + HOST + "/sitemap.xml" not in (root / "robots.txt").read_text("utf-8"):
        raise ValueError("Robots TXT changed")
    checks = {name: digest(root / name) for name in ["robots.txt", "CNAME"]}
    url_list = activate_catalog(root)
    replaced = patch_main(root)
    sitemap_previous, sitemap_final = merge_sitemap(root, url_list)
    if checks != {name: digest(root / name) for name in checks}:
        raise ValueError("robots/CNAME must not be altered")
    print({
        "ready": True, "pages_activated":len(url_list), "products": 1541,
        "homepage_and_category_links_updated":replaced,
        "sitemap_old":sitemap_previous, "sitemap_total":sitemap_final,
        "streamlit_app_modified":False,
    })


if __name__ == "__main__":
    main()
