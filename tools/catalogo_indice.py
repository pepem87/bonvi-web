"""Catálogo SEO: índice navegable privado a partir de productos aprobados.
No conecta a BD ni publica datos. Reutiliza la plantilla HTML de vista previa.
"""
import html
from datetime import datetime
import json
import re
from urllib.parse import urlsplit
from pathlib import Path
from catalogo_precios import public_offer
from catalogo_preview import slug, format_price, make_page

CATEGORIES = ["VINOS", "CHAMPAGNES", "CERVEZAS", "JUGOS Y POLVOS", "WHISKYS",
              "APERITIVOS", "ACEITES", "OTROS"]
WHATSAPP = "https://wa.me/5492216816892"
INSTAGRAM = "https://www.instagram.com/bonvimercat/"

def verified_image(item):
    """Solo imagen explícitamente verificada para este SKU; nunca inferir por nombre."""
    image = item.get("imagen_verificada") or ""
    if not image:
        return ""
    parsed = urlsplit(str(image))
    if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
        raise ValueError("La imagen verificada debe ser HTTPS")
    return str(image)

def category_image(item):
    """Ruta relativa a una ilustración aprobada, nunca una URL de producto inferida."""
    name = str(item.get("imagen_categoria") or "")
    if name and not re.fullmatch(r"assets/(?:category_placeholders|categories)/[a-z0-9_-]+\.(?:webp|png)", name):
        raise ValueError("Ruta de ilustración de categoría inválida")
    return name


def public_product(item):
    """Sólo campos comerciales permitidos, sin costos ni márgenes."""
    offer = public_offer(item["modalidad"], item["uxb"], item["precio_persona_unit"])
    return {"codigo": str(item["codigo"]), "nombre": str(item["producto"]),
            "familia": str(item.get("familia") or ""), "categoria": str(item.get("categoria") or "Otros"),
            "presentacion": str(item.get("presentacion") or ""),
            "marca": str(item.get("marca") or ""),
            "tipo": offer["tipo"], "uxb": offer["cantidad"],
            "precio": float(offer["precio_total"]),
            "unitario": float(offer["precio_unitario_referencia"]),
            "imagen": verified_image(item),
            "imagen_categoria": category_image(item),
            "icono_categoria": str(item.get("icono_categoria") or "🍾"),
            "slug": slug(str(item["producto"])) + "-" + slug(str(item["codigo"]))}

