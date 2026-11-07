# Fase 2 — sincronización segura del catálogo BON VI

Estado: **preparación y control; sin publicación automática** (07/11/2026).

## Referencia aprobada
Copia privada del catálogo del 06/11/2026: 1.541 SKU, 44 páginas PDF, ocho accesos de categorías. No modificar el diseño ni las reglas de la Fase 1.

## Arquitectura acordada
1. **Origen único:** `public.productos` y `public.parametros` de Supabase. Acceso SQL exclusivamente de solo lectura, mediante credenciales secretas fuera del repositorio.
2. **Reglas:** usar `tools/generar_catalogo_integrado.py`, `tools/puente_catalogo_streamlit.py` y el PDF original del repositorio privado `pepem87/Bonvi-Mercat`. No duplicar precios ni categorías.
3. **Destino temporal:** generar HTML, fichas y PDF en un directorio privado nuevo, fuera de ambos repositorios.
4. **Control obligatorio:** comparar con la última copia aprobada; verificar códigos únicos, precios positivos, UxB, modalidad de venta, exclusiones, integridad del PDF, recursos gráficos, ausencia de costos y credenciales. Variaciones de precio superiores al 30%, cualquier alta/baja o cambio de modalidad/categoría se elevan a revisión.
5. **Publicación:** deshabilitada en esta etapa. No actualizar `main`, `sitemap.xml`, dominio ni estado de Supabase. Mantener `noindex` durante las pruebas.
6. **Automatización:** habilitar primero ejecución manual con secretos seguros y controles, después definir horario y política de aprobación. No conectar un workflow de un repositorio público a un repositorio privado sin revisar el alcance del token.

## Comprobación de origen del 07/11/2026
Supabase: 1.652 registros; 1.541 publicables con códigos únicos; marcador `2026-11-06T16:12:55.260294Z`.

## Próximos pasos
- Incorporar y probar guardas automáticas contra una nueva generación privada real, además de los tests unitarios.
- Crear una ejecución manual de solo lectura y confirmar permisos secretos sin exposición en logs.
- Revisar con el usuario el primer reporte de cambios. Solo entonces habilitar actualización automática o publicación.

**No hubo cambios a Streamlit, Supabase, la web pública o el código aprobado en esta etapa.**
