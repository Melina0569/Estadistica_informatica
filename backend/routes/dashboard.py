from datetime import date, datetime
from decimal import Decimal
from io import BytesIO
import traceback

import pandas as pd
from flask import Blueprint, jsonify, request, send_file
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
from sqlalchemy import func, or_, text

from extensions import db
from models.historial_cargas import HistorialCarga, HistorialCargaCambio
from models.estudiantes import (
    Beca,
    Colegio,
    Discapacidad,
    Especialidad,
    Estudiante,
    Facultad,
    Ingreso,
    Local,
    Matricula,
    Movilidad,
    Programa,
    Sede,
    Ubigeo,
)


dashboard_bp = Blueprint(
    "dashboard",
    __name__,
    url_prefix="/api"
)


def _periodo_academico_actual(fecha=None):
    fecha = fecha or date.today()
    semestre = 1 if fecha.month <= 6 else 2
    return f"{fecha.year}-{semestre}"


def _periodo_academico_siguiente(periodo):
    anio, semestre = (int(valor) for valor in periodo.split("-"))
    if semestre == 1:
        return f"{anio}-2"
    return f"{anio + 1}-1"


MODELOS_REVERSIBLES = {
    Beca.__tablename__: Beca,
    Colegio.__tablename__: Colegio,
    Discapacidad.__tablename__: Discapacidad,
    Especialidad.__tablename__: Especialidad,
    Estudiante.__tablename__: Estudiante,
    Facultad.__tablename__: Facultad,
    Ingreso.__tablename__: Ingreso,
    Local.__tablename__: Local,
    Matricula.__tablename__: Matricula,
    Movilidad.__tablename__: Movilidad,
    Programa.__tablename__: Programa,
    Sede.__tablename__: Sede,
    Ubigeo.__tablename__: Ubigeo,
}

# Las filas hijas deben eliminarse antes que las filas referenciadas.
ORDEN_ELIMINACION = (
    Matricula,
    Ingreso,
    Estudiante,
    Especialidad,
    Programa,
    Local,
    Facultad,
    Sede,
    Colegio,
    Movilidad,
    Discapacidad,
    Ubigeo,
    Beca,
)

DIMENSIONES_INDICADORES = {
    "facultad": Facultad.nomb_facultad,
    "programa": Programa.nombre_prog,
    "carrera": func.trim(Especialidad.nomb_especialidad),
    "genero": Estudiante.sexo,
    "beca": Beca.nomb_beca,
    "periodo": Ingreso.periodo_ingreso,
}

COLUMNAS_REPORTE = {
    "codigo": ("Código de estudiante", Estudiante.id_codigo_alumno),
    "dni": ("DNI", Estudiante.num_dni),
    "apellidos": (
        "Apellidos",
        func.concat(
            func.coalesce(Estudiante.apellido_pat, ""),
            " ",
            func.coalesce(Estudiante.apellido_mat, ""),
        ),
    ),
    "nombres": ("Nombres", Estudiante.nombres),
    "genero": ("Género", Estudiante.sexo),
    "facultad": ("Facultad", Facultad.nomb_facultad),
    "programa": ("Programa", Programa.nombre_prog),
    "carrera": ("Carrera / especialidad", Especialidad.nomb_especialidad),
    "periodo": ("Periodo de ingreso", Ingreso.periodo_ingreso),
    "beca": ("Beca", Beca.nomb_beca),
    "modalidad_ingreso": ("Modalidad de ingreso", Ingreso.modalidad_ingreso),
    "modalidad_estudio": ("Modalidad de estudio", Matricula.modalidad_estudio),
    "nivel": ("Nivel", Matricula.nivel),
    "ciclo": ("Ciclo", Matricula.ciclo),
    "periodo_matricula": ("Periodo de matrícula", Matricula.periodo_mat),
    "permanencia": ("Permanencia", Matricula.permanencia),
    "promedio": ("Promedio ponderado", Matricula.promedio_pond),
    "ranking": ("Ranking", Matricula.ranking),
}