def index_html(products, pdf_path=None, search_aliases=None, category_icons=None,
               vigencia_marker=None, logo_path=None, background_path=None):
    """Genera un HTML estático con búsqueda, filtros, redes y acceso a PDF.
    pdf_path debe ser un archivo público revisado y versionado; nunca un enlace ficticio.
    """
    data = json.dumps(products, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    aliases = json.dumps(search_aliases or {}, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    chips = json.dumps(category_icons or {}, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    date = str(vigencia_marker or "").strip().split("T", 1)[0][:10]
    try:
        date = datetime.strptime(date, "%Y-%m-%d").strftime("%d/%m/%Y") if date else ""
    except ValueError:
        pass
    hero_meta = (f"<strong>Vigente hasta {html.escape(date)}</strong> · " if date else "") + f"{len(products)} productos"
    for name in (logo_path, background_path):
        if name and not re.fullmatch(r"assets/[a-z0-9_-]+\.png", name):
            raise ValueError("Ruta de recurso gráfico inválida")
    logo = ('<img class="hero-logo" alt="BON VI MERCAT" src="' + html.escape(logo_path, quote=True) + '">' if logo_path else "")
    background = ('linear-gradient(rgba(244,240,232,.86),rgba(244,240,232,.93)),url("'+background_path+'")' if background_path else "linear-gradient(180deg,#F4F0E8,#EAE4D8)")
    if pdf_path:
        if not re.fullmatch(r"[a-zA-Z0-9_./-]+\.pdf", pdf_path) or pdf_path.startswith("/") or ".." in pdf_path:
            raise ValueError("Ruta PDF no segura")
        pdf = '<a class="download" href="' + html.escape(pdf_path, quote=True) + '" download>Descargar catálogo PDF ↓</a>'
    else:
        pdf = '<p class="pending">La descarga del PDF completo se habilitará al validar la lista vigente.</p>'
    return """<!doctype html><html lang="es-AR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>Catálogo BON VI MERCAT | Bebidas, aceites y acetos en La Plata</title>
<style>
:root{--green:#173d31;--ivory:#f5f0e6}*{box-sizing:border-box}
body{margin:0;background:var(--ivory);background-image:__BACKGROUND__;background-position:center top;background-size:cover;background-attachment:fixed;color:var(--green);font:16px system-ui}
header,footer{background:var(--green);color:white;padding:20px;display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap}
header a,footer a{color:white;text-decoration:none}.brand{font:700 22px Georgia,serif;letter-spacing:2px}
nav{display:flex;gap:16px}.wrap{max-width:840px;margin:auto;padding:20px 16px 70px}
.hero{text-align:center;background:rgba(255,253,248,.96);border:1px solid rgba(41,74,60,.18);border-radius:24px;padding:20px 22px 18px;box-shadow:0 12px 34px rgba(41,74,60,.12)}
.hero-logo{width:120px;max-width:34vw;height:auto;margin:0 auto 6px;display:block}
h1{font:700 clamp(30px,6vw,45px) Georgia,serif;margin:8px}
.hero-meta{font-size:14px;color:#536158}.hero-meta strong{color:#294a3c}
.panel{background:#fffdf8;border:1px solid #ddd5c7;border-radius:17px;padding:19px;margin:16px 0}
.pdf{display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap}
.download{padding:13px 18px;border:1px solid var(--green);border-radius:25px;color:var(--green);text-decoration:none}
.pending{font-size:13px;color:#666}input,select{width:100%;border:1px solid #bac8bc;border-radius:10px;padding:13px;background:white;font-size:16px}
.filters{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}label{display:block;font-size:13px;font-weight:bold;margin-bottom:6px}
.clear{padding:12px 20px;border:1px solid #294a3c;border-radius:999px;background:#fffdf8;color:#294a3c;font-weight:800;cursor:pointer}
.searchrow{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:10px;align-items:center}
.tip,.selection{font-size:13px;color:#405e50;margin:10px 0}
.pager{display:flex;align-items:center;justify-content:space-between;gap:12px;margin:12px 0}
.pager button{padding:10px 16px;border:1px solid #294a3c;border-radius:999px;background:#fffdf8;color:#294a3c;font-weight:800;cursor:pointer}
.pager button:disabled{opacity:.45;cursor:default}
.pager span{font-size:13px;color:#405e50;font-weight:800}
.categories{display:grid;grid-template-columns:repeat(4,1fr);gap:8px}
.categories button{border:1px solid #aab7a9;border-radius:30px;background:white;padding:8px 5px;color:var(--green);cursor:pointer;display:flex;align-items:center;justify-content:center;gap:9px;min-height:52px;font-weight:800}
.categories button img{display:block;width:38px;height:38px;object-fit:contain;border-radius:7px}
.categories button[aria-pressed=true]{background:var(--green);color:white}
.categories button:hover{border-color:#294a3c}
.categories button:focus-visible,.pager button:focus-visible,.clear:focus-visible{outline:3px solid #b58b49;outline-offset:2px}
.grid{display:grid;grid-template-columns:1fr;gap:9px}
.product{background:#fffdf8;border:1px solid rgba(41,74,60,.14);border-radius:19px;padding:12px;display:grid;grid-template-columns:78px minmax(0,1fr);gap:13px;align-items:center;min-width:0;box-shadow:0 7px 22px rgba(41,74,60,.08)}.product-body{min-width:0;flex:1}.product-photo{width:78px;min-height:112px;border-radius:15px;background:linear-gradient(180deg,#f8f3e9,#e9e2d5);display:grid;place-items:center;overflow:hidden}.product-photo img{width:100%;height:112px;object-fit:cover}.product-photo .fallback{font:34px Georgia,serif;text-align:center;color:#71816f;padding:5px}.product h2{margin:4px 0;line-height:1.15;overflow-wrap:anywhere}
.product h2{font:700 17px Georgia,serif}.price{font:800 23px Georgia,serif;color:#174432;margin-top:3px}
.catname{font-size:11px;font-weight:900;letter-spacing:.08em;color:#8a6c3f;text-transform:uppercase}
.product-code{font-size:12px;font-weight:800;color:#405e50}.sale-row{display:flex;flex-wrap:wrap;justify-content:space-between;align-items:flex-end;gap:8px;margin-top:6px}
.sale-badge{display:inline-block;font-size:11px;font-weight:900;padding:6px 9px;border-radius:999px;background:#dde4cc;color:#294a3c}.sale-badge.bulk{background:#eadbb8;color:#5d4827}
.price-wrap{text-align:right;margin-left:auto}.price-label{font-size:11px;color:#727b75}
.unit,.muted{font-size:12px;color:#637064}.product a{color:var(--green)}
.float{position:fixed;bottom:18px;right:14px;display:grid;gap:9px}.float a{width:50px;height:50px;border-radius:50%;display:grid;place-items:center;color:white;box-shadow:0 3px 12px #0003}
.wa{background:#218b5b}.ig{background:linear-gradient(135deg,#7844ba,#c83282,#e6a04e)}
.float svg,nav svg,footer svg{width:24px;height:24px}.empty{text-align:center;color:#657369;padding:25px}
@media(max-width:700px){.product-photo{width:66px;min-height:104px}.product-photo img{height:104px}.product{padding:10px;grid-template-columns:66px minmax(0,1fr);gap:10px}.filters{grid-template-columns:1fr}.categories{grid-template-columns:repeat(2,1fr)}.searchrow{grid-template-columns:1fr}.sale-row{display:block}.price-wrap{text-align:left;margin:9px 0 0}.pager{flex-wrap:wrap}.pager span{order:-1;width:100%;text-align:center}}
</style></head><body>
<header><a class="brand" href="/">BON VI MERCAT</a><nav><a aria-label="WhatsApp" href="https://wa.me/5492216816892">WhatsApp</a><a aria-label="Instagram" href="https://www.instagram.com/bonvimercat/">Instagram</a></nav></header>
<main class="wrap"><section class="hero">__LOGO__<div class="muted">BUENAS BEBIDAS · MEJORES ENCUENTROS</div><h1>CATÁLOGO ACTUALIZADO</h1><div class="hero-meta">__HERO_META__</div></section>
<section class="panel pdf"><div><strong>¿Preferís la lista completa?</strong><div class="muted">Catálogo en PDF</div></div>""" + pdf + """</section>
<section class="panel"><h2>¿Qué estás buscando?</h2><p class="muted">Buscá por código, marca o producto.</p>
<div class="searchrow"><input id="search" type="search" aria-label="Buscar" placeholder="🔎 Código, Chandon, jugo, Fernet..."><button type="button" id="clear" class="clear">✕ Limpiar</button></div></section>
<div class="categories" id="categories"></div>
<section class="panel"><h2>Filtrar resultados</h2><div class="filters">
<div><label for="category">Categoría</label><select id="category"></select></div>
<div><label for="range">Rango de precio</label><select id="range"><option>TODOS</option><option>HASTA $10.000</option><option>$10.001 A $15.000</option><option>$15.001 A $20.000</option><option>$20.001 A $30.000</option><option>MÁS DE $30.000</option></select></div>
<div><label for="pricetype">Filtrar precio por</label><select id="pricetype"><option value="unitario">PRECIO UNITARIO</option><option value="precio">PRECIO DE VENTA</option></select></div>
<div><label for="brand">Marca / bodega</label><select id="brand"></select></div>
<div><label for="sort">Ordenar por</label><select id="sort"><option value="default">ORDEN DEL CATÁLOGO</option><option value="asc">MENOR PRECIO</option><option value="desc">MAYOR PRECIO</option><option value="name">NOMBRE A–Z</option></select></div></div><p class="tip">💡 Podés buscar por precio unitario o por el precio de venta real del bulto o unidad.</p><p class="selection" id="selection"></p></section>
<p id="count" aria-live="polite">Buscá o seleccioná una categoría para comenzar.</p>
<nav class="pager" id="topPager" aria-label="Paginación superior"></nav><section class="grid" id="results"></section><div class="empty" id="empty" hidden>No encontramos productos con esos filtros.</div><nav class="pager" id="bottomPager" aria-label="Paginación inferior"></nav><section class="panel pdf"><strong>También podés llevarte la lista completa o consultar por WhatsApp</strong><div id="bottomPDF"></div><a class="download" href="https://wa.me/5492216816892">Consultar por WhatsApp</a></section>
</main><aside class="float"><a class="ig" aria-label="Seguir en Instagram" href="https://www.instagram.com/bonvimercat/"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.6" cy="6.5" r=".8" fill="currentColor" stroke="none"/></svg></a><a class="wa" aria-label="Consultar por WhatsApp" href="https://wa.me/5492216816892"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20.5 11.7a8.5 8.5 0 0 1-12.4 7.5L3 20.5l1.4-5A8.5 8.5 0 1 1 20.5 11.7Z"/><path d="M8.6 8.1c-.5.2-1.1 1.1-.8 2.1.5 1.9 2.8 4.3 4.8 5.1 1.3.5 2.2-.1 2.6-.9l-2-1-1 .9c-1.3-.6-2.3-1.6-2.9-2.9l.9-.9-1-2.1Z"/></svg></a></aside>
<footer><span>BON VI MERCAT · La Plata</span><span><a href="https://wa.me/5492216816892">WhatsApp</a> · <a href="https://www.instagram.com/bonvimercat/">Instagram</a></span></footer>
<script>
const products=__PRODUCTS__;
const aliases=__ALIASES__;
const chipIcons=__CHIPS__;
const cats=["VINOS","CHAMPAGNES","CERVEZAS","JUGOS Y POLVOS","WHISKYS","APERITIVOS","ACEITES","OTROS"];
const $=id=>document.getElementById(id);
const norm=s=>String(s||"").normalize("NFD").split("").filter(c=>{const n=c.charCodeAt(0);return n<768||n>879}).join("").toLowerCase();
const money=n=>"$ "+Math.round(n).toLocaleString("es-AR");
const esc=s=>String(s||"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const catName=c=>c==="ACEITES"?"ACEITES Y ACETOS":c==="JUGOS Y POLVOS"?"JUGOS":c;
const matchCat=(actual,chosen)=>!chosen||(chosen==="APERITIVOS"?["APERITIVOS","GIN"].includes(actual):chosen==="OTROS"?["CUIDADO PERSONAL Y HOGAR","VARIADOS"].includes(actual):actual===chosen);
const inRange=(n,r)=>r==="TODOS"||(r==="HASTA $10.000"?n<=10000:r==="$10.001 A $15.000"?n>10000&&n<=15000:r==="$15.001 A $20.000"?n>15000&&n<=20000:r==="$20.001 A $30.000"?n>20000&&n<=30000:n>30000);
const price=p=>Number(p[$("pricetype").value]);
const perPage=80;
let page=1, filtered=[],signature="";
$("category").innerHTML='<option value="">TODAS LAS CATEGORÍAS</option>'+[...new Set(products.map(p=>p.categoria).filter(c=>c&&c!=="OTROS"))].sort().map(c=>'<option value="'+esc(c)+'">'+esc(catName(c))+'</option>').join("")+'<option value="OTROS">OTROS</option>';
$("brand").innerHTML='<option value="">TODAS LAS MARCAS</option>'+[...new Set(products.map(p=>p.marca).filter(Boolean))].sort().map(b=>'<option value="'+esc(b)+'">'+esc(b)+'</option>').join("");
$("categories").innerHTML=cats.map(c=>'<button type="button" data-cat="'+esc(c)+'" aria-pressed="false">'+(chipIcons[c]?'<img loading="lazy" alt="" src="'+esc(chipIcons[c])+'">':"")+esc(catName(c))+'</button>').join("");
$("bottomPDF").innerHTML=document.querySelector(".pdf .download")?document.querySelector(".pdf .download").outerHTML:"";
const pager=(place,pages)=>{const target=$(place);if(pages<=1){target.innerHTML="";return}target.innerHTML='<button type="button" data-move="-1" '+(page===1?"disabled":"")+'>← ANTERIOR</button><span>Página '+page+' de '+pages+'</span><button type="button" data-move="1" '+(page===pages?"disabled":"")+'>SIGUIENTE →</button>';target.querySelectorAll("[data-move]").forEach(b=>b.addEventListener("click",()=>{page+=Number(b.dataset.move);paint();$("count").scrollIntoView({block:"center",behavior:"smooth"})}))};
function paint(){
 const pages=Math.max(1,Math.ceil(filtered.length/perPage));
 page=Math.min(Math.max(1,page),pages);
 const start=(page-1)*perPage,visible=filtered.slice(start,start+perPage);
 $("results").innerHTML=visible.map(p=>{
 const bulk=p.tipo==="bulto"&&Number(p.uxb)>1;
 const badge=bulk?"📦 VENTA POR BULTO · x"+p.uxb:"🍾 VENTA POR UNIDAD";
 const fallback='<span class="fallback">'+esc(p.icono_categoria||"🍾")+'</span>';
 const photo=p.imagen?'<img loading="lazy" alt="'+esc(p.nombre)+'" src="'+esc(p.imagen)+'">':p.imagen_categoria?'<img loading="lazy" alt="Ilustración de categoría '+esc(p.categoria)+'" src="'+esc(p.imagen_categoria)+'">':fallback;
 const reference=bulk?'<div class="unit">Referencia por unidad: '+money(p.unitario)+'</div>':"";
 return '<article class="product"><div class="product-photo">'+photo+'</div><div class="product-body"><div class="catname">'+esc(p.categoria)+'</div><h2><a href="productos/'+encodeURIComponent(p.slug)+'/">'+esc(p.nombre)+'</a></h2><div class="product-code">CÓDIGO '+esc(p.codigo)+'</div><div class="muted">'+(p.presentacion?'Presentación: '+esc(p.presentacion):"")+'</div><div class="sale-row"><span class="sale-badge'+(bulk?' bulk':'')+'">'+badge+'</span><div class="price-wrap"><div class="price-label">Precio '+(bulk?"bulto":"unidad")+'</div><div class="price">'+money(p.precio)+'</div>'+reference+'</div></div></div></article>';
 }).join("");
 const started=Boolean($("search").value.trim()||$("category").value||$("brand").value||$("range").value!=="TODOS"||$("pricetype").value!=="unitario");
 $("count").textContent=started?filtered.length+" producto(s) encontrado(s)"+(filtered.length?" · Mostrando "+(start+1)+"–"+(start+visible.length):""):"Buscá o seleccioná una categoría para comenzar.";
 $("empty").hidden=filtered.length!==0;
 $("empty").textContent=started?"No encontramos productos con esos filtros. Probá ampliar el rango de precio, cambiar la marca o limpiar los filtros.":"🔎 Escribí algo, tocá una categoría o usá los filtros de precio y marca para empezar.";
 pager("topPager",pages);pager("bottomPager",pages);
 document.querySelectorAll("[data-cat]").forEach(b=>b.setAttribute("aria-pressed",String(b.dataset.cat===$("category").value)));
}
function render(){
 const q=norm($("search").value.trim()),cat=$("category").value,brand=$("brand").value,range=$("range").value,basis=$("pricetype").value,sort=$("sort").value;
 const sig=[q,cat,brand,range,basis,sort].join("|");
 if(sig!==signature){page=1;signature=sig}
 const started=Boolean(q||cat||brand||range!=="TODOS"||basis!=="unitario");
 const alias=aliases[q]||"";
 filtered=started?products.filter(p=>{
 const haystack=norm([p.codigo,p.nombre,p.familia,p.presentacion,p.categoria,p.marca].join(" "));
 const textMatch=!q||haystack.includes(q)||(alias&&p.categoria===alias);
 return textMatch&&matchCat(p.categoria,cat)&&(!brand||p.marca===brand)&&inRange(price(p),range);
 }):[];
 if(sort==="asc")filtered.sort((a,b)=>price(a)-price(b)||a.nombre.localeCompare(b.nombre));
 else if(sort==="desc")filtered.sort((a,b)=>price(b)-price(a)||a.nombre.localeCompare(b.nombre));
 else if(sort==="name")filtered.sort((a,b)=>norm(a.nombre).localeCompare(norm(b.nombre)));
 $("selection").textContent="Selección actual: "+(cat||"Todas las categorías")+" · "+range+" · "+(basis==="unitario"?"por unidad":"por presentación de venta")+" · "+(brand||"Todas las marcas")+" · "+$("sort").selectedOptions[0].text;
 paint();
}
document.querySelectorAll("[data-cat]").forEach(b=>b.addEventListener("click",()=>{$("category").value=$("category").value===b.dataset.cat?"":b.dataset.cat;render()}));
["search","category","brand","range","pricetype","sort"].forEach(id=>$(id).addEventListener("input",render));
$("clear").addEventListener("click",()=>{$("search").value="";$("category").value="";$("brand").value="";$("range").value="TODOS";$("pricetype").value="unitario";$("sort").value="default";render()});
render();
</script></body></html>""".replace("__PRODUCTS__", data).replace("__ALIASES__", aliases).replace("__CHIPS__", chips).replace("__HERO_META__", hero_meta).replace("__LOGO__", logo).replace("__BACKGROUND__", background)

def write_preview(rows, destination, pdf_path=None, search_aliases=None, category_icons=None,
                  vigencia_marker=None, logo_path=None, background_path=None):
    """Crea índice y fichas. Destino privado, nunca carpeta pública."""
    out = Path(destination).resolve()
    if out.exists() and any(out.iterdir()):
        raise ValueError("El directorio de salida debe estar vacío")
    products = [public_product(row) for row in rows]
    if len({p["slug"] for p in products}) != len(products):
        raise ValueError("Códigos duplicados; no generar páginas")
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(index_html(products, pdf_path, search_aliases, category_icons,
                                               vigencia_marker, logo_path, background_path), encoding="utf-8")
    for row, p in zip(rows, products):
        folder = out / "productos" / p["slug"]
        folder.mkdir(parents=True, exist_ok=True)
        item = dict(row, slug=p["slug"])
        (folder / "index.html").write_text(make_page(item), encoding="utf-8")
    return len(products)
