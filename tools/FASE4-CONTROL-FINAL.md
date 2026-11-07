# BON VI MERCAT — Control final de la Fase 4 (07/11/2026)

**Estado: VALIDACIÓN PRIVADA SUPERADA. NO SE PUBLICÓ.**

## Prueba efectuada en Windows por el usuario
La copia local de la portada real de BON VI se abrió correctamente y el botón «Ver catálogo actualizado» permitió ingresar al catálogo propio. El usuario ya había probado satisfactoriamente WhatsApp, Instagram y filtros del catálogo en la Fase 3.

## Auditoría automatizada del ZIP SEO privado real
- **1.541** SKU únicos y **1.541** fichas individuales.
- **16** páginas de categorías, **1.558** páginas HTML en total con `noindex`.
- **6.215** referencias locales dentro del catálogo verificadas; **0** rotas.
- **1.541** enlaces de categoría hacia las fichas; **1.558** URL canónicas únicas.
- PDF de **44** páginas: **1.541** SKU y **3.082** precios verificados.
- Sitemap **candidato**, no publicado, con 1.558 URLs.
- **0 errores** estructurales.

## Pruebas interactivas en Chromium
**32/32 correctas:** escritorio a 1440 px y móvil a 390 px, búsqueda SKU 2063, precio de bulto/unidad, categoría VINOS, intervalo de precios, cambio precio unitario/de venta, limpieza, ficha enlazada, navegación por categoría, ausencia de excepciones JS y desbordes horizontales.

La prueba automática cargó HTML con `set_content` debido a restricciones de acceso a `file://` y `localhost`; por tanto, **no reemplaza** la comprobación de recursos por HTTP en el dominio. La apertura integrada portada/catálogo en Windows fue comprobada por el usuario.

## Revisión semántica antes de publicar
- El acceso **Otros** de la portada dirige al índice general porque el catálogo no contiene una subcategoría SEO `Otros`; cuidado personal y hogar sí existe como categoría.
- El acceso **Gin/Aperitivos** apunta a Aperitivos, mientras que las 46 fichas de Gin son una categoría SEO distinta. Revisar si se desea enlace directo a Gin o una página combinada antes de migrar.
- Estos puntos **no impiden abrir el catálogo**, pero conviene resolverlos para evitar confusión comercial.

## Alcance del cierre
- GitHub `pepem87/bonvi-web/main`, `bonvimercat.com.ar`, `pepem87/Bonvi-Mercat`, Streamlit y los datos de Supabase **no modificados en estas pruebas**.
- Integración y scripts solamente en `desarrollo/catalogo-seo-l7`, con vistas de ensayo privadas.
- Se prohíbe subir el ZIP de pruebas tal como está: conserva `noindex`, no tiene `CNAME`, y la sincronización/publicación requiere una secuencia controlada.

## Próxima etapa: preparación de lanzamiento
1. Preparar resguardo del commit actual de `main` y plan de reversión.
2. Publicar primero los recursos y URLs nuevas sin romper los destinos antiguos, verificando HTTP 200 y enlaces reales; nunca afirmar que están indexados solo porque existan.
3. Una vez verificado, cambiar gradualmente los 13 enlaces que hoy conducen a Streamlit.
4. Tras asegurar canonicals y rutas, retirar `noindex` de las URLs elegibles, unir sitemap candidato al público existente y verificar Search Console.
5. Mantener el catálogo público de Streamlit como respaldo hasta la aprobación explícita de retiro.

**La publicación real requiere autorización expresa del usuario.** Avanzar de fase no implica despliegue irreversible.
