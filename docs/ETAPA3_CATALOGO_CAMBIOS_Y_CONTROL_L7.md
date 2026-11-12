# BON VI MERCAT — Etapa 3, 11/11/2026

Estado: diseño aprobado por el usuario e integrado en `catalogo/index.html` en rama `main`, commit `5969f2c2c08ada4d4b3aa705720c388fa903bb37`.

## Cambios visuales aprobados
- Encabezado marfil limpio: logo original, Inicio, Catálogo, Instagram, WhatsApp.
- Rótulo de precio: `Precio bulto xN` o `Precio por unidad`.
- En los productos vendidos por bulto, el valor unitario sigue siendo informativo y hay un botón `i` accesible por clic/tap/teclado que explica que no implica venta individual.
- **Sin** descripción inventada de sabor o notas de cata.
- No cambiar precio, UxB, categorías, íconos de categorías, filtrado, búsqueda, PDF, paginación, ni sistema Streamlit.

## Validación realizada al publicar
- Los 1.541 objetos de producto del catálogo original y actualizado son idénticos.
- Distribución actual: 1.267 vendidos por bulto y 274 por unidad.
- `index,follow`, canonical original, PDF, perPage=80, filtros y recursos de categorías conservados.
- Modificaciones limitadas a HTML, CSS y eventos de ayuda informativa del catálogo público.

## Advertencia para la próxima actualización L7
No se localizó ni se modificó con certeza el proceso/generador que reescribe `catalogo/index.html`. Si ese proceso reemplaza completamente el HTML, puede sobrescribir estas mejoras. **Antes de actualizar/publicar L7:** verificar que persisten `catalog-header`, `price-info`, `info-trigger`, `price-tooltip` y `Precio bulto x`; si no están, aplicar nuevamente las mejoras al generador o a su salida y validar antes de publicar. No tocar la app interna.

Vista previa anterior de referencia: `vista-previa-catalogo-etapa3/index.html` (noindex).
