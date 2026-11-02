from flask import Blueprint, jsonify, request
from sqlalchemy import func, or_, select, text
from sqlalchemy.orm import joinedload, selectinload
import pandas as pd

from extensions import db
from models.estudiantes import (
    Estudiante, Matricula, Ingreso, Programa, Facultad, Especialidad,
    Colegio, Ubigeo, Beca, Discapacidad, Movilidad, Sede, Local,
)

from models.historial_cargas import HistorialCarga, HistorialCargaCambio

estudiante_bp = Blueprint("estudiante_bp", __name__)


@estudiante_bp.route("/")
def inicio():
    return "Backend funcionando correctamente"


@estudiante_bp.route("/test-db")
def test_db():
    try:
        db.session.execute(text("SELECT 1"))
        return "Conexión a PostgreSQL exitosa"
    except Exception as e:
        return f"Error de conexión: {e}"


# ======================================================================
# SERIALIZADORES (igual que tu versión original)
# ======================================================================

def opciones_estudiante():
    """Carga anticipada de todas las relaciones que usa serializar_estudiante."""
    return [
        joinedload(Estudiante.beca),
        joinedload(Estudiante.colegio),
        joinedload(Estudiante.discapacidad),
        joinedload(Estudiante.movilidad),
        joinedload(Estudiante.ubigeo),
        selectinload(Estudiante.ingresos).joinedload(Ingreso.programa).joinedload(Programa.facultad),
        selectinload(Estudiante.ingresos).joinedload(Ingreso.especialidad),
        selectinload(Estudiante.ingresos).joinedload(Ingreso.sede),
        selectinload(Estudiante.ingresos).selectinload(Ingreso.matriculas),
    ]


def serializar_estudiante(estudiante: Estudiante, incluir_relaciones=True):
    data = {
        "id_codigo_alumno": estudiante.id_codigo_alumno,
        "tipo_doc_id": estudiante.tipo_doc_id,
        "num_dni": estudiante.num_dni,
        "apellido_pat": estudiante.apellido_pat,
        "apellido_mat": estudiante.apellido_mat,
        "nombres": estudiante.nombres,
        "sexo": estudiante.sexo,
        "fecha_nac": estudiante.fecha_nac.isoformat() if estudiante.fecha_nac else None,
        "nacionalidad": estudiante.nacionalidad,
        "estado_civil": estudiante.estado_civil,
        "correo_inst": estudiante.correo_inst,
        "correo_per": estudiante.correo_per,
        "distrito_domicilio": estudiante.distrito_domicilio,
        "identi_etnica": estudiante.identi_etnica,
        "lengua_nativa": estudiante.lengua_nativa,
        "idioma_extranjero": estudiante.idioma_extranjero,
        "telefono_fijo": estudiante.telefono_fijo,
        "telefono_movil": estudiante.telefono_movil,
        "beca": estudiante.beca.nomb_beca if estudiante.beca else None,
        "colegio": estudiante.colegio.nomb_colegio if estudiante.colegio else None,
        "discapacidad": (
            estudiante.discapacidad.tipo_discapacidad
            if estudiante.discapacidad else None
        ),
        "movilidad": estudiante.movilidad.nomb_movilidad if estudiante.movilidad else None,
        "ubigeo": (
            {
                "pais_nac": estudiante.ubigeo.pais_nac,
                "dep_nac": estudiante.ubigeo.dep_nac,
                "provincia_nac": estudiante.ubigeo.provincia_nac,
                "distrito_nac": estudiante.ubigeo.distrito_nac,
            }
            if estudiante.ubigeo else None
        ),
    }

    if incluir_relaciones:
        data["ingresos"] = [
            serializar_ingreso(ingreso, incluir_matriculas=True)
            for ingreso in estudiante.ingresos
        ]

    return data


def serializar_ingreso(ingreso: Ingreso, incluir_matriculas=False):
    programa = ingreso.programa
    data = {
        "id_ingreso": ingreso.id_ingreso,
        "tipo_preparacion": ingreso.tipo_preparacion,
        "modalidad_ingreso": ingreso.modalidad_ingreso,
        "periodo_ingreso": ingreso.periodo_ingreso,
        "id_codigo_alumno": ingreso.id_codigo_alumno,
        "facultad": (
            programa.facultad.nomb_facultad
            if programa and programa.facultad else None
        ),
        "cod_prog": programa.cod_prog if programa else None,
        "programa": programa.nombre_prog if programa else None,
        "especialidad": (
            ingreso.especialidad.nomb_especialidad
            if ingreso.especialidad else None
        ),
        "sede": ingreso.sede.nomb_sede if ingreso.sede else None,
    }
    if incluir_matriculas:
        data["matriculas"] = [
            serializar_matricula(m, incluir_ingreso=False)
            for m in ingreso.matriculas
        ]
    return data


def serializar_matricula(matricula: Matricula, incluir_ingreso=True):
    data = {
        "id_matricula": matricula.id_matricula,
        "nivel": matricula.nivel,
        "modalidad_estudio": matricula.modalidad_estudio,
        "periodo_mat": matricula.periodo_mat,
        "regimen_matricula": matricula.regimen_matricula,
        "ciclo": matricula.ciclo,
        "permanencia": matricula.permanencia,
        "primer_mat": matricula.primer_mat,
        "creditos_acum_sem": matricula.creditos_acum_sem,
        "creditos_acum_total": matricula.creditos_acum_total,
        "cursos_mat_cat": matricula.cursos_mat_cat,
        "promedio_pond": float(matricula.promedio_pond) if matricula.promedio_pond is not None else None,
        "ranking": matricula.ranking,
    }
    if incluir_ingreso:
        data["id_ingreso"] = matricula.id_ingreso
    return data


# ======================================================================
# CRUD DE ESTUDIANTES (igual que tu versión original)
# ======================================================================

@estudiante_bp.route("/estudiantes", methods=["GET"])
def listar_estudiantes():
    """
    Devuelve todos los estudiantes con sus ingresos y matrículas anidados.
    Soporta paginación opcional: /estudiantes?page=1&per_page=20
    """
    query = Estudiante.query.options(*opciones_estudiante())

    page = request.args.get("page", type=int)
    per_page = request.args.get("per_page", type=int)

    if page and per_page:
        paginado = query.paginate(page=page, per_page=per_page, error_out=False)
        return jsonify({
            "total": paginado.total,
            "page": paginado.page,
            "per_page": paginado.per_page,
            "pages": paginado.pages,
            "estudiantes": [serializar_estudiante(e) for e in paginado.items],
        })

    estudiantes = query.all()
    return jsonify([serializar_estudiante(e) for e in estudiantes])


@estudiante_bp.route("/estudiantes/<string:id_codigo_alumno>", methods=["GET"])
def obtener_estudiante(id_codigo_alumno):
    """Devuelve un estudiante puntual con su historial de ingresos y matrículas."""
    estudiante = (
        Estudiante.query
        .options(*opciones_estudiante())
        .filter_by(id_codigo_alumno=id_codigo_alumno)
        .first()
    )

    if estudiante is None:
        return jsonify({"error": "Estudiante no encontrado"}), 404

    return jsonify(serializar_estudiante(estudiante))