def _consulta_indicadores(filtros):
    consulta = (
        db.session.query(
            Estudiante.id_codigo_alumno,
            Estudiante.sexo,
            Facultad.nomb_facultad.label("facultad"),
            Programa.nombre_prog.label("programa"),
            Especialidad.nomb_especialidad.label("carrera"),
            Beca.nomb_beca.label("beca"),
            Ingreso.periodo_ingreso.label("periodo"),
        )
        .select_from(Estudiante)
        .outerjoin(Ingreso, Ingreso.id_codigo_alumno == Estudiante.id_codigo_alumno)
        .outerjoin(Programa, Programa.id_prog == Ingreso.id_prog)
        .outerjoin(Facultad, Facultad.id_facultad == Programa.id_facultad)
        .outerjoin(Especialidad, Especialidad.id_especialidad == Ingreso.id_especialidad)
        .outerjoin(Beca, Beca.id_beca == Estudiante.id_beca)
        .outerjoin(Matricula, Matricula.id_ingreso == Ingreso.id_ingreso)
    )

    if filtros.get("facultad"):
        consulta = consulta.filter(
            Facultad.nomb_facultad == filtros["facultad"]
        )
    if filtros.get("programa"):
        nombre_programa, separador, facultad_programa = filtros["programa"].partition("||")
        consulta = consulta.filter(
            func.trim(Programa.nombre_prog) == nombre_programa
        )
        if separador and facultad_programa:
            consulta = consulta.filter(
                Facultad.nomb_facultad == facultad_programa
            )
    if filtros.get("carrera"):
        partes_carrera = filtros["carrera"].split("||", 2)
        nombre_carrera = partes_carrera[0]
        consulta = consulta.filter(
            func.trim(Especialidad.nomb_especialidad) == nombre_carrera
        )
        if len(partes_carrera) > 1 and partes_carrera[1]:
            consulta = consulta.filter(
                func.trim(Programa.nombre_prog) == partes_carrera[1]
            )
        if len(partes_carrera) > 2 and partes_carrera[2]:
            consulta = consulta.filter(Facultad.nomb_facultad == partes_carrera[2])
    if filtros.get("genero"):
        consulta = consulta.filter(Estudiante.sexo == filtros["genero"])
    if filtros.get("beca"):
        consulta = consulta.filter(Beca.nomb_beca == filtros["beca"])
    if filtros.get("periodo"):
        consulta = consulta.filter(
            Ingreso.periodo_ingreso == filtros["periodo"]
        )
    if filtros.get("modalidad"):
        consulta = consulta.filter(
            Matricula.modalidad_estudio == filtros["modalidad"]
        )
    if filtros.get("nivel"):
        consulta = consulta.filter(Matricula.nivel == filtros["nivel"])
    if filtros.get("ciclo"):
        consulta = consulta.filter(Matricula.ciclo == filtros["ciclo"])
    if filtros.get("buscar"):
        termino = f"%{filtros['buscar']}%"
        consulta = consulta.filter(
            or_(
                Estudiante.id_codigo_alumno.ilike(termino),
                Estudiante.num_dni.ilike(termino),
                Estudiante.nombres.ilike(termino),
                Estudiante.apellido_pat.ilike(termino),
                Estudiante.apellido_mat.ilike(termino),
            )
        )

    return consulta


def _filtros_indicadores():
    return {
        nombre: (request.args.get(nombre) or "").strip()
        for nombre in (
            "facultad",
            "programa",
            "carrera",
            "genero",
            "beca",
            "periodo",
            "modalidad",
            "nivel",
            "ciclo",
            "buscar",
            "nivel_academico",
            "grado_posgrado",
            "anio_desde",
            "anio_hasta",
        )
    }


def _condicion_nivel(filtros):
    nivel = func.lower(func.trim(Matricula.nivel))
    nivel_academico = filtros.get("nivel_academico")
    grado = filtros.get("grado_posgrado")
    condiciones = []
    if nivel_academico == "pregrado":
        condiciones.append(nivel.in_(("pregrado", "p", "pre")))
    elif nivel_academico == "posgrado":
        condiciones.append(nivel.in_(
            ("posgrado", "postgrado", "pg", "m", "d", "maestria", "doctorado")
        ))
    if grado == "maestria":
        condiciones.append(nivel.in_(("m", "maestria", "magister")))
    elif grado == "doctorado":
        condiciones.append(nivel.in_(("d", "doctorado", "doctor")))
    return condiciones


def _columnas_solicitadas():
    solicitadas = [
        columna.strip()
        for columna in (request.args.get("columnas") or "").split(",")
        if columna.strip()
    ]
    if not solicitadas:
        solicitadas = [
            "codigo",
            "apellidos",
            "nombres",
            "facultad",
            "programa",
            "carrera",
            "periodo",
            "genero",
            "beca",
        ]
    invalidas = [columna for columna in solicitadas if columna not in COLUMNAS_REPORTE]
    if invalidas:
        raise ValueError(
            f"Columnas de reporte no válidas: {', '.join(invalidas)}"
        )
    return list(dict.fromkeys(solicitadas))


def _filas_detalle_indicadores(filtros, columnas):
    expresiones = [
        expresion.label(COLUMNAS_REPORTE[columna][0])
        for columna, (_, expresion) in (
            (columna, COLUMNAS_REPORTE[columna])
            for columna in columnas
        )
    ]
    return (
        _consulta_indicadores(filtros)
        .with_entities(*expresiones)
        .order_by(
            Estudiante.apellido_pat,
            Estudiante.apellido_mat,
            Estudiante.nombres,
        )
        .all()
    )


