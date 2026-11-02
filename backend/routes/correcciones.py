from datetime import datetime

from flask import Blueprint, jsonify, request
from sqlalchemy import or_

from extensions import db
from models.correcciones import AuditoriaCorreccion, DocumentoPendiente
from models.estudiantes import Estudiante, Ingreso, Matricula


correcciones_bp = Blueprint("correcciones_bp", __name__)

MODELOS_CORREGIBLES = {
    "estudiante": (Estudiante, "id_codigo_alumno", {"num_dni", "apellido_pat", "apellido_mat", "nombres", "correo_inst", "correo_per", "distrito_domicilio"}),
    "ingreso": (Ingreso, "id_ingreso", {"tipo_preparacion", "modalidad_ingreso", "periodo_ingreso"}),
    "matricula": (Matricula, "id_matricula", {"nivel", "modalidad_estudio", "periodo_mat", "regimen_matricula", "ciclo", "permanencia", "primer_mat"}),
}


@correcciones_bp.get("/api/correcciones/inconsistencias")
def listar_inconsistencias():
    limite = min(max(request.args.get("limite", 100, type=int), 1), 500)
    grupos = []

    for modelo, tabla, campo, etiqueta in (
        (Estudiante, "estudiante", "nombres", "Nombres obligatorios vacíos"),
        (Estudiante, "estudiante", "distrito_domicilio", "Distrito de domicilio vacío"),
        (Ingreso, "ingreso", "modalidad_ingreso", "Modalidad de ingreso vacía"),
        (Matricula, "matricula", "periodo_mat", "Periodo de matrícula vacío"),
        (Matricula, "matricula", "primer_mat", "Primer periodo de matrícula vacío"),
        (Matricula, "matricula", "modalidad_estudio", "Modalidad de estudio vacía"),
    ):
        columna = getattr(modelo, campo)
        filas = modelo.query.filter(or_(columna.is_(None), columna == "")).all()
        clave = f"{tabla}:{campo}"
        grupo = {
            "clave": clave,
            "tabla": tabla,
            "campo": campo,
            "etiqueta": etiqueta,
            "severidad": "CRÍTICO" if campo in {"nombres", "periodo_mat", "primer_mat"} else "ALTO",
            "cantidad": len(filas),
            "muestra": [],
        }
        for fila in filas[:5]:
            grupo["muestra"].append({
                "tabla": tabla,
                "id": str(getattr(fila, modelo.__table__.primary_key.columns.keys()[0])),
                "campo": campo,
                "valor": None,
            })
        if grupo["cantidad"]:
            grupos.append(grupo)

    return jsonify({
        "total": sum(grupo["cantidad"] for grupo in grupos),
        "tipos": len(grupos),
        "inconsistencias": grupos,
    })


@correcciones_bp.get("/api/correcciones/inconsistencias/detalle")
def detalle_inconsistencias():
    tabla = request.args.get("tabla", "").strip()
    campo = request.args.get("campo", "").strip()
    definicion = MODELOS_CORREGIBLES.get(tabla)
    if not definicion or campo not in {
        "nombres", "distrito_domicilio", "modalidad_ingreso",
        "periodo_mat", "primer_mat", "modalidad_estudio",
    }:
        return jsonify({"error": "Componente de inconsistencia no válido."}), 400
    modelo, clave, _ = definicion
    columna = getattr(modelo, campo)
    filas = modelo.query.filter(or_(columna.is_(None), columna == "")).all()
    return jsonify({"registros": [{
        "tabla": tabla,
        "id": str(getattr(fila, clave)),
        "campo": campo,
    } for fila in filas]})


@correcciones_bp.put("/api/correcciones/registro")
def corregir_registro():
    datos = request.get_json(silent=True) or {}
    tabla = str(datos.get("tabla", "")).strip()
    campo = str(datos.get("campo", "")).strip()
    identificador = str(datos.get("id", "")).strip()
    motivo = str(datos.get("motivo", "")).strip()
    if not tabla or not campo or not identificador or not motivo:
        return jsonify({"error": "Tabla, campo, id y motivo son obligatorios."}), 400

    definicion = MODELOS_CORREGIBLES.get(tabla)
    if not definicion or campo not in definicion[2]:
        return jsonify({"error": "El campo no está habilitado para corrección manual."}), 400

    modelo, clave, _ = definicion
    try:
        clave_registro = identificador if clave == "id_codigo_alumno" else int(identificador)
    except ValueError:
        return jsonify({"error": "El identificador del registro no es válido."}), 400
    registro = db.session.get(modelo, clave_registro)
    if not registro:
        return jsonify({"error": "No se encontró el registro indicado."}), 404

    valor_nuevo = datos.get("valor")
    columna = getattr(modelo, campo)
    if isinstance(valor_nuevo, str):
        valor_nuevo = valor_nuevo.strip() or None
    valor_anterior = getattr(registro, campo)
    setattr(registro, campo, valor_nuevo)
    db.session.add(AuditoriaCorreccion(
        tabla=tabla,
        id_registro=identificador,
        campo=campo,
        valor_anterior=None if valor_anterior is None else str(valor_anterior),
        valor_nuevo=None if valor_nuevo is None else str(valor_nuevo),
        motivo=motivo,
        usuario=str(datos.get("usuario") or "Administrador"),
    ))
    try:
        db.session.commit()
    except Exception as error:
        db.session.rollback()
        return jsonify({"error": "No se pudo guardar la corrección.", "detalle": str(error)}), 500
    return jsonify({"mensaje": "Corrección guardada y auditada."})