@estudiante_bp.route("/consultas/estudiantes", methods=["GET"])
def consultar_estudiantes():
    pagina = max(request.args.get("page", 1, type=int), 1)
    por_pagina = min(max(request.args.get("per_page", 20, type=int), 1), 100)
    busqueda = (request.args.get("q") or "").strip()
    periodo = (request.args.get("periodo") or "").strip()
    programa = (request.args.get("programa") or "").strip()
    facultad = (request.args.get("facultad") or "").strip()
    estado_matricula = (request.args.get("estado_matricula") or "").strip()
    condicion = (request.args.get("condicion") or "").strip()
    id_carga = request.args.get("carga", type=int)

    consulta = Estudiante.query

    if id_carga is not None:
        carga = db.session.get(HistorialCarga, id_carga)
        if carga is None:
            return jsonify({"error": "La carga no existe."}), 404

        claves_estudiante = select(
            HistorialCargaCambio.clave_registro
        ).where(
            HistorialCargaCambio.id_carga == id_carga,
            HistorialCargaCambio.tabla == Estudiante.__tablename__,
        )
        consulta = consulta.filter(
            Estudiante.id_codigo_alumno.in_(claves_estudiante)
        )

    if busqueda:
        termino = f"%{busqueda}%"
        consulta = consulta.filter(
            or_(
                Estudiante.id_codigo_alumno.ilike(termino),
                Estudiante.num_dni.ilike(termino),
                Estudiante.nombres.ilike(termino),
                Estudiante.apellido_pat.ilike(termino),
                Estudiante.apellido_mat.ilike(termino),
            )
        )

    if periodo:
        consulta = consulta.filter(
            Estudiante.ingresos.any(Ingreso.periodo_ingreso == periodo)
        )

    if programa:
        consulta = consulta.filter(
            Estudiante.ingresos.any(
                Ingreso.programa.has(
                    Programa.nombre_prog.ilike(f"%{programa}%")
                )
            )
        )

    if facultad:
        consulta = consulta.filter(
            Estudiante.ingresos.any(
                Ingreso.programa.has(
                    Programa.facultad.has(
                        Facultad.nomb_facultad.ilike(f"%{facultad}%")
                    )
                )
            )
        )

    if estado_matricula:
        consulta = consulta.filter(
            Estudiante.ingresos.any(
                Ingreso.matriculas.any(
                    Matricula.modalidad_estudio.ilike(
                        f"%{estado_matricula}%"
                    )
                )
            )
        )

    if condicion:
        consulta = consulta.filter(
            Estudiante.ingresos.any(
                Ingreso.matriculas.any(
                    Matricula.permanencia.ilike(f"%{condicion}%")
                )
            )
        )

    pagina_resultado = (
        consulta
        .order_by(
            Estudiante.apellido_pat,
            Estudiante.apellido_mat,
            Estudiante.nombres,
        )
        .paginate(page=pagina, per_page=por_pagina, error_out=False)
    )

    return jsonify({
        "total": pagina_resultado.total,
        "page": pagina_resultado.page,
        "per_page": pagina_resultado.per_page,
        "pages": pagina_resultado.pages,
        "carga": (
            {
                "id": carga.id_carga,
                "nombre": carga.nombre_archivo,
            }
            if id_carga is not None
            else None
        ),
        "estudiantes": [
            {
                "id_codigo_alumno": estudiante.id_codigo_alumno,
                "num_dni": estudiante.num_dni,
                "nombre_completo": " ".join(
                    parte for parte in (
                        estudiante.apellido_pat,
                        estudiante.apellido_mat,
                        estudiante.nombres,
                    )
                    if parte
                ),
                "sexo": estudiante.sexo,
                "correo_inst": estudiante.correo_inst,
                "telefono_movil": estudiante.telefono_movil,
            }
            for estudiante in pagina_resultado.items
        ],
    })


@estudiante_bp.route("/consultas/opciones", methods=["GET"])
def opciones_consulta():
    return jsonify({
        "modulos": {
            "estudiantes": Estudiante.query.count(),
            "docentes": 0,
            "administrativos": 0,
            "egresados_titulados": 0,
        },
        "facultades": [
            {"valor": facultad.nomb_facultad, "texto": facultad.nomb_facultad}
            for facultad in Facultad.query.order_by(Facultad.nomb_facultad).all()
        ],
        "programas": [
            {
                "valor": f"{nombre}||{facultad or ''}",
                "texto": (
                    f"{nombre} — {facultad}"
                    if facultad else f"{nombre} — Sin facultad"
                ),
                "facultad": facultad,
            }
            for nombre, facultad in db.session.query(
                func.trim(Programa.nombre_prog),
                Facultad.nomb_facultad,
            )
            .outerjoin(Facultad, Facultad.id_facultad == Programa.id_facultad)
            .filter(Programa.nombre_prog.isnot(None))
            .distinct()
            .order_by(func.trim(Programa.nombre_prog))
            .all()
        ],
        "carreras": [
            {
                "valor": (
                    f"{nombre}||{programa}||{facultad or ''}"
                    if programa else f"{nombre}||"
                ),
                "texto": (
                    f"{nombre} — {programa}"
                    if programa else f"{nombre} — Sin programa"
                ),
                "programa": f"{programa}||{facultad or ''}" if programa else "",
                "facultad": facultad,
            }
            for nombre, programa, facultad in db.session.query(
                func.trim(Especialidad.nomb_especialidad),
                func.trim(Programa.nombre_prog),
                Facultad.nomb_facultad,
            )
            .outerjoin(Programa, Programa.id_prog == Especialidad.id_prog)
            .outerjoin(Facultad, Facultad.id_facultad == Programa.id_facultad)
            .filter(Especialidad.nomb_especialidad.isnot(None))
            .distinct()
            .order_by(
                func.trim(Especialidad.nomb_especialidad),
                func.trim(Programa.nombre_prog),
            )
            .all()
        ],
        "generos": [
            {"valor": sexo, "texto": sexo}
            for (sexo,) in db.session.query(Estudiante.sexo)
            .filter(Estudiante.sexo.isnot(None))
            .distinct()
            .order_by(Estudiante.sexo)
            .all()
        ],
        "becas": [
            {"valor": beca.nomb_beca, "texto": beca.nomb_beca}
            for beca in Beca.query.order_by(Beca.nomb_beca).all()
        ],
        "periodos": [
            {"valor": periodo, "texto": periodo}
            for (periodo,) in db.session.query(
                Ingreso.periodo_ingreso
            ).filter(
                Ingreso.periodo_ingreso.isnot(None)
            ).distinct().order_by(Ingreso.periodo_ingreso).all()
        ],
        "estados_matricula": [
            {"valor": estado, "texto": estado}
            for (estado,) in db.session.query(
                Matricula.modalidad_estudio
            ).filter(
                Matricula.modalidad_estudio.isnot(None)
            ).distinct().order_by(Matricula.modalidad_estudio).all()
        ],
        "condiciones": [
            {"valor": condicion, "texto": condicion}
            for (condicion,) in db.session.query(
                Matricula.permanencia
            ).filter(
                Matricula.permanencia.isnot(None)
            ).distinct().order_by(Matricula.permanencia).all()
        ],
        "niveles": [
            {"valor": nivel, "texto": nivel}
            for (nivel,) in db.session.query(Matricula.nivel)
            .filter(Matricula.nivel.isnot(None))
            .distinct()
            .order_by(Matricula.nivel)
            .all()
        ],
        "ciclos": [
            {"valor": ciclo, "texto": str(ciclo)}
            for (ciclo,) in db.session.query(Matricula.ciclo)
            .filter(Matricula.ciclo.isnot(None))
            .distinct()
            .order_by(Matricula.ciclo)
            .all()
        ],
    })


@estudiante_bp.route("/estudiantes/<string:id_codigo_alumno>/matriculas", methods=["GET"])
def matriculas_de_estudiante(id_codigo_alumno):
    """Devuelve solo el historial de matrículas de un estudiante, por periodo."""
    matriculas = (
        Matricula.query
        .join(Ingreso, Matricula.id_ingreso == Ingreso.id_ingreso)
        .filter(Ingreso.id_codigo_alumno == id_codigo_alumno)
        .order_by(Matricula.periodo_mat)
        .all()
    )
    return jsonify([serializar_matricula(m) for m in matriculas])


@estudiante_bp.route("/estudiantes/dni/<string:num_dni>", methods=["GET"])
def obtener_estudiante_por_dni(num_dni):
    estudiantes = (
        Estudiante.query
        .options(*opciones_estudiante())
        .filter_by(num_dni=num_dni)
        .all()
    )
    if not estudiantes:
        return jsonify({"error": "Estudiante no encontrado"}), 404
    return jsonify([serializar_estudiante(e) for e in estudiantes])


