"""Pruebas offline de Fase 2. No consultan Supabase ni modifican Streamlit."""
import json
from pathlib import Path
import tempfile
import unittest

from reportlab.pdfgen import canvas
from fase2_generar_paquete_privado import (
    load_public_html, compare_approved, audit_package,
)


def item(code="101", price=6000, category="VINOS", mode="bulto", qty=6):
    return {
        "codigo": code, "nombre": "VINO MALBEC 750ML", "familia": "VINOS",
        "categoria": category, "presentacion": "750 ml", "marca": "BODEGA",
        "tipo": mode, "uxb": qty, "precio": price,
        "unitario": price / (qty if mode == "bulto" else 1),
        "imagen": "", "imagen_categoria": "assets/category_placeholders/vinos.webp",
        "icono_categoria": "🍷", "slug": "vino-" + code,
    }


def write_html(path, products):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        '<meta name="robots" content="noindex,nofollow"><script>\n'
        + "const products=" + json.dumps(products, ensure_ascii=False)
        + ";\nconst aliases={};</script>\n",
        encoding="utf-8",
    )



def test_pdf(path, rows):
    """PDF sintético de dos páginas: códigos y precios en líneas separadas."""
    pdf = canvas.Canvas(str(path), pagesize=(595, 842))
    for i in range(2):
        pdf.setTitle("BON VI - CATÁLOGO PRUEBA")
        if i < len(rows):
            item = rows[i]
            pdf.drawString(52, 780, item["codigo"])
            for j, key in enumerate(("unitario", "precio")):
                price = "$ " + format(item[key], ",.0f").replace(",", ".")
                pdf.drawString(65, 745 - j * 30, price)
        pdf.showPage()
    pdf.save()


def valid_package(folder, rows):
    root = Path(folder)
    write_html(root / "index.html", rows)
    for p in rows:
        path = root / "productos" / p["slug"] / "index.html"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('<meta name="robots" content="noindex,nofollow">', encoding="utf-8")
    required = [
        "assets/logo_bon_vi_mercat.png", "assets/web_mockup.png",
        *["assets/button_icons/" + c + ".webp" for c in
          ("vinos", "champagnes", "cervezas", "jugos", "whiskys",
           "aperitivos", "aceites", "otros")],
    ]
    for name in required:
        p = root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"fixture-graphic")
    test_pdf(root / "catalogo-personas.pdf", rows)
    (root / "control-privado.json").write_text(
        json.dumps({"productos": len(rows), "pdf_productos": len(rows),
                    "vigencia": "2026-11-07", "errores": []}),
        encoding="utf-8",
    )


class Fase2PaquetePrivadoTests(unittest.TestCase):
    def test_igualdad_sin_publicar(self):
        with tempfile.TemporaryDirectory() as d:
            html = Path(d) / "approved.html"
            write_html(html, [item()])
            a = load_public_html(html)
            comparison = compare_approved(a, a)
            self.assertEqual(comparison["estado"], "IGUAL_A_APROBADO")
            self.assertFalse(comparison["publicacion_autorizada"])

    def test_detectar_precio_y_modalidad(self):
        base = {"101": item()}
        price = {"101": item(price=6600)}
        self.assertEqual(compare_approved(base, price)["cambios_precio"], 1)
        mode = {"101": item(mode="unidad", qty=1, price=1200)}
        self.assertEqual(compare_approved(base, mode)["cambios_modalidad_uxb"], 1)

    def test_detectar_altas_y_bajas(self):
        result = compare_approved({"101": item()}, {"202": item(code="202")})
        self.assertEqual(result["altas"], 1)
        self.assertEqual(result["bajas"], 1)

    def test_campo_de_costo_prohibido(self):
        with tempfile.TemporaryDirectory() as d:
            html = Path(d) / "catalog.html"
            row = item()
            row["costo_unitario"] = 100
            write_html(html, [row])
            with self.assertRaises(ValueError):
                load_public_html(html)

    def test_precio_de_bulto_consistente(self):
        with tempfile.TemporaryDirectory() as d:
            html = Path(d) / "catalog.html"
            row = item()
            row["precio"] = 500
            write_html(html, [row])
            with self.assertRaisesRegex(ValueError, "Precio de venta"):
                load_public_html(html)

    def test_audita_fichas_pdf_e_ilustraciones(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "new"
            approved = Path(d) / "approved.html"
            data = [item(), item(code="102", price=12000)]
            valid_package(root, data)
            write_html(approved, data)
            report = audit_package(root, approved)
            self.assertEqual(report["fichas_verificadas"], 2)
            self.assertEqual(report["pdf_paginas"], 2)
            self.assertEqual(report["estado"], "IGUAL_A_APROBADO")
            self.assertFalse(report["publicacion_autorizada"])

    def test_auditoria_bloquea_precio_erroneo_en_pdf(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "new"
            approved = Path(d) / "approved.html"
            data = [item()]
            valid_package(root, data)
            write_html(approved, data)
            test_pdf(root / "catalogo-personas.pdf", [item(price=6600)])
            with self.assertRaisesRegex(ValueError, "Precios del PDF divergentes"):
                audit_package(root, approved)

    def test_auditoria_detecta_una_ficha_ausente(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "new"
            approved = Path(d) / "approved.html"
            data = [item(), item(code="102")]
            valid_package(root, data)
            write_html(approved, data)
            (root / "productos" / data[0]["slug"] / "index.html").unlink()
            with self.assertRaisesRegex(ValueError, "Fichas"):
                audit_package(root, approved)

    def test_auditoria_compara_cambio_sin_bloquear_regeneracion_privada(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "new"
            approved = Path(d) / "approved.html"
            data = [item(price=6600)]
            valid_package(root, data)
            write_html(approved, [item()])
            report = audit_package(root, approved)
            self.assertEqual(report["estado"], "CAMBIOS_PARA_REVISAR")
            self.assertEqual(report["cambios_precio"], 1)


if __name__ == "__main__":
    unittest.main()
