"""Catálogo SEO: índice navegable privado a partir de productos aprobados.
No conecta a BD ni publica datos. Reutiliza la plantilla HTML de vista previa.
"""
import html
import json
import re
from pathlib import Path
from catalogo_precios import public_offer
from catalogo_preview import slug, format_price, make_page

CATEGORIES = ["Vinos", "Champagnes", "Cervezas", "Jugos", "Whiskys",
              "Aperitivos", "Aceites y Acetos", "Otros"]
WHATSAPP = "https://wa.me/5492216816892"
INSTAGRAM = "https://www.instagram.com/bonvimercat/"

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
            "slug": slug(str(item["producto"])) + "-" + slug(str(item["codigo"]))}

def index_html(products, pdf_path=None):
    """Genera un HTML estático con búsqueda, filtros, redes y acceso a PDF.
    pdf_path debe ser un archivo público revisado y versionado; nunca un enlace ficticio.
    """
    data = json.dumps(products, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    if pdf_path:
        if not re.fullmatch(r"[a-zA-Z0-9_./-]+\\.pdf", pdf_path) or pdf_path.startswith("/") or ".." in pdf_path:
            raise ValueError("Ruta PDF no segura")
        pdf = '<a class="download" href="' + html.escape(pdf_path, quote=True) + '" download>Descargar catálogo PDF ↓</a>'
    else:
        pdf = '<p class="pending">La descarga del PDF completo se habilitará al validar la lista vigente.</p>'
    return """<!doctype html><html lang="es-AR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>Catálogo de bebidas | BON VI MERCAT La Plata</title>
<style>
:root{--green:#173d31;--ivory:#f5f0e6}*{box-sizing:border-box}
body{margin:0;background:var(--ivory);color:var(--green);font:16px system-ui}
header,footer{background:var(--green);color:white;padding:20px;display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap}
header a,footer a{color:white;text-decoration:none}.brand{font:700 22px Georgia,serif;letter-spacing:2px}
nav{display:flex;gap:16px}.wrap{max-width:1100px;margin:auto;padding:20px 16px 70px}
.hero{text-align:center;background:#fffaf3;border:1px solid #ddd5c7;border-radius:20px;padding:26px 15px}
h1{font:700 clamp(30px,6vw,45px) Georgia,serif;margin:8px}
.panel{background:#fffdf8;border:1px solid #ddd5c7;border-radius:17px;padding:19px;margin:16px 0}
.pdf{display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap}
.download{padding:13px 18px;border:1px solid var(--green);border-radius:25px;color:var(--green);text-decoration:none}
.pending{font-size:13px;color:#666}input,select{width:100%;border:1px solid #bac8bc;border-radius:10px;padding:13px;background:white;font-size:16px}
.filters{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}label{display:block;font-size:13px;font-weight:bold;margin-bottom:6px}
.categories{display:grid;grid-template-columns:repeat(4,1fr);gap:8px}
.categories button{border:1px solid #aab7a9;border-radius:30px;background:white;padding:13px 5px;color:var(--green);cursor:pointer}
.categories button[aria-pressed=true]{background:var(--green);color:white}
.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
.product{background:#fffdf8;border:1px solid #ddd5c7;border-radius:15px;padding:18px}
.product h2{font:700 21px Georgia,serif}.price{font:700 29px Georgia,serif;margin-top:12px}
.unit,.muted{font-size:12px;color:#637064}.product a{color:var(--green)}
.float{position:fixed;bottom:18px;right:14px;display:grid;gap:9px}.float a{width:50px;height:50px;border-radius:50%;display:grid;place-items:center;color:white;box-shadow:0 3px 12px #0003}
.wa{background:#218b5b}.ig{background:linear-gradient(135deg,#7844ba,#c83282,#e6a04e)}
.float svg,nav svg,footer svg{width:24px;height:24px}.empty{text-align:center;color:#657369;padding:25px}
@media(max-width:700px){.grid{grid-template-columns:1fr}.filters{grid-template-columns:1fr}.categories{grid-template-columns:repeat(2,1fr)}}
</style></head><body>
<header><a class="brand" href="/">BON VI MERCAT</a><nav><a aria-label="WhatsApp" href="https://wa.me/5492216816892">WhatsApp</a><a aria-label="Instagram" href="https://www.instagram.com/bonvimercat/">Instagram</a></nav></header>
<main class="wrap"><section class="hero"><div class="muted">BUENAS BEBIDAS · MEJORES ENCUENTROS</div><h1>CATÁLOGO ACTUALIZADO</h1></section>
<section class="panel pdf"><div><strong>¿Preferís la lista completa?</strong><div class="muted">Catálogo en PDF</div></div>""" + pdf + """</section>
<section class="panel"><h2>¿Qué estás buscando?</h2><p class="muted">Buscá por código, marca o producto.</p>
<input id="search" type="search" aria-label="Buscar" placeholder="Código, marca o producto"></section>
<div class="categories" id="categories"></div>
<section class="panel"><h2>Filtrar resultados</h2><div class="filters">
<div><label for="category">Categoría</label><select id="category"></select></div>
<div><label for="maxprice">Precio máximo</label><input id="maxprice" type="number" min="0" placeholder="Sin límite"></div>
<div><label for="pricetype">Filtrar por</label><select id="pricetype"><option value="unitario">Precio unitario</option><option value="precio">Precio de venta real</option></select></div>
<div><label for="brand">Marca / bodega</label><select id="brand"></select></div>
<div><label for="sort">Ordenar</label><select id="sort"><option value="default">Orden del catálogo</option><option value="asc">Menor precio</option><option value="desc">Mayor precio</option><option value="name">Nombre A–Z</option></select></div></div></section>
<p id="count" aria-live="polite">Buscá o seleccioná una categoría para comenzar.</p>
<section class="grid" id="results"></section><div class="empty" id="empty" hidden>No encontramos productos con esos filtros.</div>
</main><aside class="float"><a class="ig" aria-label="Seguir en Instagram" href="https://www.instagram.com/bonvimercat/"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.6" cy="6.5" r=".8" fill="currentColor" stroke="none"/></svg></a><a class="wa" aria-label="Consultar por WhatsApp" href="https://wa.me/5492216816892"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20.5 11.7a8.5 8.5 0 0 1-12.4 7.5L3 20.5l1.4-5A8.5 8.5 0 1 1 20.5 11.7Z"/><path d="M8.6 8.1c-.5.2-1.1 1.1-.8 2.1.5 1.9 2.8 4.3 4.8 5.1 1.3.5 2.2-.1 2.6-.9l-2-1-1 .9c-1.3-.6-2.3-1.6-2.9-2.9l.9-.9-1-2.1Z"/></svg></a></aside>
<footer><span>BON VI MERCAT · La Plata</span><span><a href="https://wa.me/5492216816892">WhatsApp</a> · <a href="https://www.instagram.com/bonvimercat/">Instagram</a></span></footer>
<script>
const products=__PRODUCTS__;
const cats=["Vinos","Champagnes","Cervezas","Jugos","Whiskys","Aperitivos","Aceites y Acetos","Otros"];
const $=id=>document.getElementById(id);
const norm=s=>String(s||"").normalize("NFD").replace(/[\\u0300-\\u036f]/g,"").toLowerCase();
const money=n=>"$ "+Math.round(n).toLocaleString("es-AR");
const esc=s=>String(s||"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
$("category").innerHTML='<option value="">Todas</option>'+cats.map(x=>'<option>'+esc(x)+'</option>').join("");
$("brand").innerHTML='<option value="">Todas</option>'+[...new Set(products.map(p=>p.marca).filter(Boolean))].sort().map(x=>'<option>'+esc(x)+'</option>').join("");
$("categories").innerHTML=cats.map(c=>'<button type="button" data-cat="'+esc(c)+'" aria-pressed="false">'+esc(c)+'</button>').join("");
const render=()=>{
 const q=norm($("search").value),cat=$("category").value,brand=$("brand").value,max=Number($("maxprice").value)||Infinity,key=$("pricetype").value,sort=$("sort").value;
 const started=!!(q||cat||brand||$("maxprice").value||sort!=="default");
 let rows=started?products.filter(p=>(!q||norm(p.nombre+" "+p.codigo+" "+p.marca).includes(q))&&(!cat||p.categoria===cat)&&(!brand||p.marca===brand)&&p[key]<=max):[];
 if(sort==="asc")rows.sort((a,b)=>a[key]-b[key]);if(sort==="desc")rows.sort((a,b)=>b[key]-a[key]);if(sort==="name")rows.sort((a,b)=>a.nombre.localeCompare(b.nombre));
 const visible=rows.slice(0,60);
 $("results").innerHTML=visible.map(p=>'<article class="product"><div class="muted">'+esc(p.categoria)+' · Cód. '+esc(p.codigo)+'</div><h2><a href="productos/'+encodeURIComponent(p.slug)+'/">'+esc(p.nombre)+'</a></h2><div class="muted">'+(p.tipo==="bulto"?'Venta por bulto · '+p.uxb+' unidades':'Venta por unidad')+'</div><div class="price">'+money(p.precio)+'</div>'+(p.tipo==="bulto"?'<div class="unit">Referencia: '+money(p.unitario)+' por unidad</div>':'')+'</article>').join("");
 $("count").textContent=started?rows.length+" productos encontrados"+(rows.length>60?" · Mostrando los primeros 60":""):"Buscá o seleccioná una categoría para comenzar.";
 $("empty").hidden=!started||rows.length>0;
 document.querySelectorAll("[data-cat]").forEach(b=>b.setAttribute("aria-pressed",String(b.dataset.cat===cat)));
};
document.querySelectorAll("[data-cat]").forEach(b=>b.addEventListener("click",()=>{$("category").value=$("category").value===b.dataset.cat?"":b.dataset.cat;render()}));
["search","category","brand","maxprice","pricetype","sort"].forEach(id=>$(id).addEventListener("input",render));render();
</script></body></html>""".replace("__PRODUCTS__", data)

def write_preview(rows, destination, pdf_path=None):
    """Crea índice y fichas. Destino privado, nunca carpeta pública."""
    out = Path(destination).resolve()
    if out.exists() and any(out.iterdir()):
        raise ValueError("El directorio de salida debe estar vacío")
    products = [public_product(row) for row in rows]
    if len({p["slug"] for p in products}) != len(products):
        raise ValueError("Códigos duplicados; no generar páginas")
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(index_html(products, pdf_path), encoding="utf-8")
    for row, p in zip(rows, products):
        folder = out / "productos" / p["slug"]
        folder.mkdir(parents=True, exist_ok=True)
        item = dict(row, slug=p["slug"])
        (folder / "index.html").write_text(make_page(item), encoding="utf-8")
    return len(products)
