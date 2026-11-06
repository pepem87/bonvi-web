import unittest
from pathlib import Path
import importlib.util

script = Path(__file__).with_name("catalogo_preview.py")
spec = importlib.util.spec_from_file_location("catalogo_preview", script)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class CatalogoTests(unittest.TestCase):
    def test_slug(self):
        self.assertEqual(mod.slug("Vino Ñandú 750 ml"), "vino-nandu-750-ml")

    def test_price(self):
        self.assertEqual(mod.format_price(12345.5), "$ 12.345,50")

    def test_safe_html(self):
        item = dict(codigo=10, producto="Vino & Co", familia="Vinos",
                    presentacion="750 ml", modalidad="BULTO",
                    precio_persona_unit=1200, slug="vino-co-10")
        page = mod.make_page(item)
        self.assertIn("Vino &amp; Co", page)
        self.assertIn("noindex,nofollow", page)
        self.assertIn("wa.me/5492216816892", page)

if __name__ == "__main__":
    unittest.main()
