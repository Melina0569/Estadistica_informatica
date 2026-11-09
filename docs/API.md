# API HTTP

## Convenciones

- URL base local: `http://127.0.0.1:5000`.
- JSON salvo carga de archivo y exportación.
- Errores habituales: `400` entrada inválida, `404` recurso inexistente o no encontrado, `409` operación no disponible o conflicto y `500` error interno.
- Respuestas exitosas: `200` solicitud exitosa y `201` recurso creado.
- Las respuestas de exportación son archivos Excel, no JSON.

## Endpoints relacionados con el funcionamiento del backend y la gestión de estudiantes

| Método y URL | Parámetros / cuerpo | Resultado |
|---|---|---|
| `GET /` | — | Texto `Backend funcionando correctamente`. |
| `GET /test-db` | — | Texto donde indica si la conexión funciona o no, dando un mensaje de éxito o de error. |
| `GET /estudiantes` | `page`, `per_page` opcionales | Lista serializada; con paginación devuelve `total`, `page`, `per_page`, `pages`, `estudiantes`. |
| `GET /estudiantes/{id_codigo_alumno}` | Código en URL | Estudiante con `ingresos`, `matriculas` e `información personal`; `404` si no existe. |
| `GET /estudiantes/dni/{num_dni}` | DNI en URL | Lista de estudiantes o `404`. |
| `GET /estudiantes/{id_codigo_alumno}/matriculas` | Código en URL | Lista de matrículas. |
| `GET /consultas/estudiantes` | `page`, `per_page` (máx. 100), `q`, `periodo`, `programa`, `facultad`, `estado_matricula`, `condicion`, `carga` | Resultado paginado con estudiantes resumidos. |
| `GET /consultas/opciones` | — | Opciones de facultad, programa, carrera, periodos y ciclos. |
| `POST /estudiantes` | JSON de campos obligatorios de estudiante | Estudiante creado (`201`). |
| `PUT /estudiantes/{id_codigo_alumno}` | JSON completo editable | Estudiante actualizado. |
| `PATCH /estudiantes/{id_codigo_alumno}` | JSON parcial | Campos presentes actualizados. |

### Requests y responses JSON

Los `GET` no reciben un cuerpo JSON; en esos casos se muestra la consulta como objeto JSON equivalente a sus parámetros. Los valores son ilustrativos y no representan datos reales.

`GET /` y `GET /test-db` devuelven texto plano, no JSON:

```text
Backend funcionando correctamente
Conexión a PostgreSQL exitosa
```

`GET /estudiantes?page=1&per_page=20`

```json
// Request: parámetros de consulta
{"page": 1, "per_page": 20}
```

```json
// Response 200
{
  "total": 1,
  "page": 1,
  "per_page": 20,
  "pages": 1,
  "estudiantes": [
    {
      "id_codigo_alumno": "00000001",
      "tipo_doc_id": "DNI",
      "num_dni": "<no incluir>",
      "apellido_pat": "APELLIDO",
      "apellido_mat": "MATERNO",
      "nombres": "Nombre",
      "sexo": "F",
      "fecha_nac": "2000-01-01",
      "nacionalidad": null,
      "estado_civil": null,
      "correo_inst": null,
      "correo_per": null,
      "distrito_domicilio": "Distrito",
      "identi_etnica": null,
      "lengua_nativa": null,
      "idioma_extranjero": null,
      "telefono_fijo": null,
      "telefono_movil": null,
      "beca": null,
      "colegio": null,
      "discapacidad": null,
      "movilidad": null,
      "ubigeo": null,
      "ingresos": []
    }
  ]
}
```

Sin `page` y `per_page`, el response 200 es directamente el arreglo de estudiantes serializados: `[{...}]`.

`GET /estudiantes/{id_codigo_alumno}` y `GET /estudiantes/dni/{num_dni}`:

```json
// Request: GET /estudiantes/00000001
{"id_codigo_alumno": "00000001"}
```

```json
// Response 200 de /estudiantes/{id_codigo_alumno}
{"id_codigo_alumno":"00000001","nombres":"Nombre","ingresos":[]}
```

```json
// Response 404
{"error":"Estudiante no encontrado"}
```

