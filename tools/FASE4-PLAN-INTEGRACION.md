# BON VI MERCAT — Fase 4: integración segura a la web

**Estado: EN DESARROLLO / SIN PUBLICAR**  
**Inicio: 07/11/2026.** La revisión visual y funcional de Fase 3 fue aprobada por el usuario: WhatsApp, Instagram, filtros y navegación del catálogo funcionan.

## Qué está preparado
- Integración propuesta bajo **`https://bonvimercat.com.ar/catalogo/`**, sin reemplazar la portada.
- Mantener intactas las páginas existentes `/vinos-la-plata/`, `/cervezas-la-plata/`, `/gin-la-plata/`, `/whisky-la-plata/`, `/aceites-y-acetos-la-plata/`, `robots.txt`, `CNAME` y el sitemap público vigente.
- **13 enlaces de prueba** actualizados únicamente en la rama `desarrollo/catalogo-seo-l7`: ocho de la portada (dos al catálogo general, seis por categoría) y uno en cada una de las cinco páginas de rubro.
- Las rutas del catálogo apuntan al sitio propio `/catalogo/`. Para el enlace "Otros" se usa provisoriamente el índice general porque todavía no existe una página agregada `categorias/otros/`.
- El generador `tools/fase4_montar_sitio_privado.py` está diseñado para tomar un checkout **de solo lectura** del sitio web en `main` y el ZIP **aprobado** de Fase 3, montar el sitio entero en una carpeta nueva, revisar que todas las rutas funcionen, generar un ZIP **NO PUBLICAR**, un informe y un sitemap **CANDIDATO**.
- Pruebas automatizadas de ensamblado con sitio de ejemplo: **SUCCESS**. No representan un despliegue del dominio.

## Protocolo para crear una copia de ensayo con el sitio REAL

Con un checkout local de `pepem87/bonvi-web` en la rama principal y el ZIP Fase 3 aprobado:

```powershell
python tools/fase4_montar_sitio_privado.py `
  --web-root "C:\ruta-privada\bonvi-web-main" `
  --catalog-zip "C:\ruta-privada\BONVI_Fase3_SEO_Privado_1541.zip" `
  --output "C:\ruta-privada\ensayo-fase4"
```

Se obtienen:
- `ensayo-fase4/sitio/index.html`: portada original con enlaces locales al catálogo propio.
- `ensayo-fase4/sitio/catalogo/index.html`: índice con 1.541 productos.
- 16 páginas de categoría y 1.541 fichas dentro de `sitio/catalogo/`.
- `ensayo-fase4/BONVI_Fase4_Ensayo_Privado_NO_PUBLICAR.zip`: sitio completo listo para **revisión local**, pero **NO para publicar**. El CNAME se omite intencionalmente.
- `ensayo-fase4/sitemap-CANDIDATO-SOLO-PARA-REVISION.xml`: propuesta que agrega 1.558 direcciones al sitemap actual, sin sobrescribirlo.
- `ensayo-fase4/informe-fase4.json`: número de enlaces corregidos, fichas, categorías, sitemap y enlaces rotos.

La vista de ensayo incluye `noindex` en todas las páginas y no altera el checkout de entrada, ni el repositorio privado de Streamlit ni Supabase.

## Últimos controles antes de decidir publicar

1. Ejecutar el generador con **el checkout REAL** de la web actual y el ZIP Fase 3 aprobado. El CI de prueba usa datos sintéticos, no sustituye esta ejecución.
2. Abrir la copia integrada en escritorio y celular; comprobar portada, enlaces, PDF, búsqueda, menús y las páginas antiguas.
3. Revisar especialmente el destino de **Otros** (actualmente catálogo general), las páginas `gin`/aperitivos y `aceites`/acetos para asegurar expectativas comerciales.
4. Antes del despliegue, obtener una copia/registro del estado de `main` que permita restaurar la web rápidamente.
5. **Solo con autorización expresa para publicar:** copiar los archivos nuevos a `/catalogo/`, actualizar los enlaces del sitio principal, comprobar respuestas HTTP 200 y canonicals, retirar `noindex` de las páginas públicas ya verificadas, y agregar las URLs de catálogo al sitemap público. Luego controlar Search Console. Hacer estos cambios en orden seguro para evitar páginas sin destino.
6. **No desactivar el catálogo público Streamlit** hasta verificar en el dominio que todo funciona, y el usuario autorice esa última transición.

## Prohibiciones vigentes
**No cambiar `pepem87/bonvi-web/main`, `bonvimercat.com.ar`, `pepem87/Bonvi-Mercat`, app Streamlit, Supabase ni sitemap público durante la etapa de ensayo. No dar por publicada ni indexada ninguna página del catálogo.**