def _formatear_excel(archivo, datos, filtros, titulo):
    with pd.ExcelWriter(archivo, engine="openpyxl") as escritor:
        libro = escritor.book
        hoja = libro.create_sheet("Reporte")
        hoja["A1"] = titulo
        hoja["A1"].font = Font(size=16, bold=True, color="FFFFFF")
        hoja["A1"].fill = PatternFill("solid", fgColor="123B63")
        hoja["A1"].alignment = Alignment(horizontal="left")
        hoja.merge_cells(
            start_row=1,
            start_column=1,
            end_row=1,
            end_column=max(len(datos.columns), 1),
        )
        hoja["A2"] = "Generado"
        hoja["B2"] = datetime.now().strftime("%d/%m/%Y %H:%M")
        hoja["A3"] = "Filtros aplicados"
        hoja["A3"].font = Font(bold=True, color="123B63")
        fila_filtros = 4
        for clave, valor in filtros.items():
            if valor:
                hoja.cell(fila_filtros, 1, clave.replace("_", " ").title())
                hoja.cell(fila_filtros, 2, valor)
                fila_filtros += 1
        fila_inicio = fila_filtros + 1
        for indice, nombre in enumerate(datos.columns, 1):
            celda = hoja.cell(fila_inicio, indice, nombre)
            celda.font = Font(bold=True, color="FFFFFF")
            celda.fill = PatternFill("solid", fgColor="1F6AA5")
            celda.alignment = Alignment(horizontal="center")
        for fila, valores in enumerate(datos.itertuples(index=False), fila_inicio + 1):
            for columna, valor in enumerate(valores, 1):
                hoja.cell(fila, columna, valor)
        ultima_fila = fila_inicio + len(datos)
        ultima_columna = max(len(datos.columns), 1)
        hoja.auto_filter.ref = (
            f"A{fila_inicio}:{get_column_letter(ultima_columna)}{ultima_fila}"
        )
        hoja.freeze_panes = f"A{fila_inicio + 1}"
        for columna in range(1, ultima_columna + 1):
            letra = get_column_letter(columna)
            ancho = max(
                len(str(hoja.cell(fila, columna).value or ""))
                for fila in range(fila_inicio, min(ultima_fila, fila_inicio + 100) + 1)
            )
            hoja.column_dimensions[letra].width = min(max(ancho + 2, 12), 36)
        for fila in range(fila_inicio + 1, ultima_fila + 1):
            for columna, nombre in enumerate(datos.columns, 1):
                if "Promedio" in nombre:
                    hoja.cell(fila, columna).number_format = "0.000"

        filtros_df = pd.DataFrame([
            {"Filtro": clave.replace("_", " ").title(), "Valor": valor}
            for clave, valor in filtros.items() if valor
        ])
        filtros_df.to_excel(escritor, index=False, sheet_name="Filtros")
    return archivo


TABLAS_REINICIO = (
    "historial_cargas_cambios",
    "historial_cargas",
    "matricula",
    "ingreso",
    "estudiante",
    "colegio",
    "movilidad",
    "discapacidad",
    "ubigeo",
    "beca",
    "especialidad",
    "programa",
    "facultad",
    "sede",
    "local",
)


def _valor_snapshot(valor):
    if valor is None or isinstance(valor, (str, int, float, bool)):
        return valor
    if hasattr(valor, "isoformat"):
        return valor.isoformat()
    return str(valor)


def _snapshot_modelo(instancia):
    return {
        columna.name: _valor_snapshot(getattr(instancia, columna.name))
        for columna in instancia.__table__.columns
    }


def _convertir_valor(columna, valor):
    if valor is None:
        return None

    tipo = columna.type
    python_type = getattr(tipo, "python_type", None)

    if python_type is date:
        return date.fromisoformat(valor)
    if python_type is datetime:
        return datetime.fromisoformat(valor)
    if python_type is Decimal:
        return Decimal(str(valor))
    if python_type is int:
        return int(valor)
    if python_type is float:
        return float(valor)
    if python_type is bool:
        return bool(valor)
    return valor


def _obtener_instancia(cambio):
    modelo = MODELOS_REVERSIBLES.get(cambio.tabla)
    if modelo is None:
        raise ValueError(
            f"La tabla '{cambio.tabla}' no está habilitada para reversión."
        )

    clave = next(
        columna.name
        for columna in modelo.__table__.primary_key.columns
    )
    return modelo, clave, db.session.get(modelo, cambio.clave_registro)


def _tiene_otra_carga_activa(cambio, carga):
    filtros = [
        HistorialCargaCambio.id_cambio != cambio.id_cambio,
        HistorialCargaCambio.tabla == cambio.tabla,
        HistorialCargaCambio.clave_registro == cambio.clave_registro,
        HistorialCargaCambio.id_carga != carga.id_carga,
        HistorialCarga.estado != "Eliminado",
    ]

    if cambio.operacion != "creado":
        filtros.append(HistorialCargaCambio.id_carga > carga.id_carga)

    return (
        db.session.query(HistorialCargaCambio.id_cambio)
        .join(
            HistorialCarga,
            HistorialCarga.id_carga == HistorialCargaCambio.id_carga,
        )
        .filter(*filtros)
        .first()
        is not None
    )


def _cargar_instancias(cambios):
    instancias = {}
    cambios_por_tabla = {}

    for cambio in cambios:
        cambios_por_tabla.setdefault(cambio.tabla, set()).add(
            cambio.clave_registro
        )

    for tabla, claves in cambios_por_tabla.items():
        modelo = MODELOS_REVERSIBLES.get(tabla)
        if modelo is None:
            raise ValueError(
                f"La tabla '{tabla}' no está habilitada para reversión."
            )

        clave = next(
            columna.name
            for columna in modelo.__table__.primary_key.columns
        )
        columna_clave = getattr(modelo, clave)
        filas = modelo.query.filter(
            columna_clave.in_(list(claves))
        ).all()
        instancias.update(
            (
                (tabla, str(getattr(fila, clave))),
                fila
            )
            for fila in filas
        )

    return instancias