@estudiante_bp.route("/estudiantes", methods=["POST"])
def crear_estudiante():
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No se enviaron datos"}), 400

        estudiante = Estudiante(
            id_codigo_alumno=data["id_codigo_alumno"],
            tipo_doc_id=data["tipo_doc_id"],
            num_dni=data["num_dni"],
            apellido_pat=data["apellido_pat"],
            apellido_mat=data["apellido_mat"],
            nombres=data["nombres"],
            sexo=data["sexo"],
            fecha_nac=data["fecha_nac"],
            nacionalidad=data.get("nacionalidad"),
            estado_civil=data["estado_civil"],
            correo_inst=data["correo_inst"],
            correo_per=data["correo_per"],
            distrito_domicilio=data["distrito_domicilio"],
            identi_etnica=data["identi_etnica"],
            lengua_nativa=data.get("lengua_nativa"),
            idioma_extranjero=data.get("idioma_extranjero"),
            telefono_fijo=data["telefono_fijo"],
            telefono_movil=data["telefono_movil"],
            id_colegio=data.get("id_colegio"),
            id_movilidad=data.get("id_movilidad"),
            id_beca=data.get("id_beca"),
            id_discapacidad=data.get("id_discapacidad"),
            id_ubigeo=data.get("id_ubigeo"),
        )

        db.session.add(estudiante)
        db.session.commit()

        return jsonify(serializar_estudiante(estudiante)), 201

    except KeyError as e:
        db.session.rollback()
        return jsonify({"error": f"Falta el campo obligatorio: {e.args[0]}"}), 400

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@estudiante_bp.route("/estudiantes/<string:id_codigo_alumno>", methods=["PUT"])
def actualizar_estudiante(id_codigo_alumno):
    estudiante = Estudiante.query.filter_by(id_codigo_alumno=id_codigo_alumno).first()

    if estudiante is None:
        return jsonify({"error": "Estudiante no encontrado"}), 404

    data = request.get_json()

    if not data:
        return jsonify({"error": "No se enviaron datos"}), 400

    try:
        estudiante.tipo_doc_id = data["tipo_doc_id"]
        estudiante.num_dni = data["num_dni"]
        estudiante.apellido_pat = data["apellido_pat"]
        estudiante.apellido_mat = data["apellido_mat"]
        estudiante.nombres = data["nombres"]
        estudiante.sexo = data["sexo"]
        estudiante.fecha_nac = data["fecha_nac"]
        estudiante.nacionalidad = data.get("nacionalidad")
        estudiante.estado_civil = data["estado_civil"]
        estudiante.correo_inst = data["correo_inst"]
        estudiante.correo_per = data["correo_per"]
        estudiante.distrito_domicilio = data["distrito_domicilio"]
        estudiante.identi_etnica = data["identi_etnica"]
        estudiante.lengua_nativa = data.get("lengua_nativa")
        estudiante.idioma_extranjero = data.get("idioma_extranjero")
        estudiante.telefono_fijo = data["telefono_fijo"]
        estudiante.telefono_movil = data["telefono_movil"]

        estudiante.id_colegio = data.get("id_colegio")
        estudiante.id_movilidad = data.get("id_movilidad")
        estudiante.id_beca = data.get("id_beca")
        estudiante.id_discapacidad = data.get("id_discapacidad")
        estudiante.id_ubigeo = data.get("id_ubigeo")

        db.session.commit()

        return jsonify(serializar_estudiante(estudiante)), 200

    except KeyError as e:
        db.session.rollback()
        return jsonify({"error": f"Falta el campo obligatorio: {e.args[0]}"}), 400

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@estudiante_bp.route("/estudiantes/<string:id_codigo_alumno>", methods=["PATCH"])
def actualizar_parcial_estudiante(id_codigo_alumno):
    estudiante = Estudiante.query.filter_by(id_codigo_alumno=id_codigo_alumno).first()

    if estudiante is None:
        return jsonify({"error": "Estudiante no encontrado"}), 404

    data = request.get_json()

    if not data:
        return jsonify({"error": "No se enviaron datos"}), 400

    try:
        campos = [
            "tipo_doc_id", "num_dni", "apellido_pat", "apellido_mat", "nombres",
            "sexo", "fecha_nac", "nacionalidad", "estado_civil", "correo_inst",
            "correo_per", "distrito_domicilio", "identi_etnica", "lengua_nativa",
            "idioma_extranjero", "telefono_fijo", "telefono_movil", "id_colegio",
            "id_movilidad", "id_beca", "id_discapacidad", "id_ubigeo",
        ]

        for campo in campos:
            if campo in data:
                setattr(estudiante, campo, data[campo])

        db.session.commit()

        return jsonify(serializar_estudiante(estudiante)), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# ======================================================================
# CARGA DE EXCEL
# ======================================================================
#
# ESPECIFICACION_COLUMNAS es la única fuente de verdad: de aquí salen
# el tipo de conversión, si la columna es obligatoria y la longitud
# máxima permitida (tomada de models.py, que es lo que Postgres valida
# de verdad — en un par de columnas el largo real del modelo difiere
# del que tenías en tu tabla, lo dejo indicado abajo).
#
# obligatorio:
#   True         -> nunca puede venir vacío
#   False        -> puede venir vacío
#   "condicional"-> depende de otra columna (se valida aparte, ver
#                   _validar_reglas_condicionales)

ESPECIFICACION_COLUMNAS = {
    # --- Estudiante ---
    "Código del alumno":                       {"tipo": "codigo", "ancho": 8, "max_len": 8,  "obligatorio": True},
    "Tipo de documento de identidad":          {"tipo": "texto",  "max_len": 4,  "obligatorio": True},
    "Número de documento de identidad":        {"tipo": "codigo", "ancho": None, "max_len": 20, "obligatorio": False},
    "Apellido paterno":                        {"tipo": "texto",  "max_len": 100, "obligatorio": False},
    "Apellido materno":                        {"tipo": "texto",  "max_len": 100, "obligatorio": False},
    "Nombres":                                 {"tipo": "texto",  "max_len": 50, "obligatorio": True},
    "Sexo":                                    {"tipo": "texto",  "max_len": 1,  "obligatorio": True},
    "Fecha de nacimiento":                     {"tipo": "fecha",  "obligatorio": False},
    "Nacionalidad":                            {"tipo": "texto",  "max_len": 15, "obligatorio": False},
    "Estado civil":                            {"tipo": "texto",  "max_len": 1,  "obligatorio": False},
    "Correo institucional":                    {"tipo": "texto",  "max_len": 50, "obligatorio": False},
    "Correo personal":                         {"tipo": "texto",  "max_len": 50, "obligatorio": False},
    "Distrito del domicilio":                  {"tipo": "texto",  "max_len": 50, "obligatorio": True},
    "Identidad Étnica":                        {"tipo": "texto",  "max_len": 20, "obligatorio": False},
    "Lengua nativa":                           {"tipo": "texto",  "max_len": 20, "obligatorio": False},
    "Idioma extranjero":                       {"tipo": "texto",  "max_len": 20, "obligatorio": False},
    "Teléfono fijo":                           {"tipo": "codigo", "ancho": None, "max_len": 25, "obligatorio": False},
    "Teléfono móvil":                          {"tipo": "codigo", "ancho": None, "max_len": 25,  "obligatorio": False},

    # --- Colegio ---
    "Colegio-procedencia":                     {"tipo": "codigo", "ancho": None, "max_len": 6,  "obligatorio": False},
    "Tipo colegio de procedencia":             {"tipo": "texto",  "max_len": 15, "obligatorio": False},
    "Año en que concluyó la secundaria":       {"tipo": "entero", "obligatorio": False},
    "Nombre del colegio de procedencia":       {"tipo": "texto",  "max_len": 100, "obligatorio": False},
    "Distrito del colegio de procedencia":     {"tipo": "texto",  "max_len": 40, "obligatorio": False},

    # --- Discapacidad (condicional: ver _validar_reglas_condicionales) ---
    "¿Es discapacitado?":                      {"tipo": "texto",  "max_len": 2,  "obligatorio": True},
    "Tipo de discapacidad":                    {"tipo": "texto",  "max_len": 50, "obligatorio": "condicional"},

    # --- Movilidad (opcional) ---
    "Es estudiante de Movilidad estudiantil":  {"tipo": "texto",  "max_len": 15, "obligatorio": False},

    # --- Ubigeo ---
    "País de nacimiento":                      {"tipo": "texto",  "max_len": 100, "obligatorio": True},
    "Departamento de nacimiento":               {"tipo": "texto",  "max_len": 100, "obligatorio": True},
    "Provincia de nacimiento":                 {"tipo": "texto",  "max_len": 100, "obligatorio": False},
    "Distrito de nacimiento":                  {"tipo": "texto",  "max_len": 100, "obligatorio": False},
    # --- Facultad / Programa / Especialidad ---
    "Código de facultad":                      {"tipo": "codigo", "ancho": 2, "max_len": 2,  "obligatorio": True},
    "Nombre de facultad":                      {"tipo": "texto",  "max_len": 100, "obligatorio": True},
    "Código de programa":                      {"tipo": "codigo", "ancho": 3, "max_len": 3,  "obligatorio": True},
    "Nombre de programa o carrera":            {"tipo": "texto",  "max_len": 300, "obligatorio": True},
    # Especialidad es condicional: hay programas sin especialidad (ver proyecto)
    "Código de especialidad":                  {"tipo": "codigo", "ancho": 2, "max_len": 2,  "obligatorio": "condicional"},
    "Nombre de especialidad":                  {"tipo": "texto",  "max_len": 100, "obligatorio": "condicional"},

    # --- Sede / Local (opcionales) ---
    "Sede":                                    {"tipo": "texto",  "max_len": 120, "obligatorio": False},
    "Local":                                   {"tipo": "texto",  "max_len": 50, "obligatorio": False},

    # --- Ingreso ---
    "Tipo de preparación":                     {"tipo": "texto",  "max_len": 6,  "obligatorio": False},
    # OJO: tu tabla decía VARCHAR(20), pero el modelo real usa String(50).
    "Modalidad de ingreso":                    {"tipo": "texto",  "max_len": 100, "obligatorio": True},
    "Periodo de ingreso":                      {"tipo": "periodo", "max_len": 5, "obligatorio": False},

    # --- Matrícula ---
    "Nivel":                                   {"tipo": "texto",  "max_len": 10, "obligatorio": False},
    "Modalidad de estudio (presencial, semipresencial)": {"tipo": "texto", "max_len": 120, "obligatorio": False},
    "Periodo de matrícula":                    {"tipo": "periodo", "max_len": 5, "obligatorio": True},
    "Régimen de matrícula (Anual, semestral)": {"tipo": "texto",  "max_len": 1,  "obligatorio": True},
    "Ciclo/año de estudios":                   {"tipo": "entero", "obligatorio": False},
    "Permanencia":                             {"tipo": "texto",  "max_len": 10, "obligatorio": True},
    "Primer periodo de matrícula":             {"tipo": "periodo", "max_len": 5, "obligatorio": True},
    "Créditos matriculados en el semestre":    {"tipo": "entero", "obligatorio": True},
    "Créditos acumulados":                     {"tipo": "entero", "obligatorio": False},
    "Cursos matriculados":                     {"tipo": "entero", "obligatorio": False},
    "Nota promedio / Promedio ponderado acumulado": {"tipo": "numerico", "obligatorio": True},
    "Ranking":                                 {"tipo": "entero", "obligatorio": False},

    # --- Beca (opcional: el FK en Estudiante es nullable) ---
    "Tipo de Beca":                            {"tipo": "texto",  "max_len": 100, "obligatorio": False},
}


