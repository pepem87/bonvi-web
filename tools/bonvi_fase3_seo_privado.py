#!/usr/bin/env python3
"""BON VI Fase 3: SEO privado sobre el ZIP aprobado. Nunca publica.

Genera un paquete navegable noindex, 16 páginas de categoría y un sitemap
CANDIDATO fuera del paquete. No se conecta a Supabase ni toca Streamlit.
"""
import argparse
from collections import Counter, defaultdict
from datetime import date
import html
import json
from pathlib import Path
import re
import shutil
import tempfile
from urllib.parse import urljoin, urlsplit
from xml.etree import ElementTree as ET
from zipfile import ZipFile, ZIP_DEFLATED

PATTERN = re.compile(r'const products=(\[.*?\]);\s*const aliases=', re.DOTALL)
META_ROBOTS = re.compile(r'<meta\s+name="robots"\s+content="[^"]+"\s*/?>', re.I)
CANONICAL = re.compile(r'<link\s+rel="canonical"\s+href="[^"]+"\s*/?>', re.I)
META_DESC = re.compile(r'<meta\s+name="description"\s+content="[^"]*"\s*/?>', re.I)
TITLE = re.compile(r'<title>.*?</title>', re.I | re.S)
HOST = 'https://bonvimercat.com.ar/catalogo/'


def esc(value):
    return html.escape(str(value), quote=True)


def slug(text):
    import unicodedata
    a = unicodedata.normalize('NFKD', text)
    return re.sub(r'-+', '-', re.sub('[^a-z0-9]+', '-', ''.join(x for x in a if not unicodedata.combining(x)).lower())).strip('-')


def price(value):
    return '$ ' + format(round(float(value)), ',').replace(',', '.')


