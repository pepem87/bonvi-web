"""Obtener SOLO datos publicables de la última L7 aprobada.
No escribe en Supabase. No guarda credenciales ni el snapshot en GitHub.
"""
import argparse
from decimal import Decimal, InvalidOperation
import hashlib
import json
import os
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

API = "/rest/v1/"
PAGE_SIZE = 500

def api_get(resource, query):
    url = os.environ.get("BONVI_SUPABASE_URL", "").rstrip("/")
    key = os.environ.get("BONVI_SUPABASE_SERVICE_ROLE_KEY", "")
    if not url or not key:
        raise RuntimeError("Faltan secretos de lectura BONVI_SUPABASE_URL / BONVI_SUPABASE_SERVICE_ROLE_KEY")
    endpoint = url + API + resource + "?" + urlencode(query)
    request = Request(endpoint, headers={
        "apikey": key, "Authorization": "Bearer " + key,
        "Accept": "application/json", "User-Agent": "bonvi-approved-l7-publisher/1.0"
    })
    with urlopen(request, timeout=40) as response:
        return json.loads(response.read().decode("utf-8"))

def latest_approval():
    carga = api_get("cargas_l7", {
        "select": "id,estado,vigencia", "order": "id.desc", "limit": 1
    })
    vig = api_get("parametros", {
        "select": "valor", "clave": "eq.vigencia_catalogo", "limit": 1
    })
    if len(carga) != 1 or len(vig) != 1:
        raise RuntimeError("No se encontró la L7 aprobada o su vigencia")
    a, b = carga[0], vig[0]
    if a["estado"] != "APROBADA" or a["vigencia"] != b["valor"]:
        raise RuntimeError("La L7 no está aprobada o su vigencia difiere del parámetro vigente")
    return {"id": int(a["id"]), "estado": a["estado"],
            "vigencia": a["vigencia"], "parametro": b["valor"]}

def public_rows():
    raw = []
    offset = 0
    while True:
        chunk = api_get("productos", {
            "select": "codigo,producto,familia,presentacion,uxb,modalidad,precio_persona_unit,orden_l7,rol",
            "activo": "eq.1", "precio_persona_unit": "gt.0",
            "order": "codigo.asc", "limit": PAGE_SIZE, "offset": offset
        })
        raw.extend(chunk)
        if len(chunk) < PAGE_SIZE:
            break
        offset += PAGE_SIZE
        if offset > 100000:
            raise RuntimeError("Volumen inesperado de productos")
    result = []
    seen = set()
    for r in raw:
        if "BLOQUEADO" in str(r.get("rol") or "").upper():
            continue
        code = int(r["codigo"])
        if code in seen or code <= 0:
            raise RuntimeError("Código duplicado o inválido")
        seen.add(code)
        uxb = Decimal(str(r.get("uxb") or 1))
        if not uxb.is_finite() or uxb <= 0 or uxb != uxb.to_integral_value():
            raise RuntimeError("UxB no válido para SKU " + str(code))
        price = Decimal(str(r["precio_persona_unit"]))
        rounded = price.quantize(Decimal("0.01"))
        if not price.is_finite() or price <= 0 or abs(rounded-price) > Decimal("0.005"):
            raise RuntimeError("Precio público no válido para SKU " + str(code))
        mode = str(r.get("modalidad") or "")
        if mode not in ("BULTO", "UNIDAD"):
            raise RuntimeError("Modalidad no válida para SKU " + str(code))
        result.append([
            code, str(r.get("producto") or ""), str(r.get("familia") or ""),
            str(r.get("presentacion") or ""), int(uxb), mode,
            format(rounded, ".2f"), r.get("orden_l7")
        ])
    return result

def collect():
    before = latest_approval()
    rows = public_rows()
    after = latest_approval()
    if before != after:
        raise RuntimeError("Cambió la aprobación L7 durante la exportación; abortado")
    if not rows:
        raise RuntimeError("No hay productos publicables; abortado")
    return {"meta": {**before, "n": len(rows)}, "rows": rows}

def digest(snapshot):
    normalized = json.dumps(snapshot, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

def main():
    cli = argparse.ArgumentParser()
    cli.add_argument("--snapshot", type=Path, required=True)
    cli.add_argument("--fingerprint", type=Path, required=True)
    cli.add_argument("--verify", action="store_true")
    cli.add_argument("--existing-marker", type=Path)
    cli.add_argument("--expected-id", type=int, default=0)
    args = cli.parse_args()
    snapshot = collect()
    current_id = snapshot["meta"]["id"]
    if args.expected_id and current_id != args.expected_id:
        raise RuntimeError("La aprobación cambió desde el evento: " + str(args.expected_id))
    if args.verify:
        saved = json.loads(args.fingerprint.read_text())
        if saved["id"] != current_id or saved["sha256"] != digest(snapshot):
            raise RuntimeError("El catálogo aprobado cambió durante la sincronización")
        print("Snapshot validado de nuevo: L7 #" + str(current_id))
        return
    if args.existing_marker and args.existing_marker.exists():
        existing = json.loads(args.existing_marker.read_text())
        if int(existing.get("l7", 0)) >= current_id:
            print("La versión aprobada ya se encuentra en GitHub.")
            with open(os.environ["GITHUB_OUTPUT"], "a") as output:
                output.write("update=false\n")
            return
    args.snapshot.write_text(json.dumps(snapshot, ensure_ascii=False), encoding="utf-8")
    args.fingerprint.write_text(json.dumps({"id": current_id, "sha256": digest(snapshot)}))
    with open(os.environ["GITHUB_OUTPUT"], "a") as output:
        output.write("update=true\n")
    print("L7 aprobada para publicar #" + str(current_id) + ": " + str(len(snapshot["rows"])) + " publicables")

if __name__ == "__main__":
    main()
