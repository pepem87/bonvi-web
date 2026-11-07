"""Reglas de presentación comercial del catálogo SEO (sin acceso a base de datos).

Los importes se calculan únicamente para una previsualización privada.
Antes de publicar se debe contrastar el redondeo y las reglas vigentes de Streamlit.
"""
from decimal import Decimal, ROUND_HALF_UP


def money(value):
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def public_offer(modalidad, uxb, precio_persona_unit):
    mode = str(modalidad or "").strip().upper()
    units = Decimal(str(uxb))
    unit_price = money(precio_persona_unit)
    if unit_price <= 0 or units <= 0 or units != units.to_integral_value():
        raise ValueError("Precio o cantidad por bulto inválidos")
    # Igual que el catálogo Streamlit: BULTO con UxB=1 se exhibe por unidad.
    if mode == "BULTO" and units > 1:
        return {"tipo": "bulto", "cantidad": int(units),
                "precio_total": money(unit_price * units),
                "precio_unitario_referencia": unit_price}
    if mode in {"UNIDAD", "BULTO"}:
        return {"tipo": "unidad", "cantidad": 1,
                "precio_total": unit_price,
                "precio_unitario_referencia": unit_price}
    raise ValueError("Modalidad desconocida: no publicar")


if __name__ == "__main__":
    assert public_offer("BULTO", 24, 2150)["precio_total"] == Decimal("51600.00")
    assert public_offer("UNIDAD", 12, 2150)["precio_total"] == Decimal("2150.00")
    assert public_offer("BULTO", 1, 46750)["tipo"] == "unidad"
    print("Reglas de modalidad: OK")