@correcciones_bp.put("/api/correcciones/registros")
def corregir_registros():
    datos = request.get_json(silent=True) or {}
    correcciones = datos.get("correcciones")
    valor_comun = datos.get("valor_comun")
    motivo = str(datos.get("motivo", "")).strip()
    if not isinstance(correcciones, list) or not correcciones:
        return jsonify({"error": "Debe indicar al menos una corrección."}), 400
    if not motivo:
        return jsonify({"error": "El motivo es obligatorio."}), 400

    cambios = []
    try:
        for item in correcciones:
            tabla = str(item.get("tabla", "")).strip()
            campo = str(item.get("campo", "")).strip()
            identificador = str(item.get("id", "")).strip()
            definicion = MODELOS_CORREGIBLES.get(tabla)
            if not definicion or campo not in definicion[2]:
                return jsonify({"error": f"Campo no habilitado: {tabla}.{campo}"}), 400
            modelo, clave, _ = definicion
            clave_registro = identificador if clave == "id_codigo_alumno" else int(identificador)
            registro = db.session.get(modelo, clave_registro)
            if not registro:
                return jsonify({"error": f"No se encontró el registro {tabla} #{identificador}."}), 404
            valor_nuevo = valor_comun if valor_comun is not None else item.get("valor")
            if isinstance(valor_nuevo, str):
                valor_nuevo = valor_nuevo.strip() or None
            valor_anterior = getattr(registro, campo)
            setattr(registro, campo, valor_nuevo)
            cambios.append(AuditoriaCorreccion(
                tabla=tabla,
                id_registro=identificador,
                campo=campo,
                valor_anterior=None if valor_anterior is None else str(valor_anterior),
                valor_nuevo=None if valor_nuevo is None else str(valor_nuevo),
                motivo=motivo,
                usuario=str(datos.get("usuario") or "Administrador"),
            ))
        db.session.add_all(cambios)
        db.session.commit()
    except (ValueError, TypeError):
        db.session.rollback()
        return jsonify({"error": "Uno de los identificadores no es válido."}), 400
    except Exception as error:
        db.session.rollback()
        return jsonify({"error": "No se pudo guardar el conjunto de correcciones.", "detalle": str(error)}), 500
    return jsonify({"mensaje": f"{len(cambios)} corrección(es) guardada(s) y auditada(s)."})


@correcciones_bp.get("/api/correcciones/auditoria")
def listar_auditoria():
    registros = AuditoriaCorreccion.query.order_by(AuditoriaCorreccion.creado_en.desc()).limit(200).all()
    return jsonify({"auditoria": [{
        "id": item.id_auditoria,
        "tabla": item.tabla,
        "id_registro": item.id_registro,
        "campo": item.campo,
        "anterior": item.valor_anterior,
        "nuevo": item.valor_nuevo,
        "motivo": item.motivo,
        "usuario": item.usuario,
        "creado_en": item.creado_en.isoformat(),
    } for item in registros]})


@correcciones_bp.get("/api/correcciones/documentos")
def listar_documentos():
    documentos = DocumentoPendiente.query.order_by(DocumentoPendiente.creado_en.desc()).limit(300).all()
    return jsonify({"documentos": [{
        "id": item.id_documento,
        "codigo_alumno": item.codigo_alumno,
        "tipo_documento": item.tipo_documento,
        "descripcion": item.descripcion,
        "responsable": item.responsable,
        "estado": item.estado,
        "fecha_limite": item.fecha_limite.isoformat() if item.fecha_limite else None,
    } for item in documentos]})


@correcciones_bp.post("/api/correcciones/documentos")
def crear_documento():
    datos = request.get_json(silent=True) or {}
    tipo = str(datos.get("tipo_documento", "")).strip()
    if not tipo:
        return jsonify({"error": "El tipo de documento es obligatorio."}), 400
    fecha = datos.get("fecha_limite")
    try:
        fecha_limite = datetime.strptime(fecha, "%Y-%m-%d").date() if fecha else None
    except ValueError:
        return jsonify({"error": "La fecha límite no tiene un formato válido."}), 400
    documento = DocumentoPendiente(
        codigo_alumno=str(datos.get("codigo_alumno") or "").strip() or None,
        tipo_documento=tipo,
        descripcion=str(datos.get("descripcion") or "").strip() or None,
        responsable=str(datos.get("responsable") or "").strip() or None,
        fecha_limite=fecha_limite,
    )
    db.session.add(documento)
    db.session.commit()
    return jsonify({"id": documento.id_documento, "mensaje": "Documento pendiente registrado."}), 201


@correcciones_bp.patch("/api/correcciones/documentos/<int:id_documento>")
def actualizar_documento(id_documento):
    documento = db.session.get(DocumentoPendiente, id_documento)
    if not documento:
        return jsonify({"error": "No se encontró el documento pendiente."}), 404
    datos = request.get_json(silent=True) or {}
    if "estado" in datos and datos["estado"] not in {"Pendiente", "En revisión", "Completado"}:
        return jsonify({"error": "Estado de documento no válido."}), 400
    for campo in ("estado", "responsable", "descripcion"):
        if campo in datos:
            setattr(documento, campo, str(datos[campo]).strip() or None)
    db.session.commit()
    return jsonify({"mensaje": "Documento actualizado."})
