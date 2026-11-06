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
