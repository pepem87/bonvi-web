"""Pruebas de regresión del índice privado; no necesitan base de datos."""
import tempfile
import unittest
from pathlib import Path

from catalogo_indice import index_html, public_product, write_preview


def sample(code="101", mode="BULTO", uxb=6, unit=2500):
    return {
        "codigo": code,
        "producto": "VINO MALBEC 750ML",
        "familia": "VINOS",
        "categoria": "VINOS",
        "marca": "BODEGA",
        "presentacion": "750 ml",
        "modalidad": mode,
        "uxb": uxb,
        "precio_persona_unit": unit,
        "imagen_categoria": "assets/category_placeholders/vinos.webp",
    }


class CatalogoIndiceTests(unittest.TestCase):
    def test_precio_bulto_y_unidad(self):
        bulk = public_product(sample())
        single = public_product(sample("102", "UNIDAD"))
        self.assertEqual(bulk["precio"], 15000)
        self.assertEqual(bulk["unitario"], 2500)
        self.assertEqual(bulk["tipo"], "bulto")
        self.assertEqual(single["precio"], 2500)
        self.assertEqual(single["tipo"], "unidad")

    def test_bulto_con_uxb_uno_se_publica_por_unidad(self):
        # Códigos reales de Supabase: 1410, 1582, 1947.
        for codigo in ("1410", "1582", "1947"):
            with self.subTest(codigo=codigo):
                row = sample(code=codigo, mode="BULTO", uxb=1, unit=46750)
                product = public_product(row)
                self.assertEqual(product["tipo"], "unidad")
                self.assertEqual(product["precio"], 46750)
                self.assertEqual(product["uxb"], 1)

    def test_no_incluir_costos_internos(self):
        row = sample()
        row["costo_unitario"] = 1000
        row["precio_comercio_unit"] = 1800
        row["margen"] = 0.25
        product = public_product(row)
        self.assertNotIn("costo_unitario", product)
        self.assertNotIn("precio_comercio_unit", product)
        self.assertNotIn("margen", product)

    def test_indice_replica_filtros_y_paginacion(self):
        product = public_product(sample())
        doc = index_html([product], pdf_path="catalogo-personas.pdf",
                         search_aliases={"vino": "VINOS"},
                         category_icons={"VINOS": "assets/button_icons/vinos.webp"},
                         vigencia_marker="2026-11-06", logo_path="assets/logo_bon_vi_mercat.png",
                         background_path="assets/web_mockup.png")
        for snippet in ("noindex,nofollow", "perPage=80", "HASTA $10.000",
                        "PRECIO UNITARIO", "PRECIO DE VENTA", "topPager",
                        "bottomPager", "CATÁLOGO ACTUALIZADO", "assets/button_icons/vinos.webp",
                        "catalogo-personas.pdf", "const aliases=",
                        "Vigente hasta 06/11/2026", "assets/logo_bon_vi_mercat.png",
                        "assets/web_mockup.png"):
            with self.subTest(snippet=snippet):
                self.assertIn(snippet, doc)
        self.assertNotIn("__PRODUCTS__", doc)
        self.assertNotIn("__ALIASES__", doc)
        self.assertNotIn("__CHIPS__", doc)

    def test_ruta_imagen_no_permite_archivos_arbitrarios(self):
        row = sample()
        row["imagen_categoria"] = "../../secreto"
        with self.assertRaises(ValueError):
            public_product(row)

    def test_exportacion_privada_con_fichas(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "salida"
            n = write_preview([sample()], root,
                              search_aliases={"vino": "VINOS"})
            self.assertEqual(n, 1)
            self.assertTrue((root / "index.html").exists())
            self.assertTrue((root / "productos" / "vino-malbec-750ml-101" / "index.html").exists())
            with self.assertRaises(ValueError):
                write_preview([sample()], root)


if __name__ == "__main__":
    unittest.main()