# ----------------------------------------------------------------------
# Conversores
# ----------------------------------------------------------------------

def limpiar_texto(valor):
    """Convierte un valor a texto limpio.
    Los valores vacíos se convierten en None.
    """
    if pd.isna(valor):
        return None

    valor = str(valor).strip()

    return valor if valor != "" else None


def convertir_entero(valor):
    """Convierte valores como 7.0 -> 7, 168.0 -> 168."""
    if pd.isna(valor):
        return None

    try:
        return int(float(valor))
    except (ValueError, TypeError):
        return None


def convertir_numerico(valor):
    """Convierte valores numéricos de Excel a float."""
    if pd.isna(valor):
        return None

    try:
        return float(valor)
    except (ValueError, TypeError):
        return None


def convertir_codigo(valor, ancho=None):
    """
    Convierte códigos de Excel a texto.
    Conserva ceros a la izquierda cuando corresponde.
    """
    texto = limpiar_texto(valor)

    if texto is None:
        return None

    # Ejemplo: 20.0 -> "20"
    if texto.replace(".", "", 1).isdigit() and texto.endswith(".0"):
        texto = str(int(float(texto)))

    if ancho:
        texto = texto.zfill(ancho)

    return texto


def convertir_periodo(valor):
    """Convierte 20231.0 -> '20231'."""

    if pd.isna(valor):
        return None

    try:
        return str(int(float(valor)))
    except (ValueError, TypeError):
        return limpiar_texto(valor)


def convertir_fecha(valor):
    """Convierte una fecha de Excel a date."""
    if pd.isna(valor):
        return None

    ts = pd.to_datetime(valor, dayfirst=True, errors="coerce")

    if pd.isna(ts):
        return None

    return ts.date()


def convertir_none(valor):
    if valor is None:
        return None
    if pd.isna(valor):
        return None
    if hasattr(valor, "item"):      # numpy.int64 / float64 -> int / float
        valor = valor.item()
    if isinstance(valor, float) and valor.is_integer():
        return int(valor)
    return valor




CONVERSORES = {
    "texto": lambda v, spec: limpiar_texto(v),
    "entero": lambda v, spec: convertir_entero(v),
    "numerico": lambda v, spec: convertir_numerico(v),
    "codigo": lambda v, spec: convertir_codigo(v, spec.get("ancho")),
    "periodo": lambda v, spec: convertir_periodo(v),
    "fecha": lambda v, spec: convertir_fecha(v),
}


def _dtype_lectura_excel():
    """Fuerza a texto (dtype=str) las columnas 'codigo' y las de teléfono
    al leer el Excel, para que pandas no las convierta antes de tiempo a
    float y se coman los ceros a la izquierda (el bug del 00110455)."""
    return {
        columna: str
        for columna, spec in ESPECIFICACION_COLUMNAS.items()
        if spec["tipo"] in ("codigo", "periodo")
    }


def _limpiar_dataframe(df):
    """Aplica el conversor correspondiente a cada columna presente."""
    for columna, spec in ESPECIFICACION_COLUMNAS.items():
        if columna in df.columns:
            conversor = CONVERSORES[spec["tipo"]]
            df[columna] = df[columna].apply(lambda v, s=spec, c=conversor: c(v, s))
    return df


def _validar_columnas_presentes(df):
    faltantes = [c for c in ESPECIFICACION_COLUMNAS if c not in df.columns]
    return faltantes


def _validar_obligatorios(df):
    """Columnas marcadas como obligatorio=True (no las 'condicional')."""
    errores = {}
    for columna, spec in ESPECIFICACION_COLUMNAS.items():
        if spec["obligatorio"] is True and columna in df.columns:
            cantidad = int(df[columna].isna().sum())
            if cantidad > 0:
                errores[columna] = cantidad
    return errores


def _validar_longitudes(df):
    """Valida que los valores no superen la longitud máxima definida."""
    errores = {}

    for columna, spec in ESPECIFICACION_COLUMNAS.items():
        max_len = spec.get("max_len")

        if max_len and columna in df.columns:

            serie = df[columna]

            # Ignorar valores vacíos
            demasiado_largo = (
                serie.notna()
                & (serie.astype(str).str.len() > max_len)
            )

            cantidad = int(demasiado_largo.sum())

            if cantidad > 0:
                errores[columna] = {
                    "max_len": max_len,
                    "cantidad": cantidad,
                    "ejemplos": serie[demasiado_largo].head(5).tolist()
                }

    return errores


def _validar_reglas_condicionales(df):
    """
    - Si '¿Es discapacitado?' es 'SI', 'Tipo de discapacidad' es obligatorio.
    - 'Código de especialidad' y 'Nombre de especialidad' deben venir juntos
      (ambos vacíos o ambos con valor), porque hay programas sin especialidad.
    """
    errores = {}

    if "¿Es discapacitado?" in df.columns and "Tipo de discapacidad" in df.columns:
        es_si = df["¿Es discapacitado?"].str.upper().eq("SI")
        falta_tipo = es_si & df["Tipo de discapacidad"].isna()
        if falta_tipo.any():
            errores["Tipo de discapacidad"] = (
                f"{int(falta_tipo.sum())} fila(s) marcadas como discapacitado='SI' "
                "sin 'Tipo de discapacidad'"
            )

    return errores


# ----------------------------------------------------------------------
# Obtener-o-crear genérico para catálogos
# ----------------------------------------------------------------------
# ================================================================
# NORMALIZACIÓN PARA DETECCIÓN DE POSIBLES DUPLICADOS
# ================================================================
def normalizar_nombre_entidad(valor):
    """
    Normaliza un nombre para comparar posibles duplicados.

    Esta función NO modifica el valor original del Excel.
    Solo se utiliza para comparar.
    """

    if valor is None or pd.isna(valor):
        return None

    texto = str(valor).strip().upper()

    # Quitar tildes
    import unicodedata

    texto = unicodedata.normalize(
        "NFD",
        texto
    )

    texto = "".join(
        caracter
        for caracter in texto
        if unicodedata.category(caracter) != "Mn"
    )

    # Normalizar guiones
    texto = texto.replace("-", " ")

    # Eliminar espacios repetidos
    texto = " ".join(texto.split())

    return texto


