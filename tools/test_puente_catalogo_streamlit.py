"""Pruebas sin DB y sin tocar Streamlit; correr: python -m unittest discover -s tools -p 'test_puente*.py'"""
import tempfile
import unittest
from pathlib import Path
from puente_catalogo_streamlit import load_rules, adapt_rows, export_private_json, verify_against_original

PDF_SOURCE = """
def _category_norm(value): return str(value or '').upper()
def _category_word(text, phrase): return phrase in text
def _category_starts(text, phrase): return text.startswith(phrase)
def _macro_category(family, product=''): return 'gin' if 'GIN' in product else 'vinos'
"""
PAGE_SOURCE = """
CATEGORY_TITLES = {'gin':'GIN','vinos':'VINOS'}
OTHER_PUBLIC_CATEGORIES = {'VARIADOS'}
KNOWN_BRAND_PREFIXES = ['BOMBAY']
PRICE_OPTIONS = ['TODOS']
PRICE_BASIS_OPTIONS = ['PRECIO UNITARIO']
POPULAR_CATEGORIES = ['VINOS']
SORT_OPTIONS = ['ORDEN DEL CATÁLOGO']
SEARCH_CATEGORY_ALIASES = {}
def normalize_text(value): return str(value or '').lower()
def public_category(family, product): return CATEGORY_TITLES[_macro_category(family, product)]
def public_brand(product): return product.split()[0]
def displayed_sale_price(item): return float(item['precio_unitario'])*(float(item['uxb']) if item['modalidad']=='BULTO' else 1)
def filter_price_value(item, basis): return item['precio_unitario']
def matches_public_category(a,b): return a==b
def price_filter_matches(a,b): return True
"""

class PuenteTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        (root / 'pages').mkdir()
        (root / 'pdf_catalogo.py').write_text(PDF_SOURCE, encoding='utf-8')
        (root / 'pages' / '0_📲_Catalogo_publico.py').write_text(PAGE_SOURCE, encoding='utf-8')
        self.rules = load_rules(root)
    def tearDown(self):
        self.temp.cleanup()
    def test_modalidad_y_exclusiones(self):
        rows = [
            {'codigo':'2','producto':'BOMBAY GIN','familia':'GIN PEDI POR UNIDAD','modalidad':'BULTO','uxb':6,'precio_persona_unit':3000,'orden_l7':2,'activo':1},
            {'codigo':'1','producto':'VINO MALBEC','familia':'BODEGA','modalidad':'BULTO','uxb':6,'precio_persona_unit':2000,'orden_l7':1,'activo':1},
            {'codigo':'3','producto':'VINO BLOQUEADO','familia':'BODEGA','modalidad':'UNIDAD','uxb':1,'precio_persona_unit':500,'rol':'BLOQUEADO','activo':1},
        ]
        data = adapt_rows(rows,self.rules)
        self.assertEqual([p['codigo'] for p in data],['1','2'])
        self.assertEqual(data[0]['precio_mostrado'],12000)
        self.assertEqual(data[1]['precio_mostrado'],3000)
        self.assertEqual(data[1]['categoria_publica'],'GIN')
        self.assertEqual(verify_against_original(rows,self.rules)['errores'],[])
    def test_export_sin_costos(self):
        row = {'codigo':'10','producto':'VINO','familia':'BODEGA','modalidad':'UNIDAD','uxb':1,'precio_persona_unit':1000,'costo':900,'margen':0.1,'activo':1}
        dest = Path(self.temp.name)/'catalog.json'
        self.assertEqual(export_private_json([row],self.rules,dest),1)
        data = dest.read_text(encoding='utf-8')
        self.assertNotIn('costo',data)
        self.assertNotIn('margen',data)
        with self.assertRaises(FileExistsError):
            export_private_json([row],self.rules,dest)

if __name__=='__main__': unittest.main()
