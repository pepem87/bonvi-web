# Fase 2 — preparar los dos secretos (sin pegarlos en el chat)

La validación sin credenciales ya finalizó correctamente en GitHub Actions (#1, 07/11/2026). El paso pendiente es una ejecución manual con `prueba_con_supabase=true`.

## 1. Acceso al código original privado

Crear un **fine-grained personal access token** en GitHub, limitado exclusivamente al repositorio privado `pepem87/Bonvi-Mercat`, permiso **Contents: Read-only** y vencimiento corto. Guardarlo como un **Actions repository secret** en `pepem87/bonvi-web`:

`BONVI_PRIVATE_REPO_READ_TOKEN`

No usar permisos de escritura ni conceder acceso a todos los repositorios. El token no debe aparecer en archivos, capturas, mensajes ni logs.

## 2. Conexión privada de solo lectura a PostgreSQL

No usar la contraseña de `postgres` ni `service_role`. Crear una cuenta dedicada, capaz de **SELECT** únicamente de `public.productos` y `public.parametros`, sin escritura, roles elevados, ni acceso a otras tablas. Por tratarse de datos comerciales, usar exclusivamente una cuenta de base de datos con privilegios acotados, protegida por una contraseña propia; no usar la clave del sistema Streamlit.

Ejemplo de autorizaciones a aplicar a un rol ya creado (revisar como administrador antes de ejecutar):

```sql
GRANT CONNECT ON DATABASE postgres TO bonvi_catalogo_lectura;
GRANT USAGE ON SCHEMA public TO bonvi_catalogo_lectura;
GRANT SELECT ON TABLE public.productos, public.parametros TO bonvi_catalogo_lectura;
ALTER ROLE bonvi_catalogo_lectura SET default_transaction_read_only = on;
```

Confirmar que el rol no hereda otros permisos, que no puede escribir y que puede leer las dos tablas. Tener presentes las políticas RLS actuales: un rol custom puede estar sujeto a ellas. No deshabilitar RLS ni abrir las tablas a `anon`.

Desde el panel Supabase > **Connect**, elegir el endpoint con conectividad IPv4 compatible con GitHub Actions (normalmente Session Pooler) y armar la cadena con el rol dedicado, contraseña con caracteres URL codificados y `sslmode=require`. En pooler compartido, el usuario debe usar el formato `bonvi_catalogo_lectura.[project-ref]`.

Almacenar la cadena completa en GitHub Actions secret:

`BONVI_CATALOG_READONLY_DATABASE_URL`

No pegar ninguna contraseña aquí. No agregar valores de secretos al repositorio.

## 3. Primera ejecución real — solo lectura

Abrir: https://github.com/pepem87/bonvi-web/actions/workflows/fase2-ejecutar-desde-main.yml

Run workflow > rama `main` > marcar **Leer Supabase y generar copia privada** > Run workflow.

Esta ejecución:
1. Toma código de la rama de desarrollo.
2. Ejecuta pruebas automatizadas.
3. Crea referencia offline aprobada desde los 1.541 registros auditados.
4. Obtiene productos actuales con consulta de solo lectura.
5. Genera HTML, fichas y PDF en carpeta temporal del runner.
6. Contrasta ambos catálogos; cualquier alerta bloquea el job.

Los archivos temporales no se publican, ni se suben como artifacts ni quedan incorporados a `main`. Los resultados se consultan en los logs. No marcar ningún estado de éxito antes de la ejecución real.

**Nota:** La ejecución de 06/11/2026 es una referencia histórica. Si cambia el catálogo, la primera sincronización puede dar `REVISAR`: no es un error de sistema, es la compuerta de seguridad prevista.