def _cargar_cargas_con_conflictos(carga):
    conflictos = {}
    cambios = (
        HistorialCargaCambio.query
        .join(
            HistorialCarga,
            HistorialCarga.id_carga == HistorialCargaCambio.id_carga,
        )
        .filter(
            HistorialCargaCambio.id_carga != carga.id_carga,
            HistorialCarga.estado != "Eliminado",
        )
        .all()
    )

    for cambio in cambios:
        clave = (cambio.tabla, cambio.clave_registro)
        conflictos.setdefault(clave, []).append(cambio.id_carga)

    return conflictos


@dashboard_bp.route(
    "/dashboard/resumen",
    methods=["GET"]
)
def obtener_resumen():
    try:
        # Historial de cargas de archivos Excel
        ultima_carga = (
            db.session.query(
                HistorialCarga.nombre_archivo,
                func.max(HistorialCarga.id_carga).label("id_carga"),
            )
            .filter(HistorialCarga.estado.notin_(("Eliminado", "Descartada")))
            .group_by(HistorialCarga.nombre_archivo)
            .subquery()
        )
        cargas = (
            HistorialCarga.query
            .join(
                ultima_carga,
                HistorialCarga.id_carga == ultima_carga.c.id_carga,
            )
            .all()
        )

        hoy = date.today()

        # Archivos cargados durante el día actual
        archivos_hoy = sum(
            1
            for carga in cargas
            if carga.fecha_carga
            and carga.fecha_carga.date() == hoy
        )

        # Cargas completadas o validadas
        validados = sum(
            1
            for carga in cargas
            if (carga.estado or "").strip().lower()
            in ("completado", "validado", "apto")
        )

        # Cargas con observaciones o inconsistencias
        con_observaciones = sum(
            1
            for carga in cargas
            if "observ" in (carga.estado or "").lower()
            or (carga.inconsistencias or 0) > 0
        )

        # NUEVO: contar estudiantes que existen actualmente
        registros_procesados = Estudiante.query.count()

        # Total de inconsistencias registradas en el historial
        inconsistencias = sum(
            carga.inconsistencias or 0
            for carga in cargas
            if (carga.estado or "").strip().lower()
            in ("analizada", "en corrección", "en revision", "en revisión", "observado")
        )

        periodo = _periodo_academico_actual()
        return jsonify({
            "periodo": periodo,
            "periodoSiguiente": _periodo_academico_siguiente(periodo),
            "archivosHoy": archivos_hoy,
            "validados": validados,
            "conObservaciones": con_observaciones,
            "registrosProcesados": registros_procesados,
            "inconsistencias": inconsistencias
        }), 200

    except Exception as e:
        print("Error en resumen del dashboard:", str(e))

        return jsonify({
            "error": "No se pudo consultar el resumen del dashboard."
        }), 500


