# Catálogo SEO — etapa de previsualización privada

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

Esta etapa sigue **EN DESARROLLO**, no fue desplegada ni aprobada.
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

**Pendiente de aprobar Fase 1:** generar una salida real con copia local de ambos repositorios y conexión de solo lectura; ejecutar las pruebas Python; comparar lado a lado con Streamlit en móvil y escritorio; verificar las ocho ilustraciones, fotografías de categoría, modalidades excepcionales, redondeos, orden y PDF; resolver diferencias encontradas.

**No hacer todavía:** sincronizar mediante tareas periódicas, unir la rama a `main`, alterar Supabase/Streamlit, crear fichas indexables ni actualizar `sitemap.xml`.

**Advertencia:** la rama está en un repositorio GitHub público y ya contiene archivos `preview/datos/catalogo-*.json` de una prueba anterior. La etiqueta HTML `noindex` no restringe acceso a esos archivos. No subir datos privados, costos, credenciales o nuevos snapshots no aprobados.