def safe_json(x):
    return json.dumps(x, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')


def seo_tags(title, description, canonical, crumb, website=False):
    meta = ('<meta name="description" content="' + esc(description) + '">\n'
            '<link rel="canonical" href="' + esc(canonical) + '">\n'
            '<meta property="og:locale" content="es_AR">\n'
            '<meta property="og:type" content="' + ('website' if website else 'article') + '">\n'
            '<meta property="og:title" content="' + esc(title) + '">\n'
            '<meta property="og:description" content="' + esc(description) + '">\n'
            '<meta property="og:url" content="' + esc(canonical) + '">\n'
            '<meta name="twitter:card" content="summary">\n')
    breadcrumb = {'@context':'https://schema.org','@type':'BreadcrumbList',
                  'itemListElement':[{'@type':'ListItem', 'position':i+1, 'name':name,
                                      'item':url} for i,(name,url) in enumerate(crumb)]}
    return meta + '<script type="application/ld+json">' + safe_json(breadcrumb) + '</script>\n'


def get_products(index_path):
    doc = index_path.read_text('utf-8')
    m = PATTERN.search(doc)
    if not m:
        raise ValueError('No se encontró el catálogo real de productos')
    items = json.loads(m.group(1))
    codes, slugs = set(), set()
    for p in items:
        code, path = str(p['codigo']), p['slug']
        if code in codes or path in slugs or not re.fullmatch('[a-z0-9-]+',path):
            raise ValueError('Código o slug duplicado/inválido')
        codes.add(code); slugs.add(path)
    if len(items)!=1541:
        raise ValueError('La referencia aprobada debe contener los 1541 productos')
    return items


def modify_existing_page(content, title, description, canonical, crumbs, website=False):
    if not META_ROBOTS.search(content) or 'noindex' not in META_ROBOTS.search(content).group():
        raise ValueError('No se publica una copia sin protección noindex')
    if TITLE.search(content) is None:
        raise ValueError('Página sin título')
    content = TITLE.sub('<title>' + esc(title) + '</title>', content, count=1)
    content = META_DESC.sub('', content, count=1)
    content = CANONICAL.sub('', content, count=1)
    metadata = seo_tags(title,description,canonical,crumbs,website)
    return content.replace('</head>', metadata+'</head>',1)


def category_html(label, members, canonical, base_url):
    title = f'{label.title()} en La Plata | BON VI MERCAT'
    description = f'Explorá {len(members)} productos de {label.lower()} en el catálogo de BON VI MERCAT. Consultá precios, presentaciones y venta por bulto o unidad en La Plata.'
    entries = '\n'.join('<li><a href="../../productos/' + esc(p['slug']) + '/index.html">' +
                         esc(p['nombre']) + '</a> · ' + esc(price(p['precio'])) +
                         (' por bulto x' + str(p['uxb']) if p['tipo']=='bulto' else ' por unidad') + '</li>' for p in members)
    crumbs=[('Catálogo',base_url),(label.title(),canonical)]
    return ('<!doctype html>\n<html lang="es-AR"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            '<meta name="robots" content="noindex,nofollow">'
            '<title>'+esc(title)+'</title>'+seo_tags(title,description,canonical,crumbs,website=True)+
            '<style>body{font:16px system-ui;margin:0;color:#294a3c;background:#f5f0e6}'
            'header{background:#294a3c;padding:22px;color:white}header a{color:white}'
            'main{max-width:840px;margin:auto;padding:24px}h1{font-family:Georgia,serif}'
            'li{background:#fffdf8;border:1px solid #e2dbcd;margin:7px 0;padding:11px 14px;list-style:none;border-radius:8px}'
            'li a{color:#294a3c}ul{padding:0}</style></head><body>'
            '<header><a href="../../index.html">BON VI MERCAT · Volver al catálogo</a></header>'
            '<main><h1>'+esc(label.title())+'</h1><p>Productos disponibles para consultar. '
            'Precios sujetos a confirmación.</p><p><strong>'+str(len(members))+' productos</strong></p>'
            '<ul>'+entries+'</ul><p><a href="../../index.html">Volver al catálogo completo</a></p></main></body></html>')


def build(source_zip, target_zip, review_dir, base_url=HOST):
    base_url=base_url.rstrip('/')+'/'
    u=urlsplit(base_url)
    if u.scheme!='https' or u.netloc!='bonvimercat.com.ar' or u.path!='/catalogo/':
        raise ValueError('URL canónica restringida a https://bonvimercat.com.ar/catalogo/')
    source_zip,target_zip,review_dir=Path(source_zip),Path(target_zip),Path(review_dir)
    if not source_zip.is_file() or target_zip.exists():
        raise ValueError('ZIP original faltante o destino ya existe; nunca se sobrescribe')
    if review_dir.exists() and any(review_dir.iterdir()):
        raise ValueError('Carpeta de revisión no vacía')
    with tempfile.TemporaryDirectory(prefix='bonvi-f3-') as d:
        folder=Path(d)
        with ZipFile(source_zip) as z:
            for info in z.infolist():
                name=Path(info.filename)
                if name.is_absolute() or '..' in name.parts or '\\' in info.filename or (info.external_attr>>16)&0o170000==0o120000:
                    raise ValueError('ZIP contiene ruta o enlace inseguro')
            z.extractall(folder)
        index=folder/'index.html'
        products=get_products(index)
        groups=defaultdict(list)
        urls=[base_url]
        index_text=index.read_text('utf-8')
        categories=sorted({p['categoria'] for p in products})
        if len(categories)!=16:
            raise ValueError('Cambió la clasificación base de 16 categorías')
        catalog_urls={cat:urljoin(base_url,'categorias/'+slug(cat)+'/') for cat in categories}
        for p in products:
            groups[p['categoria']].append(p)
        index_title='Catálogo de bebidas, vinos y aceites en La Plata | BON VI MERCAT'
        index_desc=('Conocé el catálogo de BON VI MERCAT en La Plata: vinos, champagnes, cervezas, aperitivos, whiskys, aceites y acetos. Consultá precios por bulto o unidad.')
        index_text=modify_existing_page(index_text,index_title,index_desc,base_url,[('Catálogo',base_url)],True)
        # Enlaces HTML reales para rastreadores: el JS anterior del buscador se conserva intacto.
        links='\n'.join('<li><a href="categorias/'+esc(slug(cat))+'/index.html">'+esc(cat.title())+' ('+str(len(groups[cat]))+')</a></li>' for cat in categories)
        nav=('<details style="margin:16px auto;max-width:840px;padding:12px 18px;border:1px solid #d4cbb7;border-radius:12px;background:#fffdf8">'
             '<summary style="cursor:pointer;font-weight:bold">Explorar todas las categorías del catálogo</summary>'
             '<nav aria-label="Categorías del catálogo"><ul>'+links+'</ul></nav></details>')
        if '</footer>' not in index_text:
            raise ValueError('La portada no contiene cierre de footer')
        index_text=index_text.replace('</footer>', '</footer>'+nav,1)
        index.write_text(index_text,'utf-8')
        for cat in categories:
            cat_dir=folder/'categorias'/slug(cat)
            cat_dir.mkdir(parents=True,exist_ok=True)
            cat_url=catalog_urls[cat]
            (cat_dir/'index.html').write_text(category_html(cat,groups[cat],cat_url,base_url),'utf-8')
            urls.append(cat_url)
        for p in products:
            url=urljoin(base_url,'productos/'+p['slug']+'/')
            path=folder/'productos'/p['slug']/'index.html'
            if not path.is_file():
                raise ValueError('Ficha faltante: '+p['slug'])
            cur=path.read_text('utf-8')
            mode=('bulto de '+str(p['uxb'])+' unidades' if p['tipo']=='bulto' else 'unidad')
            title=p['nombre'].strip()+' | BON VI MERCAT La Plata'
            desc=(p['nombre'].strip()+' · '+p['categoria'].lower()+' en BON VI MERCAT. '+
                  'Precio por '+mode+': '+price(p['precio'])+'. Consultá disponibilidad en La Plata.')
            crumbs=[('Catálogo',base_url),(p['categoria'].title(),catalog_urls[p['categoria']]),(p['nombre'],url)]
            cur=modify_existing_page(cur,title,desc,url,crumbs)
            # El breadcrumb ahora enlaza a una categoría real y a la portada.
            cur=re.sub(r'<p class="crumb">.*?</p>',
                       '<p class="crumb"><a href="../../index.html">Catálogo</a> / '
                       '<a href="../../categorias/'+esc(slug(p['categoria']))+'/index.html">'+esc(p['categoria'].title())+'</a></p>',cur,count=1,flags=re.S)
            path.write_text(cur,'utf-8')
            urls.append(url)
        # Auditar la copia privada exhaustivamente.
        html_pages=list(folder.rglob('index.html'))
        if len(html_pages)!=1558 or len(urls)!=1558:
            raise ValueError(f'Número inesperado de HTML o URLs: {len(html_pages)} / {len(urls)}')
        if len(set(urls))!=len(urls):
            raise ValueError('URLs canónicas duplicadas')
        for page in html_pages:
            doc=page.read_text('utf-8')
            if not META_ROBOTS.search(doc) or 'noindex' not in META_ROBOTS.search(doc).group():
                raise ValueError('Página privada indexable: '+str(page))
            if not META_DESC.search(doc) or not CANONICAL.search(doc):
                raise ValueError('Metadatos SEO incompletos: '+str(page))
            if len(re.findall('rel="canonical"',doc))!=1:
                raise ValueError('Canónicas repetidas: '+str(page))
            if 'application/ld+json' not in doc:
                raise ValueError('Falta ruta estructurada: '+str(page))
        # Sitemap solo para revisión, fuera del paquete navegable.
        ET.register_namespace('','http://www.sitemaps.org/schemas/sitemap/0.9')
        root=ET.Element('{http://www.sitemaps.org/schemas/sitemap/0.9}urlset')
        for url in urls:
            node=ET.SubElement(root,'{http://www.sitemaps.org/schemas/sitemap/0.9}url')
            ET.SubElement(node,'{http://www.sitemaps.org/schemas/sitemap/0.9}loc').text=url
        review_dir.mkdir(parents=True,exist_ok=True)
        sitemap=review_dir/'sitemap-CANDIDATO-NO-PUBLICAR.xml'
        ET.ElementTree(root).write(sitemap,encoding='utf-8',xml_declaration=True)
        report={
            'fase':'3 - SEO EN DESARROLLO / NO PUBLICADO', 'producto_referencia':len(products),
            'fichas_producto':1541,'paginas_categoria':16,'total_urls_candidatas':len(urls),
            'pagina_catalogo_prevista':base_url,'paginas_privadas_noindex':len(html_pages),
            'sitemap':'CANDIDATO FUERA DEL ZIP PRIVADO, NO SUBIDO A GOOGLE',
            'product_schema':'NO AÑADIDO: sin fotografías verificadas ni disponibilidad comprobada',
            'robots_txt':'NO MODIFICADO','sitemap_publico':'NO MODIFICADO',
            'web_publica':'NO MODIFICADA','supabase':'NO MODIFICADA','streamlit':'NO MODIFICADO',
            'categorias':dict(sorted(Counter(p['categoria'] for p in products).items())),
            'recomendaciones_antes_de_publicar':[
                'Aprobar el diseño SEO y la ruta /catalogo/ dentro de bonvimercat.com.ar',
                'Quitar noindex solamente al publicar las URLs finales correctas',
                'Integrar sitemap candidato al sitemap real sin sustituir URLs existentes',
                'Validar enlaces, estado HTTP 200, Search Console e indexabilidad real',
                'Revisar imágenes reales por SKU antes de considerar Product rich results',
            ]
        }
        (review_dir/'informe-seo-fase3.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8')
        with ZipFile(target_zip,'w',compression=ZIP_DEFLATED,compresslevel=6) as zz:
            for f in sorted(folder.rglob('*')):
                if f.is_file(): zz.write(f,f.relative_to(folder))
        with ZipFile(target_zip) as zz:
            if zz.testzip() is not None: raise ValueError('ZIP inválido')
        return report


def main():
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument('--source',required=True)
    a.add_argument('--target',required=True)
    a.add_argument('--review-dir',required=True)
    x=a.parse_args()
    print(json.dumps(build(x.source,x.target,x.review_dir),ensure_ascii=False,indent=2))

if __name__=='__main__':main()