@dashboard_bp.route(
    "/indicadores/resumen",
    methods=["GET"]
)
def obtener_indicadores():
    try:
        filtros = _filtros_indicadores()
        facultad_filtro = filtros["facultad"]
        periodo_filtro = filtros["periodo"]
        periodos_disponibles = sorted({
            str(periodo).strip()
            for (periodo,) in db.session.query(Ingreso.periodo_ingreso)
            .filter(Ingreso.periodo_ingreso.isnot(None))
            .distinct()
            .all()
            if str(periodo).strip()
        })
        anios_disponibles = sorted({
            periodo[:4] for periodo in periodos_disponibles
            if len(periodo) >= 4 and periodo[:4].isdigit()
        })
        # Los indicadores deben iniciar con todo el histórico disponible.
        # Limitarlo a los primeros años hacía que facultades con registros
        # recientes aparecieran sin contenido al seleccionarlas.
        anios_defecto = anios_disponibles
        anio_desde = filtros["anio_desde"] or (
            anios_defecto[0] if anios_defecto else ""
        )
        anio_hasta = filtros["anio_hasta"] or (
            anios_defecto[-1] if anios_defecto else ""
        )

        estudiantes = Estudiante.query
        ingresos = Ingreso.query

        if facultad_filtro:
            estudiantes = estudiantes.filter(
                Estudiante.ingresos.any(
                    Ingreso.programa.has(
                        Programa.facultad.has(
                            Facultad.nomb_facultad.ilike(
                                f"%{facultad_filtro}%"
                            )
                        )
                    )
                )
            )
            ingresos = ingresos.join(Ingreso.programa).join(
                Programa.facultad
            ).filter(Facultad.nomb_facultad.ilike(
                f"%{facultad_filtro}%"
            ))

        programa_filtro = filtros["programa"].partition("||")[0]
        carrera_filtro = filtros["carrera"].partition("||")[0]
        if programa_filtro:
            estudiantes = estudiantes.filter(
                Estudiante.ingresos.any(
                    Ingreso.programa.has(
                        func.trim(Programa.nombre_prog) == programa_filtro
                    )
                )
            )
            ingresos = ingresos.filter(
                Ingreso.programa.has(
                    func.trim(Programa.nombre_prog) == programa_filtro
                )
            )

        if carrera_filtro:
            estudiantes = estudiantes.filter(
                Estudiante.ingresos.any(
                    Ingreso.especialidad.has(
                        func.trim(Especialidad.nomb_especialidad) == carrera_filtro
                    )
                )
            )
            ingresos = ingresos.filter(
                Ingreso.especialidad.has(
                    func.trim(Especialidad.nomb_especialidad) == carrera_filtro
                )
            )

        if periodo_filtro:
            estudiantes = estudiantes.filter(
                Estudiante.ingresos.any(
                    Ingreso.periodo_ingreso == periodo_filtro
                )
            )
            ingresos = ingresos.filter(
                Ingreso.periodo_ingreso == periodo_filtro
            )

        if anio_desde:
            estudiantes = estudiantes.filter(
                Estudiante.ingresos.any(
                    func.substr(Ingreso.periodo_ingreso, 1, 4) >= anio_desde
                )
            )
            ingresos = ingresos.filter(
                func.substr(Ingreso.periodo_ingreso, 1, 4) >= anio_desde
            )
        if anio_hasta:
            estudiantes = estudiantes.filter(
                Estudiante.ingresos.any(
                    func.substr(Ingreso.periodo_ingreso, 1, 4) <= anio_hasta
                )
            )
            ingresos = ingresos.filter(
                func.substr(Ingreso.periodo_ingreso, 1, 4) <= anio_hasta
            )

        for condicion in _condicion_nivel(filtros):
            estudiantes = estudiantes.filter(
                Estudiante.ingresos.any(Ingreso.matriculas.any(condicion))
            )
            ingresos = ingresos.filter(Ingreso.matriculas.any(condicion))

        total_estudiantes = estudiantes.distinct().count()
        total_programas = ingresos.with_entities(
            Ingreso.id_prog
        ).filter(Ingreso.id_prog.isnot(None)).distinct().count()
        total_matriculas = (
            Matricula.query
            .join(Ingreso, Matricula.id_ingreso == Ingreso.id_ingreso)
            .filter(Ingreso.id_ingreso.in_(
                ingresos.with_entities(Ingreso.id_ingreso)
            ))
            .count()
        )
        facultades = ingresos.join(
            Ingreso.programa
        ).with_entities(
            Programa.id_facultad
        ).filter(
            Programa.id_facultad.isnot(None)
        ).distinct().count()

        ingreso_ids = ingresos.with_entities(Ingreso.id_ingreso)
        totales_facultad = dict(
            db.session.query(
                Facultad.nomb_facultad,
                func.count(func.distinct(Estudiante.id_codigo_alumno)),
            )
            .join(Programa, Programa.id_facultad == Facultad.id_facultad)
            .join(Ingreso, Ingreso.id_prog == Programa.id_prog)
            .join(
                Estudiante,
                Estudiante.id_codigo_alumno == Ingreso.id_codigo_alumno,
            )
            .filter(Ingreso.id_ingreso.in_(ingreso_ids))
            .group_by(Facultad.nomb_facultad)
            .all()
        )
        por_facultad = (
            db.session.query(
                Facultad.nomb_facultad,
                func.coalesce(
                    func.trim(Especialidad.nomb_especialidad),
                    func.trim(Programa.nombre_prog),
                ),
                func.count(func.distinct(Estudiante.id_codigo_alumno)),
            )
            .join(Programa, Programa.id_facultad == Facultad.id_facultad)
            .join(Ingreso, Ingreso.id_prog == Programa.id_prog)
            .outerjoin(Especialidad, Especialidad.id_especialidad == Ingreso.id_especialidad)
            .join(
                Estudiante,
                Estudiante.id_codigo_alumno == Ingreso.id_codigo_alumno,
            )
            .filter(Ingreso.id_ingreso.in_(ingreso_ids))
            .group_by(
                Facultad.nomb_facultad,
                func.coalesce(
                    func.trim(Especialidad.nomb_especialidad),
                    func.trim(Programa.nombre_prog),
                ),
            )
            .order_by(Facultad.nomb_facultad, func.count(
                func.distinct(Estudiante.id_codigo_alumno)
            ).desc())
            .all()
        )

        por_periodo = (
            db.session.query(
                Ingreso.periodo_ingreso,
                func.count(func.distinct(Ingreso.id_codigo_alumno)),
            )
            .filter(
                Ingreso.periodo_ingreso.isnot(None),
                Ingreso.id_ingreso.in_(ingreso_ids),
            )
            .group_by(Ingreso.periodo_ingreso)
            .order_by(Ingreso.periodo_ingreso)
            .all()
        )

        serie_grupo = Facultad.nomb_facultad
        if facultad_filtro:
            serie_grupo = func.coalesce(
                func.trim(Especialidad.nomb_especialidad),
                func.trim(Programa.nombre_prog),
            )
        anio_ingreso = func.substr(Ingreso.periodo_ingreso, 1, 4)
        serie_periodos_query = (
            db.session.query(
                serie_grupo,
                anio_ingreso,
                func.count(func.distinct(Ingreso.id_codigo_alumno)),
            )
            .join(Programa, Programa.id_prog == Ingreso.id_prog)
            .join(Facultad, Facultad.id_facultad == Programa.id_facultad)
            .outerjoin(
                Especialidad,
                Especialidad.id_especialidad == Ingreso.id_especialidad,
            )
            .filter(Ingreso.id_ingreso.in_(ingreso_ids))
            .filter(Ingreso.periodo_ingreso.isnot(None))
            .group_by(serie_grupo, anio_ingreso)
            .order_by(serie_grupo, anio_ingreso)
            .all()
        )
        series_periodo = {}
        for nombre, anio, total in serie_periodos_query:
            series_periodo.setdefault(str(nombre or "Sin categoría"), {})[
                str(anio).strip()
            ] = total
        anio_inicio = int(anio_desde) if anio_desde.isdigit() else None
        anio_fin = int(anio_hasta) if anio_hasta.isdigit() else None
        anios_grafico = (
            [str(anio) for anio in range(anio_inicio, anio_fin + 1)]
            if anio_inicio is not None
            and anio_fin is not None
            and anio_inicio <= anio_fin
            else anios_disponibles
        )
        series_periodo = [
            {
                "nombre": nombre,
                "puntos": [
                    {
                        "periodo": anio,
                        "total": valores.get(anio),
                    }
                    for anio in anios_grafico
                ],
            }
            for nombre, valores in series_periodo.items()
        ]
        distribucion_facultades = [
            {
                "nombre": nombre,
                "total": totales_facultad.get(nombre, 0),
                "carreras": [
                    {"nombre": carrera, "total": carrera_total}
                    for facultad, carrera, carrera_total in por_facultad
                    if facultad == nombre
                ],
            }
            for nombre in totales_facultad
        ]
        distribucion_facultades.sort(key=lambda fila: fila["total"], reverse=True)

        estudiante_ids = estudiantes.with_entities(Estudiante.id_codigo_alumno)
        por_beca = (
            db.session.query(
                func.coalesce(Beca.nomb_beca, "Sin beca"),
                func.count(func.distinct(Estudiante.id_codigo_alumno)),
            )
            .outerjoin(Beca, Estudiante.id_beca == Beca.id_beca)
            .filter(Estudiante.id_codigo_alumno.in_(estudiante_ids))
            .group_by(func.coalesce(Beca.nomb_beca, "Sin beca"))
            .order_by(func.count(func.distinct(
                Estudiante.id_codigo_alumno
            )).desc())
            .all()
        )

        por_genero = (
            db.session.query(
                func.coalesce(Estudiante.sexo, "Sin especificar"),
                func.count(func.distinct(Estudiante.id_codigo_alumno)),
            )
            .filter(Estudiante.id_codigo_alumno.in_(estudiante_ids))
            .group_by(func.coalesce(Estudiante.sexo, "Sin especificar"))
            .order_by(func.count(func.distinct(
                Estudiante.id_codigo_alumno
            )).desc())
            .all()
        )

        return jsonify({
            "modulos": {
                "estudiantes": Estudiante.query.count(),
                "docentes": 0,
                "administrativos": 0,
                "egresados_titulados": 0,
            },
            "kpis": {
                "estudiantes": total_estudiantes,
                "programas": total_programas,
                "matriculas": total_matriculas,
                "facultades": facultades,
            },
            "por_facultad": distribucion_facultades,
            "por_periodo": [
                {"nombre": periodo, "total": total}
                for periodo, total in por_periodo
            ],
            "series_periodo": series_periodo,
            "anios": anios_disponibles,
            "anios_grafico": anios_grafico,
            "anio_desde": anio_desde,
            "anio_hasta": anio_hasta,
            "por_beca": [
                {"nombre": nombre, "total": total}
                for nombre, total in por_beca
            ],
            "por_genero": [
                {"nombre": nombre, "total": total}
                for nombre, total in por_genero
            ],
        }), 200

    except Exception as e:
        db.session.rollback()
        print("Error en indicadores:", repr(e))
        return jsonify({
            "error": "No se pudieron calcular los indicadores.",
            "detalle": str(e),
        }), 500


