# Configuración

## Variables de entorno

`backend/config.py` usa `python-dotenv` para cargar `.env` y construye `postgresql+psycopg2://...`.

| Variable | Uso | Ejemplo no confidencial |
|---|---|---|
| `DB_HOST` | Host PostgreSQL | `localhost` |
| `DB_PORT` | Puerto PostgreSQL | `5432` |
| `DB_NAME` | Nombre de base de datos | `dataunmsm_dev` |
| `DB_USER` | Usuario de conexión | `dataunmsm_app` |
| `DB_PASSWORD` | Contraseña de conexión | `<definir-en-secreto>` |

El archivo existente contiene una contraseña real de desarrollo; no se reproduce aquí. Debe rotarse si fue compartida o publicada y el `.env` debe permanecer fuera del control de versiones.

## Configuración de frontend

`frontend/js/api.js` fija:

```js
BASE_URL: "http://127.0.0.1:5000"
```

Para otro entorno debe cambiarse ese valor en el frontend. No se encontró una variable de entorno frontend ni un archivo de despliegue que lo parametrice.

## Inicialización

`app.py` ejecuta `db.create_all()` y agrega, si no existen, columnas de correcciones, huella de archivo, contenido binario, `id_carga` y estado en tablas existentes. Es una operación de arranque, no una migración versionada.

## Pendientes de verificación

- Versión soportada de Python y PostgreSQL.
- Parámetros de pool, SSL y timeouts de PostgreSQL.
- Orígenes CORS permitidos en producción.
- Forma oficial de servir el frontend y URL por ambiente.