Para `/estudiantes/dni/{num_dni}`, el response 200 es un arreglo con el mismo formato: `[{"id_codigo_alumno":"00000001","nombres":"Nombre","ingresos":[]}]`.

`GET /estudiantes/{id_codigo_alumno}/matriculas`:

```json
// Request
{"id_codigo_alumno":"00000001"}
```

```json
// Response 200
[{
  "id_matricula": 10,
  "nivel": "PREGRADO",
  "modalidad_estudio": "REGULAR",
  "periodo_mat": "2024-1",
  "regimen_matricula": "R",
  "ciclo": 2,
  "permanencia": "ACTIVO",
  "primer_mat": "2023-1",
  "creditos_acum_sem": 20,
  "creditos_acum_total": 40,
  "cursos_mat_cat": 5,
  "promedio_pond": 15.5,
  "ranking": 10,
  "id_ingreso": 20
}]
```

`GET /consultas/estudiantes?page=1&per_page=20&q=2024`:

```http
GET /consultas/estudiantes?page=1&per_page=20&q=2024
```

```json
// Request: parámetros de consulta
{"page":1,"per_page":20,"q":"2024","periodo":"","programa":"",
 "facultad":"","estado_matricula":"","condicion":""}
```

```json
// Response 200
{
  "total": 1,
  "page": 1,
  "per_page": 20,
  "pages": 1,
  "carga": null,
  "estudiantes": [{
    "id_codigo_alumno": "00000001",
    "num_dni": "<no incluir>",
    "nombre_completo": "APELLIDO MATERNO Nombre",
    "sexo": "F",
    "correo_inst": null,
    "telefono_movil": null
  }]
}
```

`GET /consultas/opciones` no recibe cuerpo:

```json
// Response 200 (estructura)
{
  "modulos": {
    "estudiantes": 1,
    "docentes": 0,
    "administrativos": 0,
    "egresados_titulados": 0
  },
  "facultades": [{"valor":"F1","texto":"Facultad ejemplo"}],
  "programas": [{"valor":"Programa||Facultad ejemplo","texto":"Programa — Facultad ejemplo","facultad":"Facultad ejemplo"}],
  "carreras": [{"valor":"Carrera||Programa||Facultad ejemplo","texto":"Carrera — Programa","programa":"Programa||Facultad ejemplo","facultad":"Facultad ejemplo"}],
  "generos": [{"valor":"F","texto":"F"}],
  "becas": [{"valor":"Beca ejemplo","texto":"Beca ejemplo"}],
  "periodos": [{"valor":"2024-1","texto":"2024-1"}],
  "estados_matricula": [{"valor":"REGULAR","texto":"REGULAR"}],
  "condiciones": [{"valor":"ACTIVO","texto":"ACTIVO"}],
  "niveles": [{"valor":"PREGRADO","texto":"PREGRADO"}],
  "ciclos": [{"valor":2,"texto":"2"}]
}
```

`POST /estudiantes`:

```json
// Request
{
  "id_codigo_alumno":"00000001",
  "tipo_doc_id":"DNI",
  "num_dni":"<no incluir>",
  "apellido_pat":"APELLIDO",
  "apellido_mat":"MATERNO",
  "nombres":"Nombre",
  "sexo":"F",
  "fecha_nac":"2000-01-01",
  "estado_civil":"S",
  "correo_inst":"alumno@ejemplo.edu",
  "correo_per":null,
  "distrito_domicilio":"Distrito",
  "identi_etnica":null,
  "telefono_fijo":null,
  "telefono_movil":null
}
```

```json
// Response 201: estudiante serializado
{"id_codigo_alumno":"00000001","nombres":"Nombre","ingresos":[]}
```

```json
// Response 400
{"error":"Falta el campo obligatorio: nombres"}
```

`PUT /estudiantes/{id_codigo_alumno}` recibe el mismo conjunto completo de campos editables del ejemplo anterior y devuelve `200` con el estudiante serializado. `PATCH /estudiantes/{id_codigo_alumno}` recibe uno o más de esos campos:

```json
// Request PATCH
{"correo_inst":"nuevo@ejemplo.edu","telefono_movil":"999999999"}
```