@dashboard_bp.route(
    "/indicadores/tabla",
    methods=["GET"]
)
def obtener_tabla_indicadores():
    tipo = request.args.get("tipo", "resumen")
    dimension = request.args.get("dimension", "facultad")
    metrica = request.args.get("metrica", "total")
    columna = DIMENSIONES_INDICADORES.get(dimension)

    if tipo == "detalle":
        try:
            filtros = _filtros_indicadores()
            columnas = _columnas_solicitadas()
            filas = _filas_detalle_indicadores(filtros, columnas)
            return jsonify({
                "tipo": tipo,
                "total": len(filas),
                "columnas": [COLUMNAS_REPORTE[columna][0] for columna in columnas],
                "filas": [
                    {
                        clave: _valor_snapshot(valor)
                        for clave, valor in fila._mapping.items()
                    }
                    for fila in filas
                ],
            }), 200
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            db.session.rollback()
            print("Error al construir detalle de indicadores:", repr(e))
            return jsonify({
                "error": "No se pudo construir el detalle.",
                "detalle": str(e),
            }), 500

    if columna is None:
        return jsonify({"error": "La dimensión indicada no es válida."}), 400
    if metrica not in ("total", "participacion"):
        return jsonify({"error": "La métrica indicada no es válida."}), 400

    filtros = _filtros_indicadores()

    try:
        filas = (
            _consulta_indicadores(filtros)
            .with_entities(
                columna.label("nombre"),
                func.count(func.distinct(
                    Estudiante.id_codigo_alumno
                )).label("total"),
            )
            .group_by(columna)
            .order_by(func.count(func.distinct(
                Estudiante.id_codigo_alumno
            )).desc())
            .all()
        )
        total = sum(int(fila.total or 0) for fila in filas)
        resultado = []
        for fila in filas:
            cantidad = int(fila.total or 0)
            resultado.append({
                "nombre": fila.nombre or "Sin especificar",
                "total": cantidad,
                "participacion": round(
                    cantidad / max(total, 1) * 100,
                    2,
                ),
            })

        return jsonify({
            "dimension": dimension,
            "metrica": metrica,
            "total": total,
            "filas": resultado,
        }), 200
    except Exception as e:
        db.session.rollback()
        print("Error al construir tabla de indicadores:", repr(e))
        return jsonify({
            "error": "No se pudo construir la tabla.",
            "detalle": str(e),
        }), 500