def normalizar_colegios_automaticamente(df):
    """
    Corrige automáticamente variantes de escritura equivalentes
    de colegios.

    Ejemplos:
        JOSÉ MARÍA ARGUEDAS
        JOSE MARIA ARGUEDAS
        José María Arguedas

    Se consideran el mismo colegio porque, después de normalizar,
    tienen el mismo nombre y distrito.

    La corrección se realiza solo en memoria sobre el DataFrame.
    No modifica directamente el archivo Excel original.
    """

    nombre_col = "Nombre del colegio de procedencia"
    distrito_col = "Distrito del colegio de procedencia"

    if nombre_col not in df.columns or distrito_col not in df.columns:
        return df, []

    colegios = []

    for indice, fila in df.iterrows():

        nombre = fila.get(nombre_col)
        distrito = fila.get(distrito_col)

        if (
            nombre is None
            or pd.isna(nombre)
            or str(nombre).strip() == ""
        ):
            continue

        nombre_normalizado = normalizar_nombre_entidad(nombre)
        distrito_normalizado = normalizar_nombre_entidad(distrito)

        colegios.append({
            "indice": indice,
            "nombre_original": str(nombre).strip(),
            "distrito_original": (
                str(distrito).strip()
                if distrito is not None and not pd.isna(distrito)
                else None
            ),
            "nombre_normalizado": nombre_normalizado,
            "distrito_normalizado": distrito_normalizado
        })

    # Agrupar por nombre y distrito normalizados
    grupos = {}

    for colegio in colegios:

        clave = (
            colegio["nombre_normalizado"],
            colegio["distrito_normalizado"]
        )

        grupos.setdefault(clave, []).append(colegio)

    correcciones = []

    # Aplicar corrección automática
    for grupo in grupos.values():

        nombres = [
            colegio["nombre_original"]
            for colegio in grupo
        ]

        nombres_unicos = list(dict.fromkeys(nombres))

        # Si todos ya son exactamente iguales, no hacer nada
        if len(nombres_unicos) <= 1:
            continue

        # Elegir como nombre oficial el que aparece más veces
        frecuencia = {}

        for nombre in nombres:
            frecuencia[nombre] = frecuencia.get(nombre, 0) + 1

        nombre_canonico = max(
            frecuencia,
            key=frecuencia.get
        )

        for colegio in grupo:

            nombre_actual = colegio["nombre_original"]

            if nombre_actual != nombre_canonico:

                df.at[
                    colegio["indice"],
                    nombre_col
                ] = nombre_canonico

                correcciones.append({
                    "fila_excel": int(colegio["indice"]) + 2,
                    "valor_anterior": nombre_actual,
                    "valor_nuevo": nombre_canonico,
                    "distrito": colegio["distrito_original"]
                })

    return df, correcciones


# ----------------------------------------------------------------------
# ANÁLISIS DE CALIDAD DE DATOS
# ----------------------------------------------------------------------

def analizar_calidad_datos(df):
    """
    Analiza el DataFrame y devuelve un reporte de inconsistencias.
    NO modifica la base de datos.
    """

    reporte = []

    # ==============================================================
    # 1. CÓDIGO DE ALUMNO
    # ==============================================================

    columna = "Código del alumno"

    if columna in df.columns:

        mascara = (
            df[columna].isna()
            | (df[columna].astype(str).str.len() != 8)
        )

        for indice in df.index[mascara]:

            valor = df.loc[indice, columna]

            # Si está vacío
            if valor is None:
                mensaje = "El código del alumno está vacío."
                sugerencia = "Ingresar un código de 8 dígitos."

            else:
                valor = str(valor)

                if valor.isdigit() and len(valor) < 8:
                    sugerencia = valor.zfill(8)
                    mensaje = (
                        f"El código tiene {len(valor)} dígitos "
                        "y debería tener 8."
                    )
                else:
                    sugerencia = None
                    mensaje = (
                        "El código del alumno no cumple "
                        "con el formato de 8 dígitos."
                    )

            reporte.append({
                "fila_excel": int(indice) + 2,
                "campo": columna,
                "valor_actual": valor,
                "tipo": "CRÍTICO",
                "mensaje": mensaje,
                "sugerencia": sugerencia,
                "accion": "CORREGIR"
            })

    # ==============================================================
    # 2. DNI
    # ==============================================================

    columna = "Número de documento de identidad"

    if columna in df.columns:

        mascara = (
            df[columna].notna()
            & (df[columna].astype(str).str.len() > 20)
        )

        for indice in df.index[mascara]:

            valor = df.loc[indice, columna]

            reporte.append({
                "fila_excel": int(indice) + 2,
                "campo": columna,
                "valor_actual": valor,
                "tipo": "CRÍTICO",
                "mensaje": "El documento supera los 20 caracteres.",
                "sugerencia": None,
                "accion": "CORREGIR"
            })

    # ==============================================================
    # 3. CAMPOS OBLIGATORIOS
    # ==============================================================

    errores_obligatorios = _validar_obligatorios(df)

    for campo, cantidad in errores_obligatorios.items():

        filas = df.index[df[campo].isna()]

        for indice in filas:

            reporte.append({
                "fila_excel": int(indice) + 2,
                "campo": campo,
                "valor_actual": None,
                "tipo": "CRÍTICO",
                "mensaje": "Campo obligatorio vacío.",
                "sugerencia": "Completar el campo.",
                "accion": "CORREGIR"
            })

    # ==============================================================
    # 4. LONGITUDES MÁXIMAS
    # ==============================================================

    errores_longitud = _validar_longitudes(df)

    for campo, detalle in errores_longitud.items():

        serie = df[campo]

        mascara = (
            serie.notna()
            & (serie.astype(str).str.len() > detalle["max_len"])
        )

        for indice in df.index[mascara]:

            valor = df.loc[indice, campo]

            reporte.append({
                "fila_excel": int(indice) + 2,
                "campo": campo,
                "valor_actual": valor,
                "tipo": "CRÍTICO",
                "mensaje": (
                    f"El valor supera la longitud máxima "
                    f"permitida de {detalle['max_len']} caracteres."
                ),
                "sugerencia": "Revisar y corregir el valor.",
                "accion": "CORREGIR"
            })

    # ==============================================================
    # 5. REGLAS CONDICIONALES
    # ==============================================================

    errores_condicionales = _validar_reglas_condicionales(df)

    if errores_condicionales:

        for campo, mensaje in errores_condicionales.items():

            reporte.append({
                "fila_excel": None,
                "campo": campo,
                "valor_actual": None,
                "tipo": "ADVERTENCIA",
                "mensaje": mensaje,
                "sugerencia": "Revisar los datos relacionados.",
                "accion": "REVISAR"
            })

    # ==============================================================
    # 6. POSIBLES COLEGIOS DUPLICADOS
    # ==============================================================

    nombre_col = "Nombre del colegio de procedencia"
    distrito_col = "Distrito del colegio de procedencia"

    if (
        nombre_col in df.columns
        and distrito_col in df.columns
    ):

        colegios = []

        # ----------------------------------------------------------
        # 6.1 Crear estructura normalizada
        # ----------------------------------------------------------

        for indice, fila in df.iterrows():

            nombre_original = fila.get(nombre_col)
            distrito_original = fila.get(distrito_col)

            # Si no hay nombre de colegio, no se analiza
            if (
                nombre_original is None
                or pd.isna(nombre_original)
                or str(nombre_original).strip() == ""
            ):
                continue

            nombre_normalizado = normalizar_nombre_entidad(
                nombre_original
            )

            distrito_normalizado = normalizar_nombre_entidad(
                distrito_original
            )

            colegios.append({
                "indice": indice,
                "fila_excel": int(indice) + 2,
                "nombre_original": str(nombre_original),
                "distrito_original": (
                    str(distrito_original)
                    if distrito_original is not None
                    and not pd.isna(distrito_original)
                    else None
                ),
                "nombre_normalizado": nombre_normalizado,
                "distrito_normalizado": distrito_normalizado
            })

        # ----------------------------------------------------------
        # 6.2 Agrupar por nombre + distrito normalizados
        # ----------------------------------------------------------

        grupos = {}

        for colegio in colegios:

            clave = (
                colegio["nombre_normalizado"],
                colegio["distrito_normalizado"]
            )

            grupos.setdefault(
                clave,
                []
            ).append(colegio)

        # ----------------------------------------------------------
        # 6.3 Detectar variantes de escritura
        # ----------------------------------------------------------

        for clave, grupo in grupos.items():

            if len(grupo) <= 1:
                continue

            # Nombres originales diferentes
            nombres_originales = sorted(
                set(
                    str(colegio["nombre_original"]).strip()
                    for colegio in grupo
                )
            )

            # ------------------------------------------------------
            # Si todos tienen exactamente el mismo nombre,
            # NO es una variante.
            #
            # Solo significa que varios estudiantes pertenecen
            # al mismo colegio.
            # ------------------------------------------------------

            if len(nombres_originales) <= 1:
                continue

            # ------------------------------------------------------
            # Determinar el nombre que aparece más veces
            # ------------------------------------------------------

            frecuencia = {}

            for colegio in grupo:

                nombre = colegio["nombre_original"]

                frecuencia[nombre] = (
                    frecuencia.get(nombre, 0) + 1
                )

            nombre_sugerido = max(
                frecuencia,
                key=frecuencia.get
            )

            # ------------------------------------------------------
            # Generar observaciones
            # ------------------------------------------------------

            for colegio in grupo:

                nombre_actual = colegio["nombre_original"]

                # El que ya coincide con la sugerencia no necesita
                # corrección.
                if nombre_actual == nombre_sugerido:
                    continue

                reporte.append({

                    "fila_excel": colegio["fila_excel"],

                    "campo": nombre_col,

                    "valor_actual": nombre_actual,

                    "tipo": "POSIBLE_DUPLICADO",

                    "mensaje": (
                        "El nombre del colegio presenta una "
                        "posible variante de escritura que "
                        "coincide con otro colegio del mismo distrito."
                    ),

                    "sugerencia": nombre_sugerido,

                    "distrito": colegio["distrito_original"],

                    "accion": "CONFIRMAR_CORRECCION",

                    "posibles_coincidencias": nombres_originales
                })


    # ==============================================================
    # FINAL DEL ANÁLISIS
    # ==============================================================

    resumen = {}
    for inconsistencia in reporte:
        clave = (
            inconsistencia.get("campo"),
            inconsistencia.get("tipo"),
            inconsistencia.get("mensaje"),
        )
        grupo = resumen.setdefault(
            clave,
            {
                "campo": inconsistencia.get("campo"),
                "tipo": inconsistencia.get("tipo"),
                "mensaje": inconsistencia.get("mensaje"),
                "sugerencia": inconsistencia.get("sugerencia"),
                "filas": [],
                "cantidad": 0,
            },
        )
        grupo["cantidad"] += 1
        fila_excel = inconsistencia.get("fila_excel")
        if fila_excel is not None and fila_excel not in grupo["filas"]:
            grupo["filas"].append(fila_excel)

    if reporte:
        estado = "NO_APTO"
    else:
        estado = "APTO"

    return {
        "estado": estado,
        "total_inconsistencias": len(reporte),
        "inconsistencias": reporte,
        "resumen_inconsistencias": list(resumen.values()),
    }


