# Manual de usuario

## Acceso

1. Iniciar PostgreSQL con una base configurada según [`CONFIGURACION.md`](CONFIGURACION.md).
2. Iniciar Flask desde `backend`.
3. Servir la raíz del proyecto mediante un servidor HTTP estático.
4. Abrir la página inicial del frontend.

No existe login implementado en el código, por lo que el acceso actual no distingue perfiles.

## Flujo de carga

1. Abrir el módulo de carga.
2. Seleccionar un archivo `.xlsx` o `.xls`.
3. Ejecutar el análisis. El sistema valida columnas, limpia datos, calcula inconsistencias y muestra vista previa.
4. Corregir las inconsistencias desde el módulo de correcciones, indicando valor y motivo.
5. Confirmar la carga cuando el reporte esté apto.
6. Revisar el historial de cargas y el resultado en el dashboard.

El análisis inicial no inserta las filas finales; `POST /estudiantes/confirmar-carga` es el paso de confirmación.

## Consultas

En Consultas se puede buscar por texto, periodo, programa, facultad, estado/modalidad de matrícula, condición y carga. Los resultados son paginados. El detalle de un estudiante muestra datos personales, ingresos y matrículas.

## Indicadores

El módulo permite filtrar por facultad, periodo y otras dimensiones soportadas por la API, consultar tablas agregadas o detalle y exportar un archivo Excel.

## Correcciones y documentos

1. Seleccionar una inconsistencia.
2. Consultar el detalle de registros.
3. Introducir el nuevo valor y un motivo.
4. Guardar; el sistema registra una entrada de auditoría.
5. Registrar documentos pendientes cuando falte documentación y actualizar su estado.

## Operaciones administrativas

El historial permite consultar cargas y solicitar eliminación/reversión. `POST /api/base-datos/reiniciar` elimina datos mediante `TRUNCATE ... CASCADE`; debe considerarse una operación destructiva y no ejecutarse sin un backup y autorización operativa.

## Limitaciones verificadas

- No hay autenticación ni recuperación de contraseña.
- No hay mensajes o flujos documentados para docentes, egresados, titulados y administrativos en la aplicación registrada.
- La URL del frontend/backend es local y debe configurarse para un entorno real.
