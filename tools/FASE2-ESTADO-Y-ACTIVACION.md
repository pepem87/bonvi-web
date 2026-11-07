# Fase 2: estado y ejecución aislada (07/11/2026)

## Acuerdo de alcance
- La versión aprobada por el usuario es la Fase 1, con 1.541 productos, índice, fichas y PDF de 44 páginas.
- Trabajar SOLO en la rama `desarrollo/catalogo-seo-l7` de `pepem87/bonvi-web`.
- No desplegar ni modificar `bonvimercat.com.ar` / `main`.
- No escribir ni modificar el repositorio interno `pepem87/Bonvi-Mercat`, Streamlit, pedidos, precios ni Supabase.
- El catálogo público de Streamlit sigue activo hasta la migración final (Fase 4/5).
- No publicar nuevos ZIP de prueba en el repositorio GitHub público; los ZIP se generan en disco privado.

## Controles completados

- 1.541/1.541 SKU coinciden con la base Supabase; cero diferencias en campos de catálogo y orden.
- Documento HTML y PDF aprobados fijados mediante SHA256 en `tools/fase2_referencia_aprobada.json`.
- PDF aprobado: 44 páginas, 1.541 códigos presentes en filas propias, 1.541 precios unitarios y 1.541 precios de venta verificados, cero diferencias.
- `fase2_generar_paquete_privado.py` genera un paquete privado con `index.html`, todas las fichas, imágenes originales y PDF producido por el código original, valida los 3.082 precios e impide publicar automáticamente.
- CI: pruebas automatizadas de precios, modalidades, campos prohibidos, fichas y PDF, ejecutadas al actualizar esta rama de desarrollo.
- `fase2_ejecutar_privado.ps1` permite probar localmente; `fase2_programar_diario_windows.ps1` registra ejecución diaria a las 09:15 **solo tras instalación explícita por el usuario**.

## Pendientes antes de declarar cerrada la Fase 2

1. **Ejecución real de segunda generación completa:** se necesitan en la máquina de pruebas una copia local de solo lectura del proyecto original, el `index.html` y el PDF aprobados, y un acceso seguro de **solo lectura** a la base (o un snapshot vigente autorizado). No se deben copiar claves a la rama pública.
2. **Activación real de la actualización diaria:** el código de programación está preparado, pero **no está ejecutándose** hasta instalarlo en una máquina privada conectada. Con la sesión iniciada y el equipo encendido, Windows la ejecutará a las 09:15.
3. **Verificación de ejecución automática:** constatar al menos un ciclo programado que genere ZIP y reporte, sin sobrescribir la versión aprobada, con datos actuales y sin errores.

## Ejecución privada, sin automatizar

Desde PowerShell, en el checkout de `bonvi-web` rama de desarrollo, con Python y las dependencias de `tools/generar_catalogo_integrado.py` instaladas:

```powershell
# La conexión de solo lectura debe residir en un almacén privado de credenciales
# o en la variable DATABASE_URL del entorno seguro de esta ejecución. NO PEGARLA EN GITHUB.
./tools/fase2_ejecutar_privado.ps1 `
  -StreamlitDir 'C:\ruta-local\Bonvi-Mercat\BON_VI_MERCAT_Proyecto_v7_3_ONLINE\BON_VI_MERCAT_REAL_v7_3_ONLINE' `
  -AprobadoHtml 'C:\catalogo-aprobado\index.html' `
  -AprobadoPdf 'C:\catalogo-aprobado\catalogo-personas.pdf' `
  -SalidaRaiz 'C:\BONVI-PRUEBAS-PRIVADAS'
```

## Programación diaria (solo después de superar la ejecución manual)

```powershell
./tools/fase2_programar_diario_windows.ps1 `
  -StreamlitDir 'C:\ruta-local\Bonvi-Mercat\BON_VI_MERCAT_Proyecto_v7_3_ONLINE\BON_VI_MERCAT_REAL_v7_3_ONLINE' `
  -AprobadoHtml 'C:\catalogo-aprobado\index.html' `
  -AprobadoPdf 'C:\catalogo-aprobado\catalogo-personas.pdf' `
  -SalidaRaiz 'C:\BONVI-PRUEBAS-PRIVADAS'
```

Este procedimiento **no es una publicación ni una migración a la web**. Un error de conexión, precio, duplicados o PDF detiene la entrega del ZIP.