@dashboard_bp.route(
    "/indicadores/exportar",
    methods=["GET"]
)
def exportar_indicadores():
    tipo = request.args.get("tipo", "resumen")
    filtros = _filtros_indicadores()

    if tipo == "detalle":
        try:
            columnas = _columnas_solicitadas()
            filas = _filas_detalle_indicadores(filtros, columnas)
            datos = pd.DataFrame(
                [
                    {
                        clave: _valor_snapshot(valor)
                        for clave, valor in fila._mapping.items()
                    }
                    for fila in filas
                ],
                columns=[COLUMNAS_REPORTE[columna][0] for columna in columnas],
            )
            archivo = BytesIO()
            _formatear_excel(
                archivo,
                datos,
                filtros,
                "Reporte detallado de estudiantes",
            )
            archivo.seek(0)
            return send_file(
                archivo,
                as_attachment=True,
                download_name="reporte_detallado_estudiantes.xlsx",
                mimetype=(
                    "application/vnd.openxmlformats-officedocument."
                    "spreadsheetml.sheet"
                ),
            )
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            db.session.rollback()
            print("Error al exportar detalle de indicadores:", repr(e))
            return jsonify({
                "error": "No se pudo exportar el detalle.",
                "detalle": str(e),
            }), 500

    dimension = request.args.get("dimension", "facultad")
    metrica = request.args.get("metrica", "total")
    columna = DIMENSIONES_INDICADORES.get(dimension)

    if columna is None or metrica not in ("total", "participacion"):
        return jsonify({"error": "Parámetros de exportación inválidos."}), 400

    try:
        filas = (
            _consulta_indicadores(filtros)
            .with_entities(
                columna.label("Dimensión"),
                func.count(func.distinct(
                    Estudiante.id_codigo_alumno
                )).label("Total"),
            )
            .group_by(columna)
            .order_by(func.count(func.distinct(
                Estudiante.id_codigo_alumno
            )).desc())
            .all()
        )
        datos = [
            {
                "Dimensión": fila[0] or "Sin especificar",
                "Total": int(fila[1] or 0),
            }
            for fila in filas
        ]
        total = sum(fila["Total"] for fila in datos)
        if metrica == "participacion":
            for fila in datos:
                fila["Participación"] = round(
                    fila["Total"] / max(total, 1) * 100,
                    2,
                )
        datos_df = pd.DataFrame(datos)
        archivo = BytesIO()
        _formatear_excel(
            archivo,
            datos_df,
            {
                "dimensión": dimension,
                "métrica": metrica,
                **filtros,
            },
            f"Indicadores por {dimension}",
        )
        archivo.seek(0)
        return send_file(
            archivo,
            as_attachment=True,
            download_name=f"indicadores_{dimension}.xlsx",
            mimetype=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
        )
    except Exception as e:
        db.session.rollback()
        print("Error al exportar indicadores:", repr(e))
        return jsonify({
            "error": "No se pudo exportar el indicador.",
            "detalle": str(e),
        }), 500


@dashboard_bp.route(
    "/cargas",
    methods=["GET"]
)
def obtener_cargas():
    limite = request.args.get(
        "limite",
        default=10,
        type=int
    )

    if limite is None or limite < 1:
        return jsonify({
            "error": "El límite debe ser un entero positivo."
        }), 400

    try:
        cargas = (
            HistorialCarga.query
            .order_by(HistorialCarga.fecha_carga.desc())
            .limit(limite)
            .all()
        )

        resultado = []

        for carga in cargas:
            fecha = carga.fecha_carga

            resultado.append({
                "id": carga.id_carga,
                "nombre": carga.nombre_archivo,
                "tamano": None,
                "registros": carga.total_filas,
                "tipo": carga.tipo_planilla,
                "dependencia": None,
                "subidoPor": None,
                "cargo": (
                    fecha.strftime("%d/%m/%Y")
                    if fecha else None
                ),
                "hora": (
                    fecha.strftime("%H:%M")
                    if fecha else None
                ),
                "estado": carga.estado,
                "registrosProcesados": carga.registros_procesados,
                "inconsistencias": carga.inconsistencias,
                "observaciones": carga.observaciones
            })

        return jsonify(resultado), 200

    except Exception as e:
        print("Error en historial de cargas:", str(e))

        return jsonify({
            "error": "No se pudo consultar el historial de cargas."
        }), 500


