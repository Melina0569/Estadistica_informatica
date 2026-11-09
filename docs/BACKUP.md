# Backup binario PostgreSQL

El repositorio no incluye scripts de backup. Estas operaciones son el procedimiento operativo recomendado para el esquema que usa la aplicación y requieren que `pg_dump` y `pg_restore` estén en `PATH`.

## Generar formato Custom

El formato Custom (`-Fc`) es binario, comprimido y se restaura con `pg_restore`.

```powershell
$env:PGPASSWORD = "<contraseña-no-persistente>"
pg_dump -h localhost -p 5432 -U dataunmsm_app -d dataunmsm_dev `
  --format=custom --file=.\backups\dataunmsm_$(Get-Date -Format yyyyMMdd_HHmmss).dump
Remove-Item Env:PGPASSWORD
```

Preferir `.pgpass`/administración segura de secretos cuando esté disponible; no escribir credenciales en scripts ni en Git.

## Verificar el archivo

```powershell
pg_restore --list .\backups\dataunmsm_YYYYMMDD_HHMMSS.dump
```

## Restaurar en una base existente

Realizar la restauración con la aplicación detenida y una base destino respaldada previamente:

```powershell
$env:PGPASSWORD = "<contraseña-no-persistente>"
pg_restore -h localhost -p 5432 -U dataunmsm_app -d dataunmsm_restore `
  --clean --if-exists --no-owner --no-acl `
  .\backups\dataunmsm_YYYYMMDD_HHMMSS.dump
Remove-Item Env:PGPASSWORD
```

Si la base destino no existe, un administrador debe crearla y asignar permisos antes de ejecutar `pg_restore`. Validar después con `\dt`, una consulta de conteos y `GET /test-db`.

## Recomendaciones

- Confirmar versión de PostgreSQL y compatibilidad antes de restaurar.
- Proteger el dump: contiene datos académicos y potencialmente datos personales.
- Registrar fecha, operador, origen, destino y resultado de cada operación.
- No confundir este backup de PostgreSQL con el contenido binario de archivos Excel almacenado en `historial_cargas.archivo_contenido`.
