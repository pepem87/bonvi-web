"""Regresión del comparador aislado: no necesita SQL, secretos ni Streamlit."""
import unittest
from pathlib import Path
from comparar_actualizacion_privada import archived_rows, compare, normalize

ROOT = Path(__file__).resolve().parents[1]


def sample(code="101", mode="BULTO", uxb=6, price=2500, family="VINOS"):
    return {
        "codigo": code, "producto": "VINO MALBEC 750ML",
        "familia": family, "presentacion": "750 ml",
        "uxb": uxb, "modalidad": mode,
        "precio_persona_unit": price, "orden_l7": 1,
    }


class CompararAisladoTests(unittest.TestCase):
    def test_igualdad_sin_cambios(self):
        p = sample()
        result = compare([p], [dict(p)])
        self.assertEqual(result["estado"], "IGUAL_A_REFERENCIA")
        self.assertEqual(result["altas"], 0)
        self.assertFalse(result["publicacion_autorizada"])

    def test_detecta_cambio_de_precio_sin_publicar(self):
        base = sample()
        updated = dict(base, precio_persona_unit=2600)
        result = compare([base], [updated])
        self.assertEqual(result["productos_precio_modificado"], 1)
        self.assertEqual(result["estado"], "CAMBIOS_PARA_REVISAR")
        self.assertFalse(result["publicacion_autorizada"])

    def test_detecta_uxb_y_modalidad(self):
        result = compare([sample()], [sample(mode="UNIDAD", uxb=1)])
        self.assertEqual(result["productos_modalidad_uxb_modificados"], 1)
        self.assertEqual(result["productos_precio_modificado"], 1)

    def test_bulto_uxb_uno_es_unidad(self):
        for code in ("1410", "1582", "1947"):
            data = normalize([sample(code, uxb=1)])
            self.assertEqual(data[code]["modalidad"], "unidad")
            self.assertEqual(data[code]["precio_venta"], 2500)

    def test_nunca_permita_costos_ni_campos_no_autorizados(self):
        row = sample()
        row["costo_unitario"] = 42
        with self.assertRaisesRegex(ValueError, "no publicables"):
            normalize([row])

    def test_rechaza_codigos_duplicados(self):
        with self.assertRaisesRegex(ValueError, "repetido"):
            normalize([sample(), sample()])

    def test_rechaza_uxb_invalido(self):
        with self.assertRaisesRegex(ValueError, "UxB"):
            normalize([sample(uxb=2.4)])

    def test_detecta_altas_y_bajas(self):
        report = compare([sample("101")], [sample("102")])
        self.assertEqual(report["altas"], 1)
        self.assertEqual(report["bajas"], 1)
        self.assertEqual(report["estado"], "CAMBIOS_PARA_REVISAR")

    def test_referencia_real_aprobada_sin_cambios(self):
        rows = archived_rows(ROOT / "preview" / "datos")
        self.assertEqual(len(rows), 1541)
        result = compare(rows, rows)
        self.assertEqual(result["estado"], "IGUAL_A_REFERENCIA")
        self.assertEqual(result["total_base"], 1541)
        self.assertEqual(result["total_nuevo"], 1541)


if __name__ == "__main__":
    unittest.main()