@dashboard_bp.route(
    "/base-datos/reiniciar",
    methods=["POST"]
)
def reiniciar_base_datos():
    tablas = ", ".join(TABLAS_REINICIO)

    try:
        db.session.execute(text(
            f"TRUNCATE TABLE {tablas} RESTART IDENTITY CASCADE"
        ))
        db.session.commit()

        return jsonify({
            "estado": "Reiniciada",
            "mensaje": "La base de datos fue reiniciada correctamente."
        }), 200

    except Exception as e:
        db.session.rollback()
        print("Error al reiniciar la base de datos:", repr(e))
        traceback.print_exc()

        return jsonify({
            "error": "No se pudo reiniciar la base de datos.",
            "detalle": str(e)
        }), 500


@dashboard_bp.route(
    "/cargas/<int:id_carga>",
    methods=["DELETE"]
)
def eliminar_carga(id_carga):
    try:
        carga = db.session.get(HistorialCarga, id_carga)

        if carga is None:
            return jsonify({
                "error": "La carga no existe."
            }), 404

        if (carga.estado or "").strip().lower() == "eliminado":
            return jsonify({
                "error": "La carga ya fue eliminada."
            }), 409

        advertencias = []
        cambios = list(carga.cambios)
        instancias = _cargar_instancias(cambios)
        conflictos = _cargar_cargas_con_conflictos(carga)
        claves_para_eliminar = {}

        for cambio in reversed(cambios):
            modelo = MODELOS_REVERSIBLES.get(cambio.tabla)
            if modelo is None:
                raise ValueError(
                    f"La tabla '{cambio.tabla}' no está habilitada para reversión."
                )

            clave = next(
                columna.name
                for columna in modelo.__table__.primary_key.columns
            )
            instancia = instancias.get(
                (cambio.tabla, cambio.clave_registro)
            )

            if instancia is None:
                continue

            cargas_relacionadas = conflictos.get(
                (cambio.tabla, cambio.clave_registro),
                []
            )
            tiene_conflicto = (
                bool(cargas_relacionadas)
                if cambio.operacion == "creado"
                else any(
                    id_otra_carga > carga.id_carga
                    for id_otra_carga in cargas_relacionadas
                )
            )

            if tiene_conflicto:
                advertencias.append(
                    f"{cambio.tabla}:{cambio.clave_registro} "
                    "se conserva porque pertenece a otra carga activa."
                )
                continue

            snapshot_actual = _snapshot_modelo(instancia)
            snapshot_nuevo = cambio.valores_nuevos or {}

            if snapshot_actual != snapshot_nuevo:
                advertencias.append(
                    f"{cambio.tabla}:{cambio.clave_registro} "
                    "se conserva porque cambió después de esta carga."
                )
                continue

            if cambio.operacion == "creado":
                claves_para_eliminar.setdefault(modelo, set()).add(
                    getattr(instancia, clave)
                )
                continue

            if cambio.operacion != "modificado":
                raise ValueError(
                    f"Operación de cambio no válida: {cambio.operacion}"
                )

            valores_anteriores = cambio.valores_anteriores or {}
            columnas = {
                columna.name: columna
                for columna in modelo.__table__.columns
            }

            for nombre, valor in valores_anteriores.items():
                if nombre != clave and nombre in columnas:
                    setattr(
                        instancia,
                        nombre,
                        _convertir_valor(columnas[nombre], valor)
                    )

        modelos_ordenados = (
            modelo
            for modelo in ORDEN_ELIMINACION
            if modelo in claves_para_eliminar
        )
        db.session.flush()
        for modelo in modelos_ordenados:
            claves = claves_para_eliminar[modelo]
            clave = next(
                columna.name
                for columna in modelo.__table__.primary_key.columns
            )
            columna_clave = getattr(modelo, clave)
            db.session.execute(
                modelo.__table__.delete().where(
                    columna_clave.in_(claves)
                ),
                execution_options={"synchronize_session": False},
            )

        carga.estado = "Eliminado"
        carga.observaciones = (
            "Carga eliminada."
            if not advertencias
            else "Carga eliminada con registros conservados: "
            + " ".join(advertencias)
        )
        db.session.commit()

        return jsonify({
            "estado": "Eliminado",
            "id": carga.id_carga,
            "advertencias": advertencias
        }), 200

    except Exception as e:
        db.session.rollback()
        print("Error al eliminar carga:", repr(e))
        traceback.print_exc()

        return jsonify({
            "error": "No se pudo revertir la carga.",
            "detalle": str(e)
        }), 500