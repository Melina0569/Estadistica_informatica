# Seguridad y accesos

## Evidencia en el código

- No hay autenticación, sesiones, tokens ni middleware de autorización.
- `CORS(app)` permite CORS globalmente sin orígenes restringidos.
- El backend escucha explícitamente en `127.0.0.1:5000`.
- La configuración usa credenciales PostgreSQL desde `.env`.
- Los endpoints pueden crear, corregir, eliminar cargas y reiniciar la base; el código no muestra controles de rol.
- La auditoría registra `usuario` recibido por el cliente y usa `Administrador` por defecto; no constituye identidad autenticada.

## Direcciones IP y máquinas autorizadas

**Situación actual**: El sistema se encuentra en una etapa de desarrollo y está alojado localmente en el equipo de desarrollo, utilizando Flask como backend y PostgreSQL como gestor de base de datos.
**Implementación futura**: La aplicación será desplegada en un servidor institucional proporcionado por la universidad, cuya dirección OP, nombre de host y configuración de red serán definidos por Quipucamayoc.
Para identificar los equipos que tendrán acceso al sistema, se realiza un registro de sus nombres de host y direcciones IP dentro de la red institucional. Esta información va a permitir identificar las estaciones de trabajo que utilizarán la plataforma durante la implementación.


N.°	| Nombre del equipo	  | Dirección IPv4 | Máscara de subred | Puerta de enlace	| Conexión
1	| DESKTOP-U6UVBKD	  | 172.16.89.103  | 255.255.252.0	   | 172.16.88.1	    | Ethernet (Acá está alojada la información del código temporalmente)
2	| Pendiente	Pendiente |	Pendiente	   | Pendiente	       | Pendiente          |
3	| Pendiente	Pendiente |	Pendiente	   | Pendiente	       | Pendiente          |

## Medidas operativas pendientes

Restringir CORS, añadir autenticación/autorización, proteger los endpoints destructivos, usar HTTPS, rotar la contraseña expuesta históricamente en el `.env`, validar tamaño/tipo de archivos y separar configuración de desarrollo y producción.
