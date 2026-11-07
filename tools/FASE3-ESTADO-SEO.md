# Fase 3 SEO — primer paquete privado (07/11/2026)

## Estado
**PREPARACIÓN SEO GENERADA Y AUDITADA EN PRIVADO. NO PUBLICADA.**

El usuario autorizó pasar a Fase 3 luego de cerrar Fase 2. Se conserva el
catálogo privado que ya aprobó. NO se hace merge a `main`, no se suben
archivos generados al sitio, no se actualiza Search Console ni se modifica
el repositorio operativo `pepem87/Bonvi-Mercat` ni Supabase.

## Arquitectura de URLs PROPUESTA (pendiente de aprobación en Fase 4)
- Índice: `https://bonvimercat.com.ar/catalogo/`
- Fichas: `https://bonvimercat.com.ar/catalogo/productos/<slug>-<codigo>/`
- Listado de categoría: `https://bonvimercat.com.ar/catalogo/categorias/<categoria>/`

**Motivo:** mantener intacta la portada actual `/`, y que todos los
archivos HTML y gráficos del catálogo funcionen dentro de `/catalogo/`
sin reescribir la web existente. Son canónicas planificadas, no URLs
presentemente publicadas.

## Verificaciones concluidas en paquete local
- 1.541 productos y 1.541 fichas HTML sin modificación del catálogo JSON.
- 16 subcategorías comerciales originales con páginas HTML y enlaces estáticos a productos;
  los **ocho botones principales** del catálogo anterior permanecen intactos.
- Un índice SEO del catálogo: total **1.558 URLs únicas** (1 índice, 16 categorías,
  1.541 fichas).
- 1.558 títulos y descripciones; canónicas únicas y con destino planificado.
- Datos estructurados `WebSite` en el índice y `BreadcrumbList` en
  categorías y fichas; sin inventar reviews, fotografías, disponibilidad o stock.
- **1.558 HTML mantienen `noindex,nofollow`.**
- Borrador `sitemap-CANDIDATO-NO-PUBLICAR.xml` guardado **fuera** del ZIP de prueba;
  no es el sitemap existente de producción ni se subió a Search Console.
- PDF original copiado byte a byte sin cambio de diseño ni precios.
- La CI de la rama de desarrollo en GitHub finalizó SUCCESS.
- Pruebas de HTML/JSON/XML/SEO local validadas; prueba visual automatizada de
  navegador no ejecutable en este entorno (navegador bloqueó acceso local).
  No atribuirle una validación visual que no ocurrió.

## Materiales recuperables
- Código versionado: `tools/bonvi_fase3_seo_privado.py`
- Pruebas versionadas: `tools/test_fase3_seo_privado.py`
- Copias privadas en Biblioteca ChatGPT: `/BON VI MERCAT/Catalogo privado/Fase 3 SEO/`
  (generador, ZIP SEO, informe JSON y sitemap candidato).
- El ZIP SEO privado puede descargarse en la conversación y abrirse localmente
  con `index.html`, extrayendo la carpeta completa.

## Decisiones técnicas
- Las 16 categorías corresponden a categorías efectivas de los 1.541 SKU,
  pero NO modifican los filtros ni los botones existentes.
- No se añadió `Product`/ `Offer` enriquecido para Google Shopping:
  no tenemos imágenes reales verificadas por SKU, stock cierto ni
  elegibilidad de compra verificada. La indexación orgánica de las fichas
  no depende necesariamente de ese enriquecimiento.
- No se publicó `robots.txt` nuevo ni se bloqueó por robots una página
  con `noindex`. El acceso a la web pública queda sin cambios.
- Al integrar en `/catalogo/`, `noindex` deberá retirarse
  **únicamente después de validar su URL canónica real y acceso HTTP 200**.
  Después se fusionará el sitemap candidato con el sitemap público
  vigente, conservando las URLs ya publicadas.

## Pendiente para completar Fase 3 y autorizar Fase 4
1. Revisión visual y funcional del nuevo ZIP por el usuario en escritorio y celular.
2. Confirmar la ruta de integración `/catalogo/` y la prioridad de las 16
   páginas de categoría; revisar títulos/descripciones de productos clave.
3. Revisar errores de navegación visual, enlaces y el contenido de categorías.
4. Preparar checklist de lanzamiento/activación SEO sin tocar producción.
5. Fase 4 será la única etapa de integración en el dominio, con aprobación
   explícita y validación previa del cambio.

## Referencias de SEO (Google Search Central)
- https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap
- https://developers.google.com/search/docs/crawling-indexing/block-indexing
- https://developers.google.com/search/docs/appearance/structured-data/breadcrumb
- https://developers.google.com/search/docs/appearance/structured-data/merchant-listing
