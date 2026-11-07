import tempfile
import unittest
from pathlib import Path
from validar_sincronizacion import compare, load, approved_fingerprint

def item(code='1',price=6000,uxb=6,kind='bulto'):
    return {'codigo':code,'nombre':'VINO','familia':'VINOS','categoria':'VINOS',
            'presentacion':'750 ml','marca':'BODEGA','tipo':kind,'uxb':uxb,
            'precio':price,'unitario':price/uxb if kind=='bulto' else price,
            'imagen':'','imagen_categoria':'','icono_categoria':'🍷','slug':'vino-'+code}

class SyncTests(unittest.TestCase):
    def test_sin_cambios(self):
        self.assertEqual(compare({'1':item()},{'1':item()})['estado'],'SIN_ALERTAS_AUTOMATICAS')
    def test_precio(self):
        self.assertEqual(compare({'1':item()},{'1':item(price=9000)})['estado'],'REVISAR')
    def test_alta(self):
        self.assertEqual(compare({'1':item()},{'1':item(),'2':item('2')})['estado'],'REVISAR')
    def test_modalidad(self):
        self.assertEqual(compare({'1':item()},{'1':item(price=1000,uxb=1,kind='unidad')})['estado'],'REVISAR')
    def test_campos_internos(self):
        import json
        with tempfile.TemporaryDirectory() as temp:
            f=Path(temp)/'index.html'
            f.write_text('<meta content="noindex,nofollow"><script>const products='+json.dumps([item()])+';\nconst aliases={};</script>')
            self.assertEqual(len(load(f)),1)
            bad=item();bad['costo_unitario']=100
            f.write_text('<meta content="noindex,nofollow"><script>const products='+json.dumps([bad])+';\nconst aliases={};</script>')
            with self.assertRaises(ValueError):load(f)

    def test_huella_de_copia_independiente_del_orden(self):
        import json
        with tempfile.TemporaryDirectory() as temp:
            one=Path(temp)/'a.html'
            two=Path(temp)/'b.html'
            prefix='<meta content="noindex,nofollow"><script>const products='
            suffix=';\\nconst aliases={};</script>'
            first=item('1')
            second=item('2')
            one.write_text(prefix+json.dumps([first,second])+suffix)
            two.write_text(prefix+json.dumps([second,first])+suffix)
            self.assertEqual(approved_fingerprint(one),approved_fingerprint(two))
            second['precio']=12000
            second['unitario']=2000
            two.write_text(prefix+json.dumps([second,first])+suffix)
            self.assertNotEqual(approved_fingerprint(one),approved_fingerprint(two))

if __name__=='__main__':unittest.main()
