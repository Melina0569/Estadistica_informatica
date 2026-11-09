# Seguridad y accesos

## Evidencia en el código

- No hay autenticación, sesiones, tokens ni middleware de autorización.
- `CORS(app)` permite CORS globalmente sin orígenes restringidos.
- El backend escucha explícitamente en `127.0.0.1:5000`.
- La configuración usa credenciales PostgreSQL desde `.env`.
- Los endpoints pueden crear, corregir, eliminar cargas y reiniciar la base; el código no muestra controles de rol.
- La auditoría registra `usuario` recibido por el cliente y usa `Administrador` por defecto; no constituye identidad autenticada.

## Direcciones IP y máquinas autorizadas

| Recurso | Dirección observada | Estado |
|---|---|---|
| Servidor Flask | `127.0.0.1` | Verificada en `app.py`; solo loopback |
| PostgreSQL local | `localhost` | Verificada como valor de desarrollo en `.env`; resuelve a IP pendiente |
| Clientes autorizados | — | **Pendiente de verificar: no hay allowlist ni inventario de IPs en el código** |
| Servidores de producción | — | **Pendiente de verificar** |

No es posible afirmar qué máquinas están autorizadas únicamente con este repositorio.

## Medidas operativas pendientes

Restringir CORS, añadir autenticación/autorización, proteger los endpoints destructivos, usar HTTPS, rotar la contraseña expuesta históricamente en el `.env`, validar tamaño/tipo de archivos y separar configuración de desarrollo y producción.