def _valor_previsualizacion(valor):
    if valor is None:
        return None

    try:
        if pd.isna(valor):
            return None
    except (TypeError, ValueError):
        pass

    if hasattr(valor, "item"):
        valor = valor.item()

    if hasattr(valor, "isoformat"):
        return valor.isoformat()

    return valor


def _crear_vista_previa(df, inconsistencias, limite=10):
    inconsistencias_por_fila = {}
    for inconsistencia in inconsistencias:
        fila_excel = inconsistencia.get("fila_excel")
        if fila_excel is not None:
            inconsistencias_por_fila.setdefault(fila_excel, []).append(
                inconsistencia
            )

    columnas = [
        "Código del alumno",
        "Número de documento de identidad",
        "Apellido paterno",
        "Apellido materno",
        "Nombres",
        "Nombre de facultad",
        "Nombre de programa o carrera",
        "Ciclo/año de estudios",
        "Modalidad de ingreso",
    ]

    filas = []
    for indice, fila in df.head(limite).iterrows():
        fila_excel = int(indice) + 2
        problemas = inconsistencias_por_fila.get(fila_excel, [])
        nombre = " ".join(
            str(_valor_previsualizacion(fila.get(columna)) or "")
            for columna in (
                "Apellido paterno",
                "Apellido materno",
                "Nombres",
            )
        ).strip()

        filas.append({
            "fila_excel": fila_excel,
            "codigo_alumno": _valor_previsualizacion(
                fila.get("Código del alumno")
            ),
            "documento": _valor_previsualizacion(
                fila.get("Número de documento de identidad")
            ),
            "nombre": nombre,
            "facultad": _valor_previsualizacion(
                fila.get("Nombre de facultad")
            ),
            "programa": _valor_previsualizacion(
                fila.get("Nombre de programa o carrera")
            ),
            "ciclo": _valor_previsualizacion(
                fila.get("Ciclo/año de estudios")
            ),
            "modalidad_ingreso": _valor_previsualizacion(
                fila.get("Modalidad de ingreso")
            ),
            "estado": "Observado" if problemas else "Apto",
            "inconsistencias": len(problemas),
        })

    return {
        "columnas": [
            {
                "clave": columna,
                "nombre": columna,
            }
            for columna in columnas
            if columna in df.columns
        ],
        "filas": filas,
        "mostradas": len(filas),
    }

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


def obtener_o_crear(modelo, filtros, extra=None, cambios=None):
    """Busca un registro por 'filtros'; si no existe lo crea con
    filtros + extra. filtros debe identificar de forma única el registro."""
    instancia = modelo.query.filter_by(**filtros).first()
    if instancia is None:
        instancia = modelo(**{**filtros, **(extra or {})})
        db.session.add(instancia)
        db.session.flush()  # necesario para obtener el PK autogenerado
        if cambios is not None:
            clave = next(
                columna.name
                for columna in modelo.__table__.primary_key.columns
            )
            cambios.append({
                "tabla": modelo.__tablename__,
                "clave_registro": str(getattr(instancia, clave)),
                "operacion": "creado",
                "valores_anteriores": None,
                "valores_nuevos": _snapshot_modelo(instancia),
            })
    return instancia


