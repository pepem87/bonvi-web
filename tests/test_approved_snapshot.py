"""Pruebas locales: solo se exportan precios públicos de una L7 aprobada."""
from unittest import TestCase
from unittest.mock import patch
from pathlib import Path
import importlib.util

path=Path(__file__).resolve().parents[1]/"scripts"/"fetch_approved_snapshot.py"
spec=importlib.util.spec_from_file_location("public_snap",path)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class PublicacionL7(TestCase):
    def test_aprobada_filtro_y_precio_personas(self):
        def fake(resource,query):
            if resource=="cargas_l7": return [{"id":20,"estado":"APROBADA","vigencia":"2026-11-27T18:08:07Z"}]
            if resource=="parametros": return [{"valor":"2026-11-27T18:08:07Z"}]
            return [
                {"codigo":1409,"producto":"LA BANDE","familia":"VINOS",
                 "presentacion":"ESTUCHE 3","uxb":3,"modalidad":"BULTO",
                 "precio_persona_unit":8100.0,"rol":"SIN REF","orden_l7":1},
                {"codigo":174,"producto":"LOBO NEGRO","familia":"VINOS",
                 "presentacion":"750ML","uxb":6,"modalidad":"BULTO",
                 "precio_persona_unit":10000,"rol":"BLOQUEADO","orden_l7":2}
            ]
        with patch.object(m,"api_get",side_effect=fake):
            snap=m.collect()
        self.assertEqual(snap["meta"]["id"],20)
        self.assertEqual(snap["meta"]["n"],1)
        self.assertEqual(snap["rows"],[[1409,"LA BANDE","VINOS","ESTUCHE 3",3,"BULTO","8100.00",1]])
        self.assertNotIn("costo_unitario",str(snap))
        self.assertNotIn("precio_comercio",str(snap))

    def test_no_publicar_sin_aprobacion(self):
        with patch.object(m,"api_get",side_effect=[
            [{"id":20,"estado":"PENDIENTE","vigencia":"x"}],[{"valor":"x"}]
        ]):
            with self.assertRaises(RuntimeError):
                m.collect()

    def test_detectar_cambio_de_version_durante_lectura(self):
        def fake(resource,query):
            if resource=="productos": return [{"codigo":1,"producto":"VINO","familia":"VINOS",
                "presentacion":"750 ML","uxb":6,"modalidad":"BULTO",
                "precio_persona_unit":1500,"rol":"NORMAL","orden_l7":1}]
            if resource=="cargas_l7":
                fake.n+=1
                return [{"id":20 if fake.n==1 else 21,"estado":"APROBADA","vigencia":"x"}]
            return [{"valor":"x"}]
        fake.n=0
        with patch.object(m,"api_get",side_effect=fake):
            with self.assertRaises(RuntimeError):
                m.collect()
