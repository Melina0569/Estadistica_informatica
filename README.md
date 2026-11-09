# DATAUNMSM

Sistema web para carga, validación, consulta y visualización de información académica y administrativa. El backend está implementado con Flask y SQLAlchemy sobre PostgreSQL; el frontend es un conjunto de páginas HTML, hojas CSS y módulos JavaScript que consumen la API HTTP.

> **Alcance de esta documentación.** Está basada en el código presente en este repositorio. Cuando el código no permite verificar una versión, una dirección IP, una política operativa o una funcionalidad, se indica como pendiente; no se asume información externa.

## Repositorio

- GitHub: [Melina0569/Estadistica_informatica](https://github.com/Melina0569/Estadistica_informatica)
- Remoto configurado: `https://github.com/Melina0569/Estadistica_informatica.git`

## Tecnologías

| Capa | Tecnología | Versión verificable |
|---|---|---|
| Backend | Python | Pendiente: no está fijada en el repositorio |
| Backend | Flask | `3.1.3` |
| ORM | Flask-SQLAlchemy | `3.1.1` |
| ORM | SQLAlchemy | `2.0.53` |
| Driver | psycopg2-binary | `2.9.13` |
| Configuración | python-dotenv | `1.2.3` |
| Backend | Flask-CORS | Usado en código; no aparece fijado en `requirements.txt` |
| Frontend | HTML, CSS, JavaScript | Sin versión declarada |
| UI | Tailwind CSS por CDN | Versión no fijada en las páginas |
| UI | Material Symbols y Google Fonts por CDN | Versiones no declaradas |
| Base de datos | PostgreSQL | Versión pendiente de verificar |

Las versiones completas de los paquetes Python están en [`backend/requirements.txt`](backend/requirements.txt). La versión exacta de Python, PostgreSQL, Tailwind y los navegadores no está declarada.

## Requisitos

- Python compatible con las dependencias; versión mínima/máxima pendiente de definir.
- PostgreSQL y las utilidades `pg_dump`/`pg_restore` para las operaciones de respaldo.
- Navegador web moderno.
- PowerShell o una terminal equivalente.

## Instalación

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Crear `backend/.env` a partir de las variables descritas en [`docs/CONFIGURACION.md`](docs/CONFIGURACION.md). No publicar contraseñas ni el archivo `.env`.

## Ejecución

```powershell
cd backend
python app.py
```

El backend escucha en `http://127.0.0.1:5000`. El frontend no es servido por Flask en el código actual; debe publicarse con un servidor HTTP estático o abrirse mediante el mecanismo de desarrollo elegido. Las páginas usan rutas `/frontend/...`, por lo que conviene servir la raíz del repositorio.

Al iniciar, `app.py` ejecuta `db.create_all()` y aplica varias ampliaciones `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`. En producción se recomienda revisar ese comportamiento antes de usarlo como mecanismo de migración.

## Documentación

- [Arquitectura](docs/ARQUITECTURA.md)
- [Configuración](docs/CONFIGURACION.md)
- [API](docs/API.md)
- [Base de datos](docs/BASE_DATOS.md)
- [Backup PostgreSQL](docs/BACKUP.md)
- [Seguridad y accesos](docs/SEGURIDAD_Y_ACCESOS.md)
- [Manual de usuario](docs/MANUAL_USUARIO.md)

## Estado funcional observado

El código implementa carga y análisis de Excel, consultas y detalle de estudiantes, indicadores, historial de cargas, correcciones auditadas y documentos pendientes. Los blueprints registrados por `backend/app.py` son estudiantes, dashboard y correcciones. Los archivos de rutas de docentes, egresados, titulados y administrativos no están registrados y no exponen endpoints activos desde esta aplicación.
