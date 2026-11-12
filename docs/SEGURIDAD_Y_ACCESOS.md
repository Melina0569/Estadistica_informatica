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


N.°	| Nombre del equipo	  | Dirección IPv4 | Dirección IPv6 local          | Máscara de subred | Puerta de enlace | Conexión
1	| DESKTOP-U6UVBKD	  | 172.16.89.103  | fe80::1b82:50aa:89ca:edbe%10  | 255.255.252.0	   | 172.16.88.1	  | Ethernet (Acá está alojada la información del código)
2	| OGP-EEI-11          |	172.16.89.94   | fe80::5f72:e010:87f5:b654%13  | 255.255.252.0	   | 172.16.88.1      | Ethernet
3	| DESKTOP-LGKUV7L     |	172.16.89.121  | fe80::ddbf:a2af:ef68:514c%17  | 255.255.252.0	   | 172.16.88.1      | Ethernet
4	| OGP-EEI-06          |	172.16.89.85   | fe80::3b94:4915:41e8:b93c%9   | 255.255.252.0	   | 172.16.88.1      | Ethernet
5	| OGP-EEI-10          | 172.16.89.86   | fe80::4b35:7a5e:b5ed:e72c%3   | 255.255.252.0	   | 172.16.88.1      | Ethernet
6	| LAPTOP-IUCLUM9P     | 192.168.1.33   | fe80::17e8:978f:1b3b:b1f6%18  | 255.255.255.0	   | 192.168.1.1      | Ethernet
7	| LAPTOP-U87BQTM1     | 192.168.68.50  | fe80::c0a5:9324:be46:3ac7%2   | 255.255.252.0     | 192.168.68.1     | Ethernet
8	| LAPTOP-2FUMSRRO     | 192.168.18.24  | --                            | --          	   | --               | Ethernet
9	| --                  | --             | --                            | --          	   | --               | Ethernet

## Medidas operativas pendientes

Restringir CORS, añadir autenticación/autorización, proteger los endpoints destructivos, usar HTTPS, rotar la contraseña expuesta históricamente en el `.env`, validar tamaño/tipo de archivos y separar configuración de desarrollo y producción.
