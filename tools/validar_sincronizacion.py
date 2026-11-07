#!/usr/bin/env python3
"""Compara dos catálogos HTML privados; nunca autoriza ni realiza publicación."""
import argparse
import hashlib
import json
import math
import re
from pathlib import Path

PATTERN = re.compile(r'const products=(\[.*?\]);\s*const aliases=', re.DOTALL)
PUBLIC_FIELDS = {'codigo','nombre','familia','categoria','presentacion','marca','tipo','uxb','precio','unitario','imagen','imagen_categoria','icono_categoria','slug'}

def load(path):
    body = Path(path).read_text(encoding='utf-8')
    found = PATTERN.search(body)
    if not found or 'noindex,nofollow' not in body:
        raise ValueError('Archivo sin datos de productos o sin noindex')
    records = json.loads(found.group(1))
    if not isinstance(records, list) or not records:
        raise ValueError('Catálogo inválido o vacío')
    catalog = {}
    for item in records:
        if not isinstance(item, dict) or set(item) - PUBLIC_FIELDS:
            raise ValueError('Campos no autorizados en ficha')
        code = str(item.get('codigo','')).strip()
        if not code or code in catalog:
            raise ValueError('Código vacío o repetido')
        a,b,c = (item.get(k) for k in ('precio','unitario','uxb'))
        if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or v<=0 for v in (a,b,c)):
            raise ValueError('Precio/UXB inválido')
        if int(c)!=c or item.get('tipo') not in ('bulto','unidad'):
            raise ValueError('Cantidad o modalidad inválida')
        if item['tipo']=='bulto' and c<=1:
            raise ValueError('Bulto con UxB inválido')
        if abs(a-b*(c if item['tipo']=='bulto' else 1))>0.011:
            raise ValueError('Precio de venta inconsistente')
        catalog[code]=item
    return catalog

# Huella fijada de la copia local que el usuario probó y aprobó el 07/11/2026.
# Incluye todas las fichas y los campos públicos, no solo el número de productos.
APPROVED_PUBLIC_SHA256 = "905fd6580af7d4b1e56ef5a163c74a7afdf1a2aa94d794efe38bcb7d66669d6c"

def approved_fingerprint(path):
    products = load(path)
    canonical = json.dumps(
        [products[key] for key in sorted(products)],
        ensure_ascii=False, sort_keys=True, separators=(',', ':')
    )
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()

def compare(old,new):
    common=set(old)&set(new)
    new_codes=set(new)-set(old)
    gone=set(old)-set(new)
    price_changes=mode_changes=category_changes=modified=0
    for code in common:
        a,b=old[code],new[code]
        modified+=int(a!=b)
        price_changes+=int(abs(b['precio']/a['precio']-1)>0.30)
        mode_changes+=int((a['tipo'],a['uxb'])!=(b['tipo'],b['uxb']))
        category_changes+=int((a['nombre'],a['familia'],a['categoria'])!=(b['nombre'],b['familia'],b['categoria']))
    alerts=[]
    if new_codes or gone: alerts.append('Altas o bajas requieren revisión')
    if price_changes: alerts.append('Variaciones de precio >30%')
    if mode_changes: alerts.append('Cambio modalidad/UxB')
    if category_changes: alerts.append('Cambio nombre/familia/categoría')
    if abs(len(new)-len(old))/len(old)>0.05: alerts.append('Variación total de SKU >5%')
    return dict(estado='REVISAR' if alerts else 'SIN_ALERTAS_AUTOMATICAS',
                publicacion_autorizada=False,total_anterior=len(old),total_nuevo=len(new),
                altas=len(new_codes),bajas=len(gone),modificados=modified,
                cambios_precio_mayores_limite=price_changes,cambios_modalidad=mode_changes,
                cambios_clasificacion=category_changes,alertas=alerts)

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--aprobado',type=Path,required=True)
    p.add_argument('--nuevo',type=Path,required=True)
    p.add_argument('--reporte',type=Path,required=True)
    a=p.parse_args()
    if a.reporte.exists() or a.reporte.resolve() in (a.aprobado.resolve(),a.nuevo.resolve()):
        p.error('Ruta de reporte existente o no válida')
    try:
        result=compare(load(a.aprobado),load(a.nuevo))
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as err:
        result={'estado':'ERROR','publicacion_autorizada':False,'alertas':[str(err)]}
    a.reporte.parent.mkdir(parents=True,exist_ok=True)
    a.reporte.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))
    raise SystemExit(0 if result['estado']=='SIN_ALERTAS_AUTOMATICAS' else 2)

if __name__=='__main__': main()
