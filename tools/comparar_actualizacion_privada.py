#!/usr/bin/env python3
"""Compara dos exportaciones de catálogo SIN consultar la base ni publicar.

La referencia de Fase 1 son los 16 fragmentos JSON ya aprobados. El archivo
nuevo debe contener exclusivamente las columnas públicas usadas por el
generador; nunca costos, márgenes ni información de clientes.

Ejemplo (desde la raíz del repositorio web):
 python tools/comparar_actualizacion_privada.py \
   --base preview/datos \
   --nuevo /ruta/privada/productos-vigentes.json \
   --reporte /ruta/privada/comparacion.json

El reporte es un CONTROL, no una autorización de despliegue.
"""
import argparse
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path

PUBLIC_COLUMNS = {
    "codigo", "producto", "familia", "presentacion", "uxb",
    "modalidad", "precio_persona_unit", "orden_l7", "activo", "rol",
}
COMPARE_COLUMNS = (
    "producto", "familia", "presentacion", "uxb", "modalidad",
    "precio_persona_unit", "orden_l7",
)


def archived_rows(directory):
    files = sorted(Path(directory).glob("catalogo-??.json"))
    if len(files) != 16:
        raise ValueError("La referencia aprobada necesita exactamente 16 fragmentos")
    rows = []
    for path in files:
        part = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(part, list):
            raise ValueError("Fragmento inválido: " + path.name)
        rows.extend(part)
    if len(rows) != 1541:
        raise ValueError("La referencia aprobada debe contener 1541 productos")
    return rows


def incoming_rows(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = data.get("catalogo")
    if not isinstance(data, list):
        raise ValueError("Se espera un arreglo de productos o un objeto con catalogo")
    return data


def _number(value, field, code):
    if value is None or isinstance(value, bool):
        raise ValueError(f"Campo {field} inválido en {code}")
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as error:
        raise ValueError(f"Campo {field} inválido en {code}") from error
    if not number.is_finite():
        raise ValueError(f"Campo {field} no finito en {code}")
    return number


def normalize(rows):
    """Valida antes de comparar; no permite campos contables internos."""
    result = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Cada producto debe ser un objeto")
        forbidden = set(row) - PUBLIC_COLUMNS
        if forbidden:
            raise ValueError("Campos no publicables presentes: " + ", ".join(sorted(forbidden)))
        code = str(row.get("codigo") or "").strip()
        if not code or code in result:
            raise ValueError("Código vacío o repetido: " + code)
        if not row.get("producto") or not row.get("familia"):
            raise ValueError("Nombre o familia vacíos: " + code)

        # Una exportación SQL amplia puede incluir bloqueados/inactivos:
        # se descartan para coincidir con las reglas del catálogo público.
        if "activo" in row and str(row["activo"]).lower() not in ("1", "true"):
            continue
        if "BLOQUEADO" in str(row.get("rol") or "").upper():
            continue
        unit_price = _number(row.get("precio_persona_unit"), "precio_persona_unit", code)
        if unit_price <= 0:
            # La consulta original excluye artículos con precio no positivo.
            continue
        uxb = _number(row.get("uxb"), "uxb", code)
        if uxb <= 0 or uxb != uxb.to_integral_value():
            raise ValueError("UxB inválido: " + code)
        modalidad = str(row.get("modalidad") or "").upper().strip()
        if modalidad not in ("BULTO", "UNIDAD"):
            raise ValueError("Modalidad inválida: " + code)
        family = str(row["familia"])
        if "PEDI" in family.upper() and "UNID" in family.upper():
            modalidad = "UNIDAD"
        tipo = "bulto" if modalidad == "BULTO" and uxb > 1 else "unidad"
        order = row.get("orden_l7")
        if order is not None:
            order = _number(order, "orden_l7", code)
        result[code] = {
            "producto": str(row["producto"]).strip(),
            "familia": family.strip(),
            "presentacion": str(row.get("presentacion") or "").strip(),
            "uxb": int(uxb),
            "modalidad": tipo,
            "precio_persona_unit": unit_price,
            "orden_l7": order,
            "precio_venta": unit_price * (uxb if tipo == "bulto" else 1),
        }
    if not result:
        raise ValueError("La exportación no contiene productos publicables")
    return result


def compare(previous, current):
    before = normalize(previous)
    after = normalize(current)
    old_codes, new_codes = set(before), set(after)
    added = sorted(new_codes - old_codes)
    removed = sorted(old_codes - new_codes)
    changed = []
    price_count = mode_count = identity_count = order_count = 0
    for code in sorted(old_codes & new_codes):
        old, new = before[code], after[code]
        fields = [name for name in (*COMPARE_COLUMNS, "precio_venta")
                  if old[name] != new[name]]
        if not fields:
            continue
        price_count += int("precio_persona_unit" in fields or "precio_venta" in fields)
        mode_count += int("modalidad" in fields or "uxb" in fields)
        identity_count += int(any(x in fields for x in ("producto", "familia", "presentacion")))
        order_count += int("orden_l7" in fields)
        if len(changed) < 25:
            changed.append({"codigo": code, "campos": fields})
    difference_count = len(added) + len(removed) + price_count + mode_count + identity_count + order_count
    return {
        "estado": "IGUAL_A_REFERENCIA" if not difference_count else "CAMBIOS_PARA_REVISAR",
        "publicacion_autorizada": False,
        "total_base": len(before), "total_nuevo": len(after),
        "altas": len(added), "bajas": len(removed),
        "productos_precio_modificado": price_count,
        "productos_modalidad_uxb_modificados": mode_count,
        "productos_descripcion_familia_modificados": identity_count,
        "productos_orden_modificado": order_count,
        "ejemplos_altas": added[:25],
        "ejemplos_bajas": removed[:25],
        "ejemplos_cambios": changed,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True, type=Path, help="Carpeta de los 16 fragmentos aprobados")
    parser.add_argument("--nuevo", required=True, type=Path, help="Exportación privada nueva JSON")
    parser.add_argument("--reporte", required=True, type=Path, help="JSON de resultado fuera del repositorio")
    args = parser.parse_args()
    target = args.reporte.resolve()
    repository = Path(__file__).resolve().parents[1]
    if target.exists() or target == repository or repository in target.parents:
        parser.error("El reporte no puede sobrescribir archivos ni guardarse en el repositorio")
    if target == args.nuevo.resolve() or target == args.base.resolve():
        parser.error("La salida no puede reemplazar los datos fuente")
    result = compare(archived_rows(args.base), incoming_rows(args.nuevo))
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["estado"] == "IGUAL_A_REFERENCIA" else 2


if __name__ == "__main__":
    raise SystemExit(main())
