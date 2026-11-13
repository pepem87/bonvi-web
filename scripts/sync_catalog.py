"""Render only an approved public snapshot into a clean checkout of bonvi-web."""
import argparse
from collections import Counter, defaultdict
from datetime import datetime
from decimal import Decimal
import html
import json
from pathlib import Path
import re
import unicodedata
from zoneinfo import ZoneInfo
import xml.etree.ElementTree as ET

import fitz
from catalog_pdf import create_pdf, money

BASE = 'https://bonvimercat.com.ar/catalogo/'
RX = re.compile(r'const products=(\[.*?\]);\s*(?=const aliases=)', re.S)
ESC = html.escape

def slug(s):
    return re.sub(r'[^a-z0-9]+', '-', unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower()).strip('-')

def one(rx, replacement, s, flags=0):
    result, count = re.subn(rx, lambda _: replacement, s, flags=flags)
    if count != 1:
        raise ValueError(f'Template mismatch: {rx} ({count})')
    return result

def product_page(template, p, cat_slug, cat_name):
    old = 'BONVI_PRODUCT_TITLE'
    condition = f"Venta por bulto · {p['uxb']} unidades" if p['tipo']=='bulto' else 'Venta por unidad'
    description = f"{p['nombre']} · {cat_name.lower()} en BON VI MERCAT. {condition}: {money(p['precio'])}. Consultá disponibilidad en La Plata."
    url = BASE+'productos/'+p['slug']+'/'
    data = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', template)[1])
    data['itemListElement'][1].update(name=cat_name,item=BASE+'categorias/'+cat_slug+'/')
    data['itemListElement'][2].update(name=p['nombre'],item=url)
    template = one(r'<script type="application/ld\+json">.*?</script>', '<script type="application/ld+json">'+json.dumps(data,ensure_ascii=False).replace('<',r'\u003c')+'</script>', template)
    template = template.replace(BASE+'productos/bonvi-template-slug/', url)
    template = one(r'(?<=name="description" content=")[^"]+', ESC(description),template)
    template = one(r'(?<=property="og:description" content=")[^"]+', ESC(description),template)
    template = template.replace('categorias/vinos/index.html">Vinos', f'categorias/{cat_slug}/index.html">{ESC(cat_name)}')
    present = f"<p>{ESC(p['presentacion'])}</p>" if p['presentacion'] else ''
    ref = f'<p class="reference">Referencia: {money(p["unitario"])} por unidad</p>' if p['tipo']=='bulto' else ''
    return one(r'<h1>.*?</h1>\s*<p>750 ml</p><p class="condition">.*?</p>\s*<p class="price">.*?</p><p class="reference">.*?</p>',f'<h1>{ESC(p["nombre"])}</h1>\n{present}<p class="condition">{condition}</p>\n<p class="price">{money(p["precio"])}</p>{ref}',template).replace(old,ESC(p['nombre']))

def verify_pdf(path, products, date):
    expected = {p['codigo']: ('BULTO x'+str(p['uxb']) if p['tipo']=='bulto' else 'UNIDAD', money(p['unitario']), money(p['precio'])) for p in products}
    found={}
    with fitz.open(path) as doc:
        for page in doc:
            lines=[x.strip() for x in page.get_text().splitlines()]
            assert 'VIGENTE HASTA '+date in lines
            for i,s in enumerate(lines):
                if not re.fullmatch(r'\d+',s): continue
                prices=[x for x in lines[i+1:] if x]
                # PDF cell order: code, description, sale mode, unit price, total.
                j=next((j for j,x in enumerate(prices) if x=='UNIDAD' or re.fullmatch(r'BULTO x\d+',x)),None)
                if j is None or j>9 or j+2>=len(prices): continue
                if not all(re.fullmatch(r'\$ [\d.]+,\d{2}',x) for x in prices[j+1:j+3]): continue
                assert s not in found, ('duplicate PDF code',s)
                found[s]=tuple(prices[j:j+3])
        assert expected==found, (set(expected)^set(found),[c for c in expected.keys() & found.keys() if expected[c]!=found[c]][:20])
        return len(doc)

