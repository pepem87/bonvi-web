#!/usr/bin/env python3
"""Auditoría integral OFFLINE: 1.541 SKU, PDF y HTML sin modificar la producción.

Necesita dos checkouts locales y las dependencias de la app original.
No se conecta a Supabase: utiliza exclusivamente el snapshot ya comparado
con la base el 07/11/2026. No publicar la salida sin aprobarla.
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def load_archived_rows(data_dir):
    files = sorted(Path(data_dir).glob("catalogo-??.json"))
    if len(files) != 16:
        raise ValueError(f"Se esperaban 16 fragmentos, existen {len(files)}")
    rows = []
    for f in files:
        chunk = json.loads(f.read_text(encoding="utf-8"))
        if not isinstance(chunk, list):
            raise ValueError(f"Archivo no es una lista: {f.name}")
        rows.extend(chunk)
    if len(rows) != 1541:
        raise ValueError(f"Se esperaban 1541 SKU: se encontraron {len(rows)}")
    codes = [str(row.get("codigo")) for row in rows]
    if len(set(codes)) != len(codes):
        raise ValueError("Hay codigos duplicados")
    actual_bulto = 0
    actual_unidad = 0
    for r in rows:
        unit = float(r["precio_persona_unit"])
        uxb = float(r["uxb"])
        mode = str(r["modalidad"])
        if unit <= 0 or uxb <= 0 or not uxb.is_integer():
            raise ValueError(f"Cantidad o precio no valido en SKU {r['codigo']}")
        if mode not in {"BULTO", "UNIDAD"}:
            raise ValueError(f"Modalidad no valida en SKU {r['codigo']}")
        if mode == "BULTO" and uxb > 1:
            actual_bulto += 1
        else:
            actual_unidad += 1
    if (actual_bulto, actual_unidad) != (1267, 274):
        raise ValueError("Desglose de modalidad visual divergente")
    return rows


def audit(original, output, data_dir, vigencia):
    if not original.is_dir():
        raise FileNotFoundError(f"No existe directorio de Streamlit: {original}")
    script = Path(__file__).with_name("generar_catalogo_integrado.py")
    if output.exists() and any(output.iterdir()):
        raise ValueError("Salida debe estar vacia para no sobrescribir pruebas")
    if Path.cwd().resolve() == output or Path.cwd().resolve() in output.parents:
        raise ValueError("La carpeta de pruebas debe estar fuera del repositorio")
    rows = load_archived_rows(data_dir)

    with tempfile.TemporaryDirectory(prefix="bonvi-snapshot-") as temp:
        snapshot = Path(temp) / "snapshot-privado.json"
        # Todos los registros activos cumplen el filtro publicable a fecha del
        # snapshot. Para una publicacion futura, usar consulta real de Supabase.
        snapshot.write_text(json.dumps({
            "catalogo": rows, "pdf": rows, "vigencia": vigencia
        }, ensure_ascii=False), encoding="utf-8")

        env = dict(os.environ)
        env.pop("DATABASE_URL", None)  # fuerzo modo offline de solo lectura
        cmd = [sys.executable, str(script), "--streamlit-dir", str(original),
               "--output", str(output), "--snapshot", str(snapshot)]
        subprocess.run(cmd, check=True, env=env)

    checks = {}
    control_file = output / "control-privado.json"
    report = json.loads(control_file.read_text(encoding="utf-8"))
    checks["1541_SKU"] = report["productos"] == len(rows) == 1541
    checks["sin_errores_integridad"] = not report.get("errores")
    checks["1541_PDF_fuente"] = report["pdf_productos"] == 1541
    pdf = output / "catalogo-personas.pdf"
    checks["PDF_generado"] = pdf.is_file() and pdf.read_bytes()[:5] == b"%PDF-"
    index_file = output / "index.html"
    page = index_file.read_text(encoding="utf-8")
    checks["noindex_pruebas"] = 'content="noindex,nofollow"' in page
    checks["80_por_pagina"] = "perPage=80" in page
    checks["1541_productos_indexados_en_JSON"] = page.count('"codigo": ') == 1541
    checks["fichas_individuales"] = len(list((output / "productos").glob("*/index.html"))) == 1541
    checks["logo_original"] = (output / "assets/logo_bon_vi_mercat.png").is_file()
    checks["fondo_original"] = (output / "assets/web_mockup.png").is_file()
    checks["ocho_iconos_botones"] = all((output / "assets/button_icons" / x).is_file()
                                        for x in ("vinos.webp", "champagnes.webp",
                                                  "cervezas.webp", "jugos.webp",
                                                  "whiskys.webp", "aperitivos.webp",
                                                  "aceites.webp", "otros.webp"))
    checks["sin_campo_costo"] = '"costo_unitario":' not in page
    checks["sin_precio_comercio"] = '"precio_comercio_unit":' not in page
    checks["sin_credenciales"] = "DATABASE_URL=" not in page

    result = {
        "estado": "APROBADO" if all(checks.values()) else "FALLA",
        "snapshot_fecha": vigencia,
        "productos": len(rows),
        "controles": checks,
        "observacion": "Auditoria offline, no prueba de publicacion ni sincronizacion"
    }
    (output / "reporte-auditoria.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    for name, ok in checks.items():
        print(("OK   " if ok else "ERROR") + " " + name)
    if not all(checks.values()):
        raise RuntimeError("Una o mas verificaciones fallaron; NO PUBLICAR")
    print("VALIDACION OFFLINE SUPERADA: 1541 productos, PDF y fichas privadas")
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--streamlit-dir", required=True,
                   help="Ruta absoluta a la app original Bonvi-Mercat")
    p.add_argument("--output", required=True,
                   help="Directorio privado vacio y fuera del repositorio")
    p.add_argument("--data-dir", default=str(Path(__file__).resolve().parents[1] /
                                              "preview" / "datos"),
                   help="Ruta a los 16 fragmentos publicos ya auditados")
    p.add_argument("--vigencia", default="2026-11-06T16:12:55.260294Z")
    args = p.parse_args()
    audit(Path(args.streamlit_dir).resolve(),
          Path(args.output).resolve(),
          Path(args.data_dir).resolve(), args.vigencia)


if __name__ == "__main__":
    main()
