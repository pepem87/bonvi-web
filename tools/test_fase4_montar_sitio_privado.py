"""Pruebas de Fase 4: ensamblado local con sitio ficticio; nunca publica."""
import json
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET
from zipfile import ZipFile

from fase4_montar_sitio_privado import BASE, LANDING, STREAMLIT, build


def fixture(root):
    source = root / "web"
    source.mkdir()
    (source / "robots.txt").write_text("User-agent: *\nAllow: /\nSitemap: " + BASE + "/sitemap.xml\n")
    (source / "CNAME").write_text("bonvimercat.com.ar\n")
    namespace = "http://www.sitemaps.org/schemas/sitemap/0.9"
    site = ET.Element("{" + namespace + "}urlset")
    for i in range(7):
        e = ET.SubElement(site, "{" + namespace + "}url")
        ET.SubElement(e, "{" + namespace + "}loc").text = BASE + "/pagina-" + str(i) + "/"
    ET.ElementTree(site).write(source / "sitemap.xml", encoding="utf-8", xml_declaration=True)
    links = []
    for category in LANDING["index.html"]:
        href = STREAMLIT + (("?categoria=" + category) if category else "")
        links.append('<a href="' + href + '">Ver productos</a>')
        if not category:
            links.append('<a href="' + href + '">Ver catálogo</a>')
    (source / "index.html").write_text('<html><head><meta name="robots" content="index,follow"></head><body>' + "".join(links) + '</body></html>')
    for folder in ("assets", "vinos-la-plata", "cervezas-la-plata", "gin-la-plata", "whisky-la-plata", "aceites-y-acetos-la-plata"):
        (source / folder).mkdir()
    for page, cat in list(LANDING.items())[1:]:
        category = next(iter(cat))
        (source / page).write_text('<html><head><meta name="robots" content="index,follow"></head><body><a href="' + STREAMLIT + '?categoria=' + category + '">Ver</a></body></html>')
    zpath = root / "fase3.zip"
    categories = [
        "vinos", "cervezas", "whiskys", "aperitivos", "aceites", "gin",
        "champagnes", "vodka", "tequila", "sidras", "anis-y-licores",
        "cocteles-rtd", "sin-alcohol-energizantes", "jugos-y-polvos",
        "cuidado-personal-y-hogar", "ron-y-cachaca",
    ]
    noindex = '<!doctype html><html><head><meta name="robots" content="noindex,nofollow"></head><body></body></html>'
    with ZipFile(zpath, "w") as z:
        z.writestr("index.html", noindex)
        z.writestr("catalogo-personas.pdf", "%PDF-1.7\nfixture\n")
        for c in categories:
            z.writestr(f"categorias/{c}/index.html", noindex)
        for i in range(1541):
            z.writestr(f"productos/producto-{i}/index.html", noindex)
    return source, zpath


class Fase4EnsayoTests(unittest.TestCase):
    def test_montar_catalogo_sin_alterar_web(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            web, catalog = fixture(root)
            original = (web / "index.html").read_bytes()
            result = build(web, catalog, root / "salida")
            self.assertEqual(result["estado"], "ENSAYO_VERIFICADO")
            self.assertEqual(result["paginas_catalogo"], 1558)
            self.assertEqual(result["enlaces_streamlit_sustituidos"], 13)
            self.assertEqual(result["sitemap_candidato_total"], 1565)
            self.assertEqual(result["enlaces_internos_rotos"], 0)
            self.assertFalse(result["publicado"])
            self.assertEqual((web / "index.html").read_bytes(), original)
            self.assertFalse((root / "salida" / "sitio" / "CNAME").exists())
            home = (root / "salida" / "sitio" / "index.html").read_text()
            self.assertNotIn(STREAMLIT, home)
            self.assertIn("noindex,nofollow", home)
            with ZipFile(root / "salida" / "BONVI_Fase4_Ensayo_Privado_NO_PUBLICAR.zip") as z:
                self.assertIn("catalogo/index.html", z.namelist())
                self.assertNotIn("CNAME", z.namelist())

    def test_no_sobrescribe_ensayos(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            web, catalog = fixture(root)
            out = root / "ocupada"
            out.mkdir()
            with self.assertRaisesRegex(ValueError, "ya existe"):
                build(web, catalog, out)

    def test_falta_cat_frena_ensayo(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            web, catalog = fixture(root)
            (web / "vinos-la-plata" / "index.html").unlink()
            with self.assertRaises(FileNotFoundError):
                build(web, catalog, root / "salida")


if __name__ == "__main__":
    unittest.main()