```json
// Response 200
{"id_codigo_alumno":"00000001","correo_inst":"nuevo@ejemplo.edu","telefono_movil":"999999999","ingresos":[]}
```

Para ambos endpoints, los errores de recurso inexistente o cuerpo vacío son:

```json
{"error":"Estudiante no encontrado"}
{"error":"No se enviaron datos"}
```

## Cargas

| Método y URL | Entrada | Salida |
|---|---|---|
| `POST /estudiantes/cargar-excel` | `multipart/form-data`, campo `archivo`, `.xlsx` o `.xls` | Reporte de calidad, vista previa, inconsistencias e `id_carga`; no persiste filas finales. |
| `POST /estudiantes/confirmar-carga` | Sin cuerpo | Persiste la carga analizada o devuelve `409` si no existe una carga pendiente. Se puede identificar la carga cuando la barra de espera esté al 100%. |
| `GET /api/cargas` | `limite` entero positivo | Lista de historial. |
| `DELETE /api/cargas/{id_carga}` | ID en URL | Revierte/elimina una carga o devuelve conflicto. |
| `POST /api/base-datos/reiniciar` | Sin cuerpo | Trunca tablas configuradas y devuelve estado `Reiniciada`. Toda la data registrada en PostgreSQL se elimina definitivamente.|

Ejemplo de carga:

```bash
curl -F "archivo=@estudiantes.xlsx" http://127.0.0.1:5000/estudiantes/cargar-excel
```

`POST /estudiantes/cargar-excel` no recibe JSON: recibe `multipart/form-data` con el campo `archivo`. Response 200:

```json
{
  "estado":"APTO",
  "archivo":"estudiantes.xlsx",
  "total_filas":1,
  "total_inconsistencias":0,
  "inconsistencias":[],
  "resumen_inconsistencias":[],
  "vista_previa":[],
  "correcciones_automaticas":[],
  "id_carga":1,
  "siguiente_paso":"El archivo está apto para continuar con la validación final y posterior carga."
}
```

Errores de carga:

```json
{"estado":"ERROR","error":"No se recibió ningún archivo."}
{"estado":"ERROR","error":"El archivo debe tener formato Excel (.xlsx o .xls)."}
```

`POST /estudiantes/confirmar-carga` no recibe cuerpo:

```json
// Response 201
{
  "estado":"EXITOSO",
  "mensaje":"Los datos se cargaron correctamente en PostgreSQL.",
  "archivo":"estudiantes.xlsx",
  "filas_procesadas":100,
  "correcciones_automaticas":[],
  "total_correcciones":0
}
```

```json
// Response 409
{"estado":"ERROR","error":"No hay una carga analizada pendiente de confirmación."}
```

`GET /api/cargas?limite=10`:

```json
// Request: {"limite":10}
// Response 200
[{
  "id":1,
  "nombre":"estudiantes.xlsx",
  "tamano":null,
  "registros":100,
  "tipo":"Estudiantes",
  "dependencia":null,
  "subidoPor":null,
  "cargo":"06/11/2026",
  "hora":"12:00",
  "estado":"Apta",
  "registrosProcesados":100,
  "inconsistencias":0,
  "observaciones":null
}]
```

`DELETE /api/cargas/{id_carga}` devuelve un objeto de operación:

```json
// Response 200
{"estado":"Eliminado","id":1,"advertencias":[]}
```

```json
// Response 404/409
{"error":"La carga no existe."}
{"error":"La carga ya fue eliminada."}
```

`POST /api/base-datos/reiniciar`:

```json
// Request: {}
// Response 200
{"estado":"Reiniciada","mensaje":"La base de datos fue reiniciada correctamente."}
```

## Dashboard e indicadores

| Método y URL | Parámetros | Resultado |
|---|---|---|
| `GET /api/dashboard/resumen` | — | Periodos, archivos del día, validados, observaciones, procesados e inconsistencias. |
| `GET /api/indicadores/resumen` | `facultad`, `periodo` | KPIs y distribuciones por facultad, periodo y beca. |
| `GET /api/indicadores/tabla` | `tipo`, `dimension`, `metrica`, filtros de indicadores, `columnas` para detalle | Filas agregadas o detalle. Dimensiones: `facultad`, `programa`, `carrera`, `genero`, `beca`, `periodo`; métricas: `total`, `participacion`. |
| `GET /api/indicadores/exportar` | Los mismos filtros | Descarga `.xlsx`; `tipo=detalle` permite columnas válidas del código. |

