#!/usr/bin/env python3
"""Validate exact BON VI approved public-only catalog ZIP before staging it.
No network, SQL, github writes or site publication in this module.
"""
import argparse
import hashlib
from html.parser import HTMLParser
import io
import json
from pathlib import Path, PurePosixPath
import re
import sys
from urllib.parse import urlsplit, unquote
from zipfile import ZipFile
from pypdf import PdfReader

HOST = "https://bonvimercat.com.ar/catalogo/"
INDEX_PATTERN = re.compile(r"const products=(\[.*?\]);\s*const aliases=", re.S)
PRODUCT = re.compile(r"productos/[^/]+/index\.html\Z")
CATEGORY = re.compile(r"categorias/[^/]+/index\.html\Z")
ROBOTS = 'content="noindex,nofollow"'
EXPECTED_PDF_SHA = "6a8f2a3256b1bf6119228be130ad1e60e48d80aaee451912d861178d7fb2c120"


class RefParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs = []
    def handle_starttag(self, tag, attrs):
        if tag not in {"a", "img", "script", "source", "link"}:
            return
        d = dict(attrs)
        if tag == "link" and d.get("rel") == "canonical":
            return
        link = d.get("href") if tag in {"a", "link"} else d.get("src")
        if link:
            self.refs.append(link)


def check_zip(source, manifest):
    blob = source.read_bytes()
    assert hashlib.sha256(blob).hexdigest() == manifest["zip_sha256"], "ZIP sha256 mismatch"
    assert len(blob) == manifest["zip_size"], "ZIP size mismatch"
    with ZipFile(io.BytesIO(blob)) as z:
        assert z.testzip() is None, "Corrupt ZIP"
        names = z.namelist()
        assert len(names) == len(set(names)) == manifest["expected_files"], "Files mismatch"
        for name in names:
            p = PurePosixPath(name)
            assert not p.is_absolute() and ".." not in p.parts and "\\" not in name
            assert not name.startswith(".") and not any(part.startswith(".") for part in p.parts)
            assert not name.endswith("/")
            assert name.startswith(("assets/", "productos/", "categorias/")) or name in ("index.html", "catalogo-personas.pdf"), name
            assert not ((z.getinfo(name).external_attr >> 16) & 0o170000 == 0o120000), name
        product_pages = [name for name in names if PRODUCT.fullmatch(name)]
        cats = [name for name in names if CATEGORY.fullmatch(name)]
        pages = ["index.html"] + product_pages + cats
        assert len(product_pages) == 1541 and len(cats) == 16 and len(pages) == 1558
        index = z.read("index.html").decode("utf-8")
        match = INDEX_PATTERN.search(index)
        assert match, "Missing complete public JSON catalog"
        products = json.loads(match.group(1))
        assert len(products) == 1541 and len(set(p["codigo"] for p in products)) == 1541
        allowed_keys = {"codigo", "nombre", "familia", "categoria", "presentacion", "marca",
                        "tipo", "uxb", "precio", "unitario", "imagen", "imagen_categoria",
                        "icono_categoria", "slug"}
        assert all(set(p).issubset(allowed_keys) for p in products)
        by_cat = lambda cat: [p for p in products if p["categoria"] == cat]
        assert {x["codigo"] for x in by_cat("CUIDADO PERSONAL Y HOGAR")} == {"2482", "2483", "2362", "2175"}
        assert len(by_cat("GIN")) == 46 and len(by_cat("APERITIVOS")) == 27
        assert 'chosen==="APERITIVOS"?["APERITIVOS","GIN"].includes(actual)' in index
        assert 'chosen==="OTROS"?["CUIDADO PERSONAL Y HOGAR","VARIADOS"].includes(actual)' in index
        assert 'URLSearchParams(window.location.search)' in index, "URL category filter not activated"
        assert "catalogo-personas.pdf" in names
        pdf = z.read("catalogo-personas.pdf")
        assert hashlib.sha256(pdf).hexdigest() == EXPECTED_PDF_SHA
        assert len(PdfReader(io.BytesIO(pdf)).pages) == 44
        canonicals = set()
        local_errors = []
        set_names = set(names)
        for i, name in enumerate(pages):
            doc = z.read(name).decode("utf-8")
            assert ROBOTS in doc, f"Missing noindex in {name}"
            assert "Vista previa privada" not in doc and "No publicar sin validar" not in doc, name
            assert "DATABASE_URL=" not in doc and '"costo_unitario"' not in doc
            assert '"precio_comercio_unit"' not in doc
            cs = re.findall(r'<link rel="canonical" href="([^"]+)"', doc)
            assert len(cs) == 1 and cs[0].startswith(HOST), (name, cs)
            assert cs[0] not in canonicals, cs[0]
            canonicals.add(cs[0])
            parser = RefParser()
            parser.feed(doc)
            current = PurePosixPath(name).parent
            for link in parser.refs:
                u = urlsplit(link)
                if u.scheme or u.netloc or link.startswith("//") or not u.path:
                    continue
                path = unquote(u.path)
                if path.startswith("/"):
                    # Brand links go to site's root, not inside catalog.
                    if path == "/":
                        continue
                    # Paths from site root expected to exist only after full site deployed.
                    continue
                candidate = current / path
                components = []
                for part in candidate.parts:
                    if part in ("", "."):
                        continue
                    if part == "..":
                        if components:
                            components.pop()
                        else:
                            local_errors.append([name, link, "escape"])
                    else:
                        components.append(part)
                resolved = "/".join(components)
                if resolved not in set_names and resolved.rstrip("/") + "/index.html" not in set_names:
                    local_errors.append([name, link, "missing"])
        assert len(canonicals) == 1558
        assert not local_errors, f"Broken links: {local_errors[:8]}"
        return {
            "success": True, "products": len(products), "categories": len(cats),
            "pages": len(pages), "files": len(names), "pdf_pages": 44,
            "canonical_urls": len(canonicals), "internal_errors": 0,
            "other_products": 4, "aperitivos_with_gin": 73, "robots": "noindex,nofollow"
        }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--zip", required=True)
    p.add_argument("--manifest", required=True)
    p.add_argument("--extract", help="Optional EMPTY destination outside repo original")
    args = p.parse_args()
    source = Path(args.zip)
    manifest = json.loads(Path(args.manifest).read_text("utf-8"))
    checks = check_zip(source, manifest)
    if args.extract:
        output = Path(args.extract)
        if output.exists():
            raise ValueError("Refusing to overwrite an existing catalog folder")
        output.mkdir(parents=True)
        with ZipFile(source) as archive:
            archive.extractall(output)
    print(json.dumps(checks, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
