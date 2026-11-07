# BON VI MERCAT — Publicación oficial del catálogo (07/11/2026)

## ESTADO: PUBLICADO Y VERIFICADO EN DOMINIO REAL

El usuario autorizó explícitamente la publicación y aclaró la regla comercial:
- **OTROS**: cuidado personal y hogar (OFF, COLGATE, DOVE).
- **APERITIVOS**: los 27 de aperitivos más los 46 de Gin, total 73.
Esto se preservó en el buscador JS, en la selección por URL y en los enlaces de la portada.

### Publicación por etapas y puntos de reversión

**Pre-publicación original de main:** \`ef6b1d1949a00bf62a1dd26c0f33c3c6bb0c9dad\`.

**Etapa 1 — catálogo protegido (sin cambiar enlaces existentes):**
\`ad17e86db587db9b19119342576a9f36a051c88b\`.
Se incorporó únicamente \`/catalogo/\` con 1.541 fichas, 16 categorías y 44 páginas PDF. En todas las fichas se conservó \`noindex\`. La portada y el sitemap público todavía apuntaban al sistema anterior. El dominio real devolvió el HTML y el PDF con hashes idénticos al ZIP revisado.

**Etapa 2 — integración y SEO activa:**
\`8ede2f162950a52dfff701e6647595d6c5dd9019\`.
Se actualizaron 13 enlaces de la portada y las cinco páginas de rubro (VINOS, CERVEZAS, WHISKYS, APERITIVOS/Gin, ACEITES, OTROS), se retiró \`noindex\` de las **1.558 páginas** del catálogo, se publicó el sitemap de **1.564 URLs** y se conservaron \`CNAME\`, \`robots.txt\`, HTML base y recursos originales.

### Evidencias de despliegue real

- GitHub Pages, segunda publicación: [SUCCESS](https://github.com/pepem87/bonvi-web/actions/runs/42419334713).
- Verificación HTTP en el **dominio real**: [SUCCESS](https://github.com/pepem87/bonvi-web/actions/runs/42419560124).
- Se probaron por HTTP la portada, el catálogo y sus filtros de entrada por URL, fichas, Gin, Otros, el PDF con checksum y el sitemap.
- PDF original SHA256: \`6a8f2a3256b1bf6119228be130ad1e60e48d80aaee451912d861178d7fb2c120\`.
- 1.541 fichas, 16 páginas de categoría, 1 índice, sitemap sin duplicados.
- Las pruebas Playwright del filtro por URL confirmaron: OTROS 4 productos; APERITIVOS+GIN 73; VINOS 1.140.
- Archivos y datos en \`pepem87/Bonvi-Mercat\`, Streamlit y Supabase permanecieron intactos.

### URLs principales

- https://bonvimercat.com.ar/
- https://bonvimercat.com.ar/catalogo/
- https://bonvimercat.com.ar/catalogo/?categoria=OTROS
- https://bonvimercat.com.ar/catalogo/?categoria=APERITIVOS
- https://bonvimercat.com.ar/catalogo/catalogo-personas.pdf
- https://bonvimercat.com.ar/sitemap.xml

### Reversión de emergencia, si es necesario

Para restaurar los enlaces de Streamlit y volver a \`noindex\` sin borrar el catálogo protegido, **revertir exclusivamente el commit de la etapa 2** sobre \`main\`: \`8ede2f162950a52dfff701e6647595d6c5dd9019\`. Hacer un nuevo commit de reversión sin forzar la rama. Si se desea deshacer toda la publicación, revertir después el commit de la etapa 1 (\`ad17e86...\`). No modificar el repositorio privado de Streamlit ni la base Supabase.

### Avisos operativos IMPORTANTES

1. La publicación es **estática** con los precios vigentes al \`2026-11-06T16:12:55.260294Z\`. Antes de publicar se cotejó nuevamente con Supabase: los 1.541 registros y los hashes de precios coincidieron.
2. La tarea de ChatGPT **Sincronizar catálogo BON VI privado** actualiza solamente la copia **privada**, **NO modifica automáticamente los precios en la web oficial**. Antes de cambiar precios en Supabase deberá definirse y probarse una actualización pública controlada; no suponer que ya existe.
3. El catálogo público anterior de Streamlit sigue disponible como respaldo. **No retirar el módulo ni desactivar la app**, que permanece como sistema de gestión.
4. Se publicó \`sitemap.xml\`, pero no se envió explícitamente a Search Console por esta operación. **Publicado e indexable no significa indexado en Google**; controlar Search Console y esperar rastreo.
5. Si un cliente encuentra un enlace o precio incorrecto, revertir la etapa 2 en primer lugar, investigar y volver a desplegar solo cuando esté corregido.

### Próxima etapa

**Fase 5 — operaciones posteriores al lanzamiento:** prueba del usuario desde celular y PC, Search Console, seguimiento de errores reales, desarrollo de una sincronización pública estable y retiro del catálogo público de Streamlit solamente tras aprobación explícita del usuario.