def run(root, snap, report):
    catroot=root/'catalogo'
    idx=catroot/'index.html'
    source=idx.read_text()
    base=json.loads(RX.search(source)[1])
    old={p['codigo']:p for p in base}
    meta=snap['meta']
    rows=snap['rows']
    assert meta['estado']=='APROBADA' and meta['vigencia']==meta['parametro'] and meta['n']==len(rows)>0
    date=datetime.fromisoformat(meta['vigencia']).astimezone(ZoneInfo('America/Argentina/Buenos_Aires')).strftime('%d/%m/%Y')
    category_pages={}
    for match in re.finditer(r'<li><a href="categorias/([^/]+)/index.html">([^<]+) \(\d+\)</a></li>',source):
        category_pages[match[1]]=html.unescape(match[2])
    cat_alias={'sin-alcohol-energizantes':'sin-alcohol-energizantes'}
    families=defaultdict(set)
    samples={}
    for p in base:
        families[slug(p['familia'])].add(p['categoria'])
        samples[p['categoria']]=p
    for f,cs in json.loads((root/'scripts/catalog_family_map.json').read_text()).items():
        families[f].update(cs)
    for f,c in json.loads((root/'scripts/catalog_family_overrides.json').read_text()).items():
        families[slug(f)]={c}
    categories={c:cat_alias.get(slug(c),slug(c)) for c in samples}
    assert set(categories.values())==set(category_pages)
    groups=defaultdict(list)
    products=[]
    seen=set()
    for code,name,family,presentation,units,mode,unit,order in sorted(rows,key=lambda r:(r[7] if r[7] is not None else 10**10,r[0])):
        assert isinstance(code,int) and code>0 and isinstance(units,int) and units>0 and mode in ('BULTO','UNIDAD') and name.strip() and family.strip()
        code=str(code)
        assert code not in seen
        seen.add(code)
        u=Decimal(unit)
        assert u.is_finite() and 0<u<10**9 and u==u.quantize(Decimal('.01'))
        prior=old.get(code)
        if prior:
            # Preserve editorial category and the indexed URL for an existing code.
            cat=prior['categoria']
        else:
            choices=families[slug(family)]
            if len(choices)!=1: raise ValueError(f'Categoría sin resolver para código {code} ({family})')
            cat=next(iter(choices))
        qty=units if mode=='BULTO' and units>1 else 1
        sample=samples[cat]
        icon=sample['imagen_categoria']
        if cat=='ACEITES':
            icon='assets/category_placeholders/'+('acetos' if re.search(r'\baceto\b',slug(name)) else 'aceites')+'.webp'
        p=dict(codigo=code,nombre=name,familia=family,categoria=cat,presentacion=presentation or '',
               marca=prior['marca'] if prior else name.split()[0].upper(),tipo='bulto' if qty>1 else 'unidad',uxb=qty,
               precio=float(u*qty),unitario=float(u),imagen=prior['imagen'] if prior else '',
               imagen_categoria=prior['imagen_categoria'] if prior else icon,
               icono_categoria=sample['icono_categoria'],slug=prior['slug'] if prior else slug(name)+'-'+code)
        assert categories[cat] in category_pages
        products.append(p)
        groups[cat].append(p)
    assert len({p['slug'] for p in products})==len(products)
    assert all(re.fullmatch('[a-z0-9-]+',p['slug']) for p in products)
    assets=['catalog-header','price-tooltip','info-trigger','Precio bulto x','id="search"','const perPage=80','catalogo-personas.pdf']
    assert all(x in source for x in assets)
    updated=one(r'Vigente hasta [^<]+</strong> · \d+ productos',f'Vigente hasta {date}</strong> · {len(products)} productos',source)
    updated=re.sub(r'(<li><a href="categorias/([^/]+)/index.html">[^<]+) \(\d+\)',lambda m: f'{m[1]} ({len(groups[next(c for c in categories if categories[c]==m[2])])})',updated)
    index_data=json.dumps(products,ensure_ascii=False,separators=(',',':')).replace('<',r'\u003c')
    updated=one(RX,f'const products={index_data};\n',updated)
    updated=one(r'const money=n=>[^\n]+', 'const money=n=>"$ "+Number(n).toLocaleString("es-AR",{maximumFractionDigits:2});',updated)
    assert all(x in updated for x in assets) and json.loads(RX.search(updated)[1])==products
    for p in products:
        for k in ['imagen','imagen_categoria']:
            assert not p[k] or (catroot/p[k]).is_file(), (p['codigo'],p[k])
    idx.write_text(updated)
    # Reuse the approved detail-page layout and existing category styles.
    template=(root/'scripts/catalog_product_template.tmpl').read_text()
    changed=0
    for p in products:
        prev=old.get(p['codigo'])
        page=catroot/'productos'/p['slug']/'index.html'
        if not page.is_file() or not prev or any(prev[k]!=p[k] for k in ('nombre','presentacion','precio','unitario','uxb','tipo','categoria')):
            c=categories[p['categoria']]
            page.parent.mkdir(parents=True,exist_ok=True)
            page.write_text(product_page(template,p,c,category_pages[c]))
            changed+=1
        body=page.read_text()
        assert f'<p class="price">{money(p["precio"])}</p>' in body,(p['codigo'],'ficha precio')
        assert f'<h1>{ESC(p["nombre"])}</h1>' in body,(p['codigo'],'ficha nombre')
        assert f'href="{BASE}productos/{p["slug"]}/"' in body
        assert (p['tipo']=='bulto')==('class="reference"' in body)
        assert p['tipo']!='bulto' or (f'Venta por bulto · {p["uxb"]} unidades' in body and f'Referencia: {money(p["unitario"])} por unidad' in body)
    for code in old.keys()-seen:
        (catroot/'productos'/old[code]['slug']/'index.html').unlink()
    for cat,c in categories.items():
        path=catroot/'categorias'/c/'index.html'
        txt=path.read_text()
        txt=re.sub(r'Explorá \d+ productos',f'Explorá {len(groups[cat])} productos',txt)
        txt=one(r'<strong>\d+ productos</strong>',f'<strong>{len(groups[cat])} productos</strong>',txt)
        listing='\n'.join(f'<li><a href="../../productos/{p["slug"]}/index.html">{ESC(p["nombre"])}</a> · {money(p["precio"], 0 if p["precio"].is_integer() else 2)} '+(f'por bulto x{p["uxb"]}' if p['tipo']=='bulto' else 'por unidad')+'</li>' for p in groups[cat])
        txt=one(r'<ul>.*?</ul>',f'<ul>{listing}</ul>',txt,re.S)
        path.write_text(txt)
        assert re.findall(r'../../productos/([^/]+)/index.html',txt)==[p['slug'] for p in groups[cat]]
    sitemap=root/'sitemap.xml'
    ns='http://www.sitemaps.org/schemas/sitemap/0.9'
    ET.register_namespace('',ns)
    tree=ET.parse(sitemap)
    tag=lambda t:f'{{{ns}}}{t}'
    sr=tree.getroot()
    for element in list(sr):
        loc=element.findtext(tag('loc'),'')
        if loc.startswith(BASE+'productos/'):sr.remove(element)
    for p in products:
        el=ET.SubElement(sr,tag('url'))
        ET.SubElement(el,tag('loc')).text=BASE+'productos/'+p['slug']+'/'
        ET.SubElement(el,tag('lastmod')).text=datetime.fromisoformat(meta['vigencia']).date().isoformat()
    tree.write(sitemap,encoding='utf-8',xml_declaration=True)
    listed=[el.findtext(tag('loc'),'') for el in ET.parse(sitemap).getroot()]
    assert len(listed)==len(set(listed)) and {x for x in listed if x.startswith(BASE+'productos/')}=={BASE+'productos/'+p['slug']+'/' for p in products}
    pdf=catroot/'catalogo-personas.pdf'
    create_pdf(pdf,products,date,catroot/'assets/logo_bon_vi_mercat.png')
    pages=verify_pdf(pdf,products,date)
    stats=dict(l7=meta['id'],vigencia=meta['vigencia'],publicables=len(products),altas=len(seen-old.keys()),bajas=len(old.keys()-seen),fichas_reescritas=changed,categorias=len(categories),modalidades=dict(Counter(p['tipo'] for p in products)),precios_pdf=len(products)*2,paginas_pdf=pages)
    (catroot/'version-l7.json').write_text(json.dumps({k:stats[k] for k in ('l7','vigencia','publicables')},ensure_ascii=False)+'\n')
    report.write_text(json.dumps(stats,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(stats,ensure_ascii=False))

if __name__=='__main__':
    cli=argparse.ArgumentParser()
    cli.add_argument('--root',type=Path,required=True)
    cli.add_argument('--snapshot',type=Path,required=True)
    cli.add_argument('--report',type=Path,required=True)
    args=cli.parse_args()
    run(args.root,json.loads(args.snapshot.read_text()),args.report)
