"""Fase 3: pruebas SEO locales sin conexión externa ni despliegue."""
import unittest
from bonvi_fase3_seo_privado import (slug, seo_tags, modify_existing_page, category_html)

class SEOPrivadoTests(unittest.TestCase):
    def test_slugs_legibles(self):
        self.assertEqual(slug('ANÍS Y LICORES'), 'anis-y-licores')
        self.assertEqual(slug('RON Y CACHAÇA'), 'ron-y-cachaca')

    def test_metadatos_y_rutas_estructuradas(self):
        base='https://bonvimercat.com.ar/catalogo/'
        tags=seo_tags('Vino prueba', 'Descripción de prueba',
                      base+'productos/prueba/', [('Catálogo',base), ('Prueba',base+'productos/prueba/')])
        self.assertIn('rel="canonical"', tags)
        self.assertIn('"@type":"BreadcrumbList"', tags)
        self.assertIn('og:title', tags)
        self.assertNotIn('availability', tags)
        self.assertNotIn('"@type":"Offer"', tags)

    def test_reemplazo_en_head_y_noindex_permanente(self):
        doc='<html><head><meta name="robots" content="noindex,nofollow"><title>Anterior</title><meta name="description" content="Vieja"><link rel="canonical" href="https://bonvimercat.com.ar/productos/antigua/"></head><body><h1>Hola</h1></body></html>'
        revised=modify_existing_page(doc, 'Título nuevo', 'Descripción nueva',
                 'https://bonvimercat.com.ar/catalogo/productos/nuevo/',
                 [('Catálogo','https://bonvimercat.com.ar/catalogo/')])
        self.assertEqual(revised.count('rel="canonical"'),1)
        self.assertEqual(revised.count('name="description"'),1)
        self.assertIn('noindex,nofollow',revised)
        self.assertIn('<h1>Hola</h1>',revised)

    def test_no_permite_quitar_noindex(self):
        with self.assertRaisesRegex(ValueError, 'noindex'):
            modify_existing_page('<html><head><title>Algo</title></head></html>',
                  'Nuevo','Desc','https://bonvimercat.com.ar/catalogo/',[])

    def test_pagina_categoria_html_statico(self):
        row={'slug':'malbec-123','nombre':'Malbec 750','precio':6000,'tipo':'bulto','uxb':6}
        page=category_html('VINOS',[row],
             'https://bonvimercat.com.ar/catalogo/categorias/vinos/',
             'https://bonvimercat.com.ar/catalogo/')
        self.assertIn('malbec-123/index.html',page)
        self.assertIn('noindex',page)
        self.assertIn('$ 6.000',page)
        self.assertIn('application/ld+json',page)

if __name__=='__main__':
    unittest.main()