def _procesar_fila(fila):
    """Resuelve/crea todos los catálogos de una fila y crea/actualiza
    Estudiante -> Ingreso -> Matricula. Se asume que la fila ya pasó
    limpieza y validación."""

    cambios = []

    # ---------- Colegio ----------
    colegio = None

    colegio_procedencia = convertir_none(
        fila.get("Colegio-procedencia")
    )

    if colegio_procedencia is not None:

        colegio = obtener_o_crear(
            Colegio,
            filtros={
                "nomb_colegio": convertir_none(
                    fila.get("Nombre del colegio de procedencia")
                ),
                "distrito_colegio": convertir_none(
                    fila.get("Distrito del colegio de procedencia")
                ),
            },
            extra={
                "colegio_procedencia": convertir_none(
                    fila.get("Colegio-procedencia")
                ),
                "tipo_procedencia": convertir_none(
                    fila.get("Tipo colegio de procedencia")
                ),
            },
            cambios=cambios,
        )

    # ---------- Ubigeo ----------
    ubigeo = obtener_o_crear(
        Ubigeo,
        filtros={
            "pais_nac": fila["País de nacimiento"],
            "dep_nac": fila["Departamento de nacimiento"],
            "provincia_nac": fila.get("Provincia de nacimiento"),
            "distrito_nac": fila.get("Distrito de nacimiento"),
        },
        cambios=cambios,
    )

    # ---------- Discapacidad (opcional) ----------
    discapacidad = None
    tipo_discapacidad = convertir_none(
        fila.get("Tipo de discapacidad")
    )

    discapacidad_si_no = convertir_none(
        fila.get("¿Es discapacitado?")
    )

    if tipo_discapacidad is not None and discapacidad_si_no is not None:
        discapacidad = obtener_o_crear(
            Discapacidad,
            filtros={
                "tipo_discapacidad": tipo_discapacidad,
                "discapacidad_si_no": discapacidad_si_no,
            },
            cambios=cambios,
        )

    # ---------- Movilidad (opcional) ----------
    movilidad = None
    if fila.get("Es estudiante de Movilidad estudiantil"):
        movilidad = obtener_o_crear(
            Movilidad,
            filtros={"nomb_movilidad": fila["Es estudiante de Movilidad estudiantil"]},
            cambios=cambios,
        )

    # ---------- Beca (opcional) ----------
    beca = None
    if fila.get("Tipo de Beca"):
        beca = obtener_o_crear(
            Beca,
            filtros={"nomb_beca": fila["Tipo de Beca"]},
            cambios=cambios,
        )

    # ---------- Facultad ----------
    facultad = db.session.get(Facultad, fila["Código de facultad"])
    if facultad is None:
        facultad = Facultad(
            id_facultad=fila["Código de facultad"],
            nomb_facultad=fila["Nombre de facultad"],
        )
        db.session.add(facultad)
        db.session.flush()
        cambios.append({
            "tabla": Facultad.__tablename__,
            "clave_registro": str(facultad.id_facultad),
            "operacion": "creado",
            "valores_anteriores": None,
            "valores_nuevos": _snapshot_modelo(facultad),
        })

    # ---------- Programa ----------
    programa = obtener_o_crear(
        Programa,
        filtros={"cod_prog": fila["Código de programa"], "id_facultad": facultad.id_facultad},
        extra={"nombre_prog": fila["Nombre de programa o carrera"]},
        cambios=cambios,
    )

    # ---------- Especialidad ----------
    especialidad = None

    codigo_especialidad = convertir_none(
        fila.get("Código de especialidad")
    )

    nombre_especialidad = convertir_none(
        fila.get("Nombre de especialidad")
    )

    # Si el código está vacío
    if codigo_especialidad is None:
        codigo_especialidad = "V"

    # Si el nombre está vacío
    if nombre_especialidad is None:
        nombre_especialidad = "Estudios Generales"

    especialidad = obtener_o_crear(
        Especialidad,
        filtros={
            "codigo_especialidad": codigo_especialidad,
            "id_prog": programa.id_prog
        },
        extra={
            "nomb_especialidad": nombre_especialidad
        },
        cambios=cambios,
    )
    
    # ---------- Sede (opcional) ----------
    sede = None
    if fila.get("Sede"):
        sede = obtener_o_crear(
            Sede,
            filtros={"nomb_sede": fila["Sede"]},
            cambios=cambios,
        )

    # ---------- Local (opcional, informativo — no está enlazado a Ingreso) ----------
    if fila.get("Local"):
        obtener_o_crear(
            Local,
            filtros={"nomb_local": fila["Local"], "id_sede": sede.id_sede if sede else None},
            cambios=cambios,
        )

    # ---------- Estudiante (crear o actualizar) ----------
    estudiante = db.session.get(Estudiante, fila["Código del alumno"])
    datos_estudiante = {
        "tipo_doc_id": convertir_none(
            fila.get("Tipo de documento de identidad")
        ),
        "num_dni": convertir_none(
            fila.get("Número de documento de identidad")
        ),
        "apellido_pat": convertir_none(
        fila.get("Apellido paterno")
        ),

        "apellido_mat": convertir_none(
            fila.get("Apellido materno")
        ),

        "nombres": convertir_none(
            fila.get("Nombres")
        ),

        "sexo": convertir_none(
            fila.get("Sexo")
        ),

        "fecha_nac": convertir_none(
            fila.get("Fecha de nacimiento")
        ),

        "nacionalidad": convertir_none(
            fila.get("Nacionalidad")
        ),

        "estado_civil": convertir_none(
            fila.get("Estado civil")
        ),

        "correo_inst": convertir_none(
            fila.get("Correo institucional")
        ),

        "correo_per": convertir_none(
            fila.get("Correo personal")
        ),

        "distrito_domicilio": convertir_none(
            fila.get("Distrito del domicilio")
        ),

        "identi_etnica": convertir_none(
            fila.get("Identidad Étnica")
        ),

        "lengua_nativa": convertir_none(
            fila.get("Lengua nativa")
        ),

        "idioma_extranjero": convertir_none(
            fila.get("Idioma extranjero")
        ),

        "telefono_fijo": convertir_none(
            fila.get("Teléfono fijo")
        ),

        "telefono_movil": convertir_none(
            fila.get("Teléfono móvil")
        ),

        "anio_fin_sec": convertir_none(
            fila.get("Año en que concluyó la secundaria")
        ),

        "id_colegio": colegio.id_colegio if colegio else None,

        "id_movilidad": movilidad.id_movilidad if movilidad else None,

        "id_beca": beca.id_beca if beca else None,

        "id_discapacidad": discapacidad.id_discapacidad
            if discapacidad else None,

        "id_ubigeo": ubigeo.id_ubigeo
            if ubigeo else None,
    }

    estudiante_nuevo = estudiante is None
    valores_anteriores_estudiante = (
        None if estudiante_nuevo else _snapshot_modelo(estudiante)
    )

    if estudiante_nuevo:
        estudiante = Estudiante(id_codigo_alumno=fila["Código del alumno"], **datos_estudiante)
        db.session.add(estudiante)
    else:
        for campo, valor in datos_estudiante.items():
            setattr(estudiante, campo, valor)
    db.session.flush()

    valores_nuevos_estudiante = _snapshot_modelo(estudiante)
    if (
        estudiante_nuevo
        or valores_anteriores_estudiante != valores_nuevos_estudiante
    ):
        cambios.append({
            "tabla": Estudiante.__tablename__,
            "clave_registro": estudiante.id_codigo_alumno,
            "operacion": "creado" if estudiante_nuevo else "modificado",
            "valores_anteriores": valores_anteriores_estudiante,
            "valores_nuevos": valores_nuevos_estudiante,
        })

    # ---------- Ingreso (natural: alumno + periodo de ingreso) ----------
    periodo_ingreso = convertir_none(
        fila["Periodo de ingreso"]
    )

    ingreso_existente = Ingreso.query.filter_by(
        id_codigo_alumno=estudiante.id_codigo_alumno,
        periodo_ingreso=periodo_ingreso,
    ).first()

    ingreso = obtener_o_crear(
        Ingreso,
        filtros={
            "id_codigo_alumno": estudiante.id_codigo_alumno,
            "periodo_ingreso": periodo_ingreso,
        },
        extra={
            "tipo_preparacion": convertir_none(
                fila["Tipo de preparación"]
            ),
            "modalidad_ingreso": convertir_none(
                fila["Modalidad de ingreso"]
            ),
            "id_prog": programa.id_prog,
            "id_especialidad": especialidad.id_especialidad
            if especialidad else None,
            "id_sede": sede.id_sede
            if sede else None,
        },
        cambios=cambios,
    )

    if ingreso_existente is None:
        cambios.append({
            "tabla": Ingreso.__tablename__,
            "clave_registro": str(ingreso.id_ingreso),
            "operacion": "creado",
            "valores_anteriores": None,
            "valores_nuevos": _snapshot_modelo(ingreso),
        })

    # ---------- Matrícula ----------
    periodo_mat = convertir_none(
        fila["Periodo de matrícula"]
    )

    # Datos de la matrícula
    datos_matricula = {
        "nivel": convertir_none(
            fila.get("Nivel")
        ),
        "modalidad_estudio": convertir_none(
            fila.get("Modalidad de estudio (presencial, semipresencial)")
        ),
        "regimen_matricula": convertir_none(
            fila["Régimen de matrícula (Anual, semestral)"]
        ),
        "ciclo": convertir_none(
            fila["Ciclo/año de estudios"]
        ),
        "permanencia": convertir_none(
            fila["Permanencia"]
        ),
        "primer_mat": convertir_none(
            fila["Primer periodo de matrícula"]
        ),
        "creditos_acum_sem": convertir_none(
            fila["Créditos matriculados en el semestre"]
        ),
        "creditos_acum_total": convertir_none(
            fila["Créditos acumulados"]
        ),
        "cursos_mat_cat": convertir_none(
            fila.get("Cursos matriculados")
        ),
        "promedio_pond": convertir_none(
            fila["Nota promedio / Promedio ponderado acumulado"]
        ),
        "ranking": convertir_none(
            fila.get("Ranking")
        ),
    }

    print(
        "DEBUG créditos acumulados:",
        repr(datos_matricula["creditos_acum_total"]),
        type(datos_matricula["creditos_acum_total"])
    )

    # ---------------------------------------------------------
    # Buscar matrículas existentes para el mismo ingreso y periodo
    # ---------------------------------------------------------
    matriculas_existentes = Matricula.query.filter_by(
        id_ingreso=ingreso.id_ingreso,
        periodo_mat=periodo_mat
    ).all()

    # ---------------------------------------------------------
    # Comprobar si ya existe una matrícula EXACTAMENTE igual
    # ---------------------------------------------------------
    matricula_igual = None

    for matricula_existente in matriculas_existentes:

        datos_iguales = all(
            getattr(matricula_existente, campo) == valor
            for campo, valor in datos_matricula.items()
        )

        if datos_iguales:
            matricula_igual = matricula_existente
            break

    # ---------------------------------------------------------
    # Si ya existe exactamente la misma fila:
    # NO crear otra
    # ---------------------------------------------------------
    if matricula_igual is not None:

        print(
            "Matrícula duplicada exactamente. "
            "No se crea otro registro:",
            ingreso.id_ingreso,
            periodo_mat
        )

    # ---------------------------------------------------------
    # Si existe la misma combinación pero los datos son diferentes:
    # CREAR una nueva matrícula
    # ---------------------------------------------------------
    else:

        matricula = Matricula(
            id_ingreso=ingreso.id_ingreso,
            periodo_mat=periodo_mat,
            **datos_matricula,
        )

        db.session.add(matricula)

        print(
            "Nueva matrícula creada:",
            ingreso.id_ingreso,
            periodo_mat
        )

        db.session.flush()
        cambios.append({
            "tabla": Matricula.__tablename__,
            "clave_registro": str(matricula.id_matricula),
            "operacion": "creado",
            "valores_anteriores": None,
            "valores_nuevos": _snapshot_modelo(matricula),
        })

    return cambios