Ejemplo:

```json
{"dimension":"facultad","metrica":"total","total":10,
 "filas":[{"nombre":"Facultad ejemplo","total":10,"participacion":100.0}]}
```

`GET /api/dashboard/resumen`:

```json
// Response 200
{
  "periodo":"2026-2",
  "periodoSiguiente":"2027-1",
  "archivosHoy":1,
  "validados":1,
  "conObservaciones":0,
  "registrosProcesados":100,
  "inconsistencias":0
}
```

`GET /api/indicadores/resumen?facultad=Facultad%20ejemplo&periodo=2024-1`:

```json
// Request: {"facultad":"Facultad ejemplo","periodo":"2024-1"}
// Response 200
{
  "modulos":{"estudiantes":100,"docentes":0,"administrativos":0,"egresados_titulados":0},
  "kpis":{"estudiantes":20,"programas":3,"matriculas":40,"facultades":1},
  "por_facultad":[{"nombre":"Facultad ejemplo","total":20}],
  "por_periodo":[{"nombre":"2024-1","total":20}],
  "por_beca":[{"nombre":"Sin beca","total":20}]
}
```

`GET /api/indicadores/tabla?dimension=facultad&metrica=total`:

```json
// Request: {"tipo":"resumen","dimension":"facultad","metrica":"total"}
// Response 200
{"dimension":"facultad","metrica":"total","total":20,
 "filas":[{"nombre":"Facultad ejemplo","total":20,"participacion":100.0}]}
```

Con `tipo=detalle`, el response incluye las columnas y filas solicitadas:

```json
{"tipo":"detalle","total":1,"columnas":["Código de estudiante","Nombres"],
 "filas":[{"Código de estudiante":"00000001","Nombres":"Nombre"}]}
```

`GET /api/indicadores/exportar` no devuelve JSON en caso exitoso: devuelve un archivo Excel con `Content-Disposition`. Los errores sí son JSON:

```json
{"error":"Parámetros de exportación inválidos."}
```

## Correcciones y documentos

| Método y URL | Entrada | Resultado |
|---|---|---|
| `GET /api/correcciones/reporte-activo` | — | Reporte activo o `{"reporte":null,"id_carga":null}`. |
| `GET /api/correcciones/inconsistencias` | `limite` 1..500 | Grupos y totales de inconsistencias. |
| `POST /api/correcciones/reporte-validacion` | JSON `{archivo, reporte}` | Guarda reporte. |
| `PUT /api/correcciones/reporte-validacion/correccion` | `{campo, valor, motivo}` | Registra corrección pendiente y auditoría. |
| `GET /api/correcciones/inconsistencias/detalle` | `tabla`, `campo` | Registros afectados. |
| `PUT /api/correcciones/registro` | `{tabla,campo,id,valor,motivo,usuario?}` | Corrige un registro y audita. |
| `PUT /api/correcciones/registros` | `{correcciones:[], valor_comun?, motivo, usuario?}` | Corrige varios registros y audita. |
| `GET /api/correcciones/auditoria` | `pagina` | Auditoría paginada de 10 elementos. |
| `GET /api/correcciones/documentos` | — | Hasta 300 documentos pendientes. |
| `POST /api/correcciones/documentos` | `tipo_documento` obligatorio; `codigo_alumno`, `descripcion`, `responsable`, `fecha_limite` opcionales | Crea documento (`201`). |
| `PATCH /api/correcciones/documentos/{id_documento}` | `estado`, `responsable`, `descripcion` | Actualiza documento. Estados aceptados: `Pendiente`, `En revisión`, `Completado`. |

Ejemplo de corrección:

```json
{"tabla":"estudiante","campo":"nombres","id":"00000001",
 "valor":"Nombre corregido","motivo":"Corrección documentada",
 "usuario":"Administrador"}
```

`GET /api/correcciones/reporte-activo`:

```json
// Response 200 sin reporte
{"reporte":null,"id_carga":null}
```

