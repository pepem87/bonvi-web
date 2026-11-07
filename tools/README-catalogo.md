# BON VI — catálogo web separado (Fase 1 aprobada / Fase 2 en desarrollo)

**Criterio definitivo del 07/11/2026:** se trabaja únicamente en la rama
`desarrollo/catalogo-seo-l7` de `pepem87/bonvi-web`. No se publica en
`bonvimercat.com.ar`, no se modifica `main`, no se modifica el repositorio
interno `pepem87/Bonvi-Mercat`, Streamlit ni los datos de Supabase.

**Fase 1: aprobada por el usuario.** Se probó una copia ZIP aislada con 1.541
fichas, índice, filtros e informe PDF. Se conserva como referencia.
Las rutas `preview/index.html` y `preview/catalogo-completo.html` en el
repositorio son maquetas anteriores, no la ZIP final aprobada.

**Fase 2: todavía no terminada.** La sincronización se implementará y probará
de forma independiente; solo cuando el catálogo web completo se apruebe
expresamente se preparará su migración al dominio. El catálogo público actual
de Streamlit sigue disponible hasta entonces.

## Prueba de cambios de catálogo sin conectar ni modificar sistemas internos

El programa `tools/comparar_actualizacion_privada.py` compara los 16 JSON
originales de Fase 1 con una exportación nueva de **solo datos públicos de
productos**. No consulta la base, no genera fichas, no despliega ni escribe
archivos en la web. Detecta altas, bajas, precios, modalidades, nombres y
orden; todas las diferencias requieren revisión.

```bash
python tools/comparar_actualizacion_privada.py \
  --base preview/datos \
  --nuevo /ruta/privada/productos-vigentes.json \
  --reporte /ruta/privada/comparacion.json
```

El nuevo JSON tiene la forma de un arreglo de productos y solo acepta los
campos autorizados: código, producto, familia, presentación, UxB, modalidad,
precio persona unitario, orden L7, activo y rol. **No admite costos, márgenes,
clientes ni claves**. El informe debe guardarse fuera del repositorio.

Las pruebas incluyen una comparación de la referencia real de 1.541
productos consigo misma (cero cambios), una simulación de cambio de precio,
altas y bajas, modalidades y rechazo de campos contables internos.

## Prueba de equivalencia con Supabase — 07/11/2026

Se ejecutó una consulta real de **solo lectura** a Supabase y se compararon
huellas MD5 independientes con el `index.html` del ZIP aprobado que el usuario
compartió. Se verificaron los 1.541 códigos en su orden, nombres, familias,
presentaciones, precios unitarios y de venta, modalidad y UxB.

- Hash campos comerciales: `ff88b4140ceafd9d93d453cee9049444` en ambos orígenes.
- Hash precios/modos: `34911825f17b2fbe38122ec69d905bfc` en ambos orígenes.
- Hash orden de códigos: `11b613520c74c7eb0c801dd097f07ae6` en ambos orígenes.
- Sin diferencias. Vigencia observada: `2026-11-06T16:12:55.260294Z`.
- El PDF adjuntado y aprobado tiene 44 páginas.

Se comprobó **en memoria** que subir el precio unitario de prueba del código
2063 de $3.950 a $4.050 cambiaría el precio del bulto de seis unidades de
$23.700 a $24.300 y alteraría la huella de precios. **No se modificó ningún
precio real** ni se guardó esa simulación como nuevo catálogo.

**Estado:** equivalencia actual verificada; todavía falta comprobar una
regeneración efectiva de HTML + fichas + PDF desde una exportación posterior,
y luego automatizarla. Esta prueba no representa sincronización automática.

---

## Historial y documentación anterior


Este desarrollo vive solo en la rama `desarrollo/catalogo-seo-l7`.
**No modifica** la página actual, Streamlit, Supabase ni el sitemap público.

## Objetivo
Leer `public.productos` en modo solo lectura y generar páginas HTML de prueba.
Solo se extraen código, nombre, familia, presentación, unidades por bulto,
modalidad, precio para personas y estado. **Nunca** se consultan costos ni
precios para comercios.

## Ejecución en un entorno privado
Instalar `psycopg2-binary` en el entorno de prueba y configurar
`DATABASE_URL` como secreto del entorno, nunca en archivos ni commits.

```bash
python tools/catalogo_preview.py --output /tmp/bonvi-catalogo-preview --limit 20
```

La carpeta de salida debe estar fuera del repositorio y vacía.
Se generan `productos/<slug>-<codigo>/index.html` y un manifiesto
`manifest-preview.json` para revisión interna.

## Controles antes de publicar
- Confirmar qué significa `precio_persona_unit` en cada modalidad.
- Validar si el producto se ofrece por unidad o por bulto y el precio final.
- Confirmar categorías, descripciones, exclusiones y vigencia de L7.
- Validar páginas en móvil, enlaces, canonical, indexación y sitemap.
- Definir mecanismo automatizado de ejecución segura con credenciales privadas.
- Revisar una muestra y aprobar expresamente el despliegue.

Las páginas de prueba incluyen `noindex,nofollow` y **no se despliegan**.
No ejecutar contra producción desde un workflow público ni publicar el manifiesto
sin revisar contenido y permisos.