@estudiante_bp.route("/estudiantes/cargar-excel", methods=["POST"])
def cargar_excel():

    try:

        # ============================================================
        # 1. RECIBIR ARCHIVO
        # ============================================================

        if "archivo" not in request.files:

            return jsonify({
                "estado": "ERROR",
                "error": "No se recibió ningún archivo."
            }), 400

        archivo = request.files["archivo"]

        if archivo.filename == "":

            return jsonify({
                "estado": "ERROR",
                "error": "No se seleccionó ningún archivo."
            }), 400

        if not archivo.filename.lower().endswith(
            (".xlsx", ".xls")
        ):

            return jsonify({
                "estado": "ERROR",
                "error": (
                    "El archivo debe tener formato "
                    "Excel (.xlsx o .xls)."
                )
            }), 400

        # ============================================================
        # 2. LEER EXCEL
        #
        # Se fuerzan determinados tipos para evitar que pandas
        # elimine ceros a la izquierda.
        # ============================================================

        df = pd.read_excel(
            archivo,
            dtype=_dtype_lectura_excel()
        )

        # Limpiar espacios de los nombres de las columnas

        df.columns = df.columns.str.strip()

        # ============================================================
        # 3. VALIDAR ARCHIVO VACÍO
        # ============================================================

        if df.empty:

            return jsonify({
                "estado": "ERROR",
                "error": "El archivo Excel está vacío."
            }), 400

        # ============================================================
        # 4. VALIDAR COLUMNAS OBLIGATORIAS
        # ============================================================

        faltantes = _validar_columnas_presentes(df)

        if faltantes:

            return jsonify({

                "estado": "ERROR",

                "error": (
                    "El archivo no contiene todas "
                    "las columnas obligatorias."
                ),

                "columnas_faltantes": faltantes

            }), 400

        # ============================================================
        # 5. LIMPIAR Y CONVERTIR DATAFRAME
        # ============================================================

        df = _limpiar_dataframe(df)

        # ============================================================
        # 5.1 NORMALIZAR AUTOMÁTICAMENTE COLEGIOS
        # ============================================================

        df, correcciones_automaticas = normalizar_colegios_automaticamente(df)

        # Convertir NaN / NaT a None
        df = df.astype(object).where(
            df.notna(),
            None
        )

        # ============================================================
        # 6. ANALIZAR CALIDAD DE DATOS
        #
        # IMPORTANTE:
        # Aquí todavía NO se modifica la base de datos.
        # ============================================================

        reporte = analizar_calidad_datos(df)

        reporte["archivo"] = archivo.filename
        reporte["total_filas"] = len(df)
        reporte["vista_previa"] = _crear_vista_previa(
            df,
            reporte["inconsistencias"],
        )
        reporte["correcciones_automaticas"] = correcciones_automaticas

        # ============================================================
        # 8. INDICAR QUÉ DEBE HACER EL USUARIO
        # ============================================================

        if reporte["estado"] == "APTO":

            reporte["siguiente_paso"] = (
                "El archivo está apto para continuar "
                "con la validación final y posterior carga."
            )

        else:

            reporte["siguiente_paso"] = (
                "Debe corregir las inconsistencias "
                "detectadas antes de guardar los datos "
                "en la base de datos."
            )

        # ============================================================
        # 9. RESPUESTA
        #
        # NO HACEMOS:
        #
        # _procesar_fila(...)
        # db.session.commit()
        #
        # porque todavía estamos en la etapa de análisis.
        # ============================================================

        return jsonify(reporte), 200

    # ================================================================
    # ERROR GENERAL
    # ================================================================

    except Exception as e:

        db.session.rollback()

        import traceback

        traceback_completo = traceback.format_exc()

        print(
            "========== ERROR EN ANÁLISIS DE EXCEL =========="
        )

        print(traceback_completo)

        print(
            "================================================="
        )

        return jsonify({

            "estado": "ERROR",

            "error": type(e).__name__,

            "detalle": str(e),

            "mensaje": (
                "Ocurrió un error durante "
                "el análisis del archivo."
            )

        }), 500


@estudiante_bp.route(
    "/estudiantes/confirmar-carga",
    methods=["POST"]
)
def confirmar_carga():

    fila_excel = None

    try:
        # ============================================================
        # 1. RECIBIR Y VALIDAR EL ARCHIVO
        # ============================================================

        if "archivo" not in request.files:
            return jsonify({
                "estado": "ERROR",
                "error": "No se recibió ningún archivo."
            }), 400

        archivo = request.files["archivo"]

        if archivo.filename == "":
            return jsonify({
                "estado": "ERROR",
                "error": "No se seleccionó ningún archivo."
            }), 400

        if not archivo.filename.lower().endswith(
            (".xlsx", ".xls")
        ):
            return jsonify({
                "estado": "ERROR",
                "error": (
                    "El archivo debe tener formato "
                    "Excel (.xlsx o .xls)."
                )
            }), 400

        # ============================================================
        # 2. LEER EL EXCEL
        # ============================================================

        df = pd.read_excel(
            archivo,
            dtype=_dtype_lectura_excel()
        )

        df.columns = df.columns.str.strip()

        if df.empty:
            return jsonify({
                "estado": "ERROR",
                "error": "El archivo Excel está vacío."
            }), 400

        # ============================================================
        # 3. VALIDAR COLUMNAS OBLIGATORIAS
        # ============================================================

        faltantes = _validar_columnas_presentes(df)

        if faltantes:
            return jsonify({
                "estado": "ERROR",
                "error": (
                    "El archivo no contiene todas "
                    "las columnas obligatorias."
                ),
                "columnas_faltantes": faltantes
            }), 400

        # ============================================================
        # 4. LIMPIAR Y NORMALIZAR LOS DATOS
        # ============================================================

        df = _limpiar_dataframe(df)

        df, correcciones_automaticas = (
            normalizar_colegios_automaticamente(df)
        )

        # Convertir NaN y NaT a None
        df = df.astype(object).where(
            df.notna(),
            None
        )

        # ============================================================
        # 5. VALIDAR LA CALIDAD ANTES DE GUARDAR
        # ============================================================

        reporte = analizar_calidad_datos(df)

        if reporte["estado"] != "APTO":
            return jsonify({
                "estado": "NO_APTO",
                "mensaje": (
                    "La carga fue cancelada porque el archivo "
                    "presenta inconsistencias."
                ),
                "archivo": archivo.filename,
                "reporte": reporte,
                "correcciones_automaticas": (
                    correcciones_automaticas
                )
            }), 422

        # ============================================================
        # 6. CARGAR LOS REGISTROS EN POSTGRESQL
        # ============================================================

        filas_procesadas = 0
        cambios_carga = []

        try:
            for indice, fila in df.iterrows():

                fila_excel = int(indice) + 2

                cambios_carga.extend(_procesar_fila(fila))

                filas_procesadas += 1

            # Registrar la operación de carga en el historial.
            historial = HistorialCarga(
                nombre_archivo=archivo.filename,
                tipo_planilla="Estudiantes",
                total_filas=len(df),
                registros_procesados=filas_procesadas,
                inconsistencias=0,
                estado="Completado",
                observaciones=None
            )

            db.session.add(historial)
            historial.cambios.extend(
                HistorialCargaCambio(**cambio)
                for cambio in cambios_carga
            )

            # Confirmar estudiantes e historial en la misma transacción.
            db.session.commit()

        except Exception as e:
            db.session.rollback()

            return jsonify({
                "estado": "ERROR",
                "mensaje": (
                    "La carga fue cancelada. "
                    "No se confirmaron los cambios "
                    "de esta transacción."
                ),
                "fila_excel": fila_excel,
                "detalle": str(e)
            }), 500

        # ============================================================
        # 7. RESPUESTA EXITOSA
        # ============================================================

        return jsonify({
            "estado": "EXITOSO",
            "mensaje": (
                "Los datos se cargaron correctamente "
                "en PostgreSQL."
            ),
            "archivo": archivo.filename,
            "filas_procesadas": filas_procesadas,
            "correcciones_automaticas": (
                correcciones_automaticas
            ),
            "total_correcciones": len(
                correcciones_automaticas
            )
        }), 201

    except Exception as e:
        db.session.rollback()

        return jsonify({
            "estado": "ERROR",
            "mensaje": "Ocurrió un error durante la carga.",
            "fila_excel": fila_excel,
            "detalle": str(e)
        }), 500
