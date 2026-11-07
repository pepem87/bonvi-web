# Fase 2 — CERRADA EN DESARROLLO (07/11/2026)

**Estado:** pruebas controladas completadas y aprobadas como hito de desarrollo. La automatización diaria privada quedó **habilitada en ChatGPT**; su primera ejecución por horario (08/11/2026 09:15, Argentina) **aún no está verificada** al momento de este cierre. Esta observación se registra como seguimiento operativo, sin afirmar que ya haya corrido.

## Alcance inalterable

- Únicamente catálogo privado independiente, sin publicar ni migrar a `bonvimercat.com.ar`.
- `pepem87/bonvi-web/main` intacto; el trabajo de código está en `desarrollo/catalogo-seo-l7`.
- Sistema interno `pepem87/Bonvi-Mercat`, Streamlit, pedidos, precios y tablas de Supabase sin modificaciones por estas pruebas.
- El catálogo público de Streamlit sigue activo hasta que la web nueva esté publicada, validada y autorizada en Fases 4/5.
- No usar en publicidad ni ventas los precios de la simulación.

## Evidencias y pruebas efectuadas

1. **Referencia original aprobada.** ZIP completo de Fase 1, 1.541 fichas, índice y PDF de 44 páginas. Verificación de estructura y recursos gráficos, búsqueda, filtros, ocho categorías, paginación y visualización móvil.
2. **Datos vigentes.** Consultas de solo lectura a Supabase, 1.541 productos coincidentes, cero diferencias frente a referencia. Vigencia de catálogo observada: `2026-11-06T16:12:55.260294Z`.
3. **PDF y precios.** 1.541 códigos y 3.082 precios (unitario y venta) verificados en el PDF, sin diferencias.
4. **Segunda copia privada.** Se produjo ZIP de segunda generación con 1.541 fichas y PDF de 44 páginas; paquete comprobado sin publicar. Conservar también la versión original.
5. **Prueba de cambio SIMULADO.** Código 2063: precio unitario de prueba $3.950 a $4.050; bulto de seis de $23.700 a $24.300. Ficha y PDF reflejaron el cambio; los otros 1.540 productos permanecieron sin cambios; Supabase no se escribió.
6. **Pruebas automatizadas de código.** GitHub Actions de validación en rama de desarrollo completó con SUCCESS; no es despliegue.
7. **Almacenamiento privado.** Archivos en Biblioteca personal de ChatGPT: `/BON VI MERCAT/Catalogo privado/` (ZIP aprobado, ZIP de segunda copia, script del generador). No incluir claves ni nuevos ZIP en GitHub público.
8. **Tarea automática.** `Sincronizar catálogo BON VI privado` configurada y habilitada para todos los días a las 09:15 (Argentina) desde 08/11/2026. La ejecución manual inmediata revisó Supabase y no encontró cambios, por lo que no correspondió generar ZIP adicional.

## Control de seguimiento, no cumplimiento ya afirmado

- **PENDIENTE DE COMPROBAR:** resultado de la primera ejecución **programada** del 08/11/2026 09:15, si tuvo acceso a Supabase y Biblioteca y si respetó la política de no publicar.
- Si la tarea falla o no dispone de entorno, informarlo y corregir antes de considerar validada la operación diaria.
- La tarea de ChatGPT no es equivalente al programador opcional de Windows documentado más abajo, que permanece **sin instalar**.

## Próxima fase

Fase 3: preparar SEO, páginas indexables, slugs/canonicals y sitemap **únicamente en desarrollo**, sin subir a `main` y sin publicar en el dominio. Mantener `noindex` para cualquier vista privada hasta autorización de migración.

---

## Herramientas locales opcionales (no instaladas)
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