Con reporte:

```json
{"id_carga":1,"archivo":"estudiantes.xlsx",
 "reporte":{"estado":"APTO","total_filas":100,
 "total_inconsistencias":0,"resumen_inconsistencias":[],"id_carga":1}}
```

`GET /api/correcciones/inconsistencias?limite=100`:

```json
// Request: {"limite":100}
// Response 200
{"total":1,"tipos":1,
 "inconsistencias":[{
   "clave":"archivo:0","tabla":"archivo","campo":"nombres",
   "etiqueta":"nombres","severidad":"CRÍTICO","cantidad":1,
   "muestra":[],"origen":"archivo","archivo":"estudiantes.xlsx",
   "detalle_disponible":true,"id_carga":1
 }],
 "reportes":[{"archivo":"estudiantes.xlsx","total_filas":100,
 "total_inconsistencias":1,"creado_en":"2026-11-06T12:00:00",
 "id_carga":1,"estado":"en_correccion"}],
 "id_carga":1}
```

`POST /api/correcciones/reporte-validacion`:

```json
// Request
{"archivo":"estudiantes.xlsx",
 "reporte":{"estado":"NO_APTO","total_filas":100,
 "total_inconsistencias":1,
 "resumen_inconsistencias":[
   {"campo":"nombres","tipo":"CRÍTICO","cantidad":1}
 ]}}
```

```json
// Response 200
{"mensaje":"Reporte de validación actualizado."}
```

`PUT /api/correcciones/reporte-validacion/correccion`:

```json
// Response 200
{"mensaje":"Corrección pendiente guardada para el archivo.",
 "id_carga":1,"total_inconsistencias":0,"estado":"apta"}
```

`GET /api/correcciones/inconsistencias/detalle?tabla=estudiante&campo=nombres`:

```json
// Request: {"tabla":"estudiante","campo":"nombres"}
// Response 200
{"registros":[{"tabla":"estudiante","id":"00000001","campo":"nombres"}]}
```

`PUT /api/correcciones/registro`:

```json
// Response 200
{"mensaje":"Corrección guardada y auditada."}
```

```json
// Response 400
{"error":"Tabla, campo, id y motivo son obligatorios."}
```

`PUT /api/correcciones/registros`:

```json
// Request
{"correcciones":[
  {"tabla":"estudiante","campo":"nombres","id":"00000001","valor":"Nombre"}
],"motivo":"Corrección masiva","usuario":"Administrador"}
```

```json
// Response 200
{"mensaje":"1 corrección(es) guardada(s) y auditada(s)."}
```

`GET /api/correcciones/auditoria?pagina=1`:

```json
// Request: {"pagina":1}
// Response 200
{"auditoria":[{
  "id":1,"tabla":"estudiante","id_registro":"00000001",
  "campo":"nombres","anterior":"Nombre anterior","nuevo":"Nombre",
  "motivo":"Corrección documentada","usuario":"Administrador",
  "creado_en":"2026-11-06T12:00:00"
 }],"pagina":1,"por_pagina":10,"total":1,"paginas":1}
```

`GET /api/correcciones/documentos`:

```json
// Response 200
{"documentos":[{
  "id":1,"codigo_alumno":"00000001",
  "tipo_documento":"DNI","descripcion":"Copia pendiente",
  "responsable":"Oficina","estado":"Pendiente",
  "fecha_limite":"2026-12-01"
}]}
```

`POST /api/correcciones/documentos`:

```json
// Request
{"codigo_alumno":"00000001","tipo_documento":"DNI",
 "descripcion":"Copia pendiente","responsable":"Oficina",
 "fecha_limite":"2026-12-01"}
```

```json
// Response 201
{"id":1,"mensaje":"Documento pendiente registrado."}
```

`PATCH /api/correcciones/documentos/{id_documento}`:

```json
// Request
{"estado":"Completado","responsable":"Oficina","descripcion":"Recibido"}
```

```json
// Response 200
{"mensaje":"Documento actualizado."}
```

> Los campos aceptados para corrección están restringidos por `MODELOS_CORREGIBLES` en el código. No se documentan endpoints de otros archivos de rutas porque no están registrados en `app.py`.