## Fase 1 — réplica del catálogo público (avance del 06/11/2026)

Esta etapa fue **APROBADA** por el usuario al probar el ZIP aislado. No fue desplegada.
Se tomó como referencia el archivo original `pages/0_📲_Catalogo_publico.py` de la rama `main` de `Bonvi-Mercat`.

**Incorporado al generador privado `catalogo_indice.py`:**
- ocho accesos principales, con los mismos agrupamientos públicos (GIN dentro de APERITIVOS, categorías de hogar dentro de OTROS);
- búsqueda por código, producto, familia, presentación, categoría y marca; alias tomados del código original;
- rango de precio con los mismos cinco tramos y selección de precio unitario / precio de venta;
- orden L7 por defecto, orden por precio y nombre; paginación de 80 resultados;
- formato de tarjeta en una columna, modalidad, precio del bulto y precio por unidad como referencia;
- información de vigencia del catálogo, enlace al PDF arriba y abajo, limpieza de filtros y accesos a redes;
- mapas de íconos e ilustraciones del código original: el generador integrado copia **archivos gráficos aprobados** desde un checkout local de Streamlit a la salida privada. No toma imágenes de productos de búsquedas ni enlaces GitHub privados.

**Arquitectura:** `generar_catalogo_integrado.py` sigue en modo SELECT, genera en una carpeta privada externa al repositorio y reutiliza las funciones originales de Streamlit para clasificación y precios. La rama actual `preview/index.html` y `preview/catalogo-completo.html` son maquetas anteriores: NO deben interpretarse como la salida del generador integrado actualizado.

**Controles disponibles:** `tools/test_catalogo_indice.py` incorpora pruebas de bulto/unidad, ausencia de costos, filtros en HTML, fichas individuales y rutas seguras de ilustraciones. Ejecutar en un checkout de prueba:

```bash
python -m unittest discover -s tools -p 'test_*.py'
```

**Historial de pendientes anterior a la aprobación del ZIP:** generar una salida real con copia local de ambos repositorios y conexión de solo lectura; ejecutar las pruebas Python; comparar lado a lado con Streamlit en móvil y escritorio; verificar las ocho ilustraciones, fotografías de categoría, modalidades excepcionales, redondeos, orden y PDF; resolver diferencias encontradas.

**No hacer todavía:** sincronizar mediante tareas periódicas, unir la rama a `main`, alterar Supabase/Streamlit, crear fichas indexables ni actualizar `sitemap.xml`.

**Advertencia:** la rama está en un repositorio GitHub público y ya contiene archivos `preview/datos/catalogo-*.json` de una prueba anterior. La etiqueta HTML `noindex` no restringe acceso a esos archivos. No subir datos privados, costos, credenciales o nuevos snapshots no aprobados.


## Auditoría de los 1.541 productos — 07/11/2026

Comprobación **de solo lectura** contra la tabla `public.productos` de la base vigente BON VI (marca de vigencia `2026-11-06T16:12:55.260294Z`) y los 16 archivos de datos de la rama de desarrollo.

- Registros totales en Supabase: **1.652**; activos y publicables según el SQL del catálogo: **1.541**; el resto (111) no debe publicarse.
- Registros comparados: **1.541 de Supabase frente a 1.541 de la muestra**, con **1.541 códigos únicos en cada origen**.
- Diferencias de **código presente, nombre, familia, presentación, UxB, modalidad efectiva, precio unitario personas, orden L7 y posición relativa:** **cero**.
- Control independiente adicional de los **1.541 precios de venta calculados** (precio unitario × UxB cuando corresponde) y de sus **1.541 etiquetas de venta bulto/unidad**: **cero diferencias** frente a los cálculos en Supabase. Desglose de visualización: **1.267 por bulto y 274 por unidad**.
- Modalidades efectivas: **1.270 BULTO** y **271 UNIDAD**, de las cuales **147** siguen la marca `PEDI POR UNIDAD` (todas constan efectivamente como UNIDAD en la BD).
- Excepciones detectadas: productos **1410, 1582 y 1947** llevan `modalidad=BULTO` y `uxb=1`. El catálogo original los muestra como **venta por unidad**, y se corrigió el generador de fichas y tarjetas para igualar este comportamiento.
- Sin precios unitarios nulos/no positivos, UxB inválido, UxB fraccionario ni nombres o familias vacíos.
- En los datos fuente hay **446 presentaciones vacías** y **130 órdenes L7 nulos**. Se verificó que ambas condiciones están iguales en la muestra; el catálogo original omite presentaciones vacías y ordena valores nulos al final.

**Alcance preciso:** esta auditoría demuestra equivalencia de los datos fuente y reglas de modalidad examinadas. No demuestra todavía la reproducción visual de todas las tarjetas, el resultado de todas las categorías o filtros con el motor Python original, la generación efectiva del PDF, ni el despliegue y la sincronización. Antes de cerrar la Fase 1, ejecutar el generador integrado, correr pruebas Python y comparar una salida real de extremo a extremo con Streamlit.

Ninguna consulta de esta auditoría modificó Supabase; los ajustes permanecen exclusivamente en la rama `desarrollo/catalogo-seo-l7`.
