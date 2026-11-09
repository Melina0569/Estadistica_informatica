from datetime import datetime

from flask import Blueprint, jsonify, request
from sqlalchemy import Integer, Numeric, String, func, or_

from extensions import db
from models.correcciones import (
    AuditoriaCorreccion,
    DocumentoPendiente,
    CorreccionReporte,
    ReporteValidacion,
)
from models.estudiantes import Estudiante, Ingreso, Matricula
from models.historial_cargas import HistorialCarga


correcciones_bp = Blueprint("correcciones_bp", __name__)

MODELOS_CORREGIBLES = {
    "estudiante": (Estudiante, "id_codigo_alumno", {
        "tipo_doc_id", "num_dni", "apellido_pat", "apellido_mat", "nombres",
        "sexo", "fecha_nac", "anio_fin_sec", "nacionalidad", "estado_civil",
        "correo_inst", "correo_per", "distrito_domicilio", "identi_etnica",
        "lengua_nativa", "idioma_extranjero", "telefono_fijo", "telefono_movil",
    }),
    "ingreso": (Ingreso, "id_ingreso", {
        "tipo_preparacion", "modalidad_ingreso", "periodo_ingreso",
    }),
    "matricula": (Matricula, "id_matricula", {
        "nivel", "modalidad_estudio", "periodo_mat", "regimen_matricula",
        "ciclo", "permanencia", "primer_mat", "creditos_acum_sem",
        "creditos_acum_total", "cursos_mat_cat", "promedio_pond", "ranking",
    }),
}

INCONSISTENCIAS = (
    (Estudiante, "estudiante", "nombres", "Nombres obligatorios vacíos", "CRÍTICO", "vacío"),
    (Estudiante, "estudiante", "distrito_domicilio", "Distrito de domicilio vacío", "ALTO", "vacío"),
    (Ingreso, "ingreso", "modalidad_ingreso", "Modalidad de ingreso vacía", "ALTO", "vacío"),
    (Matricula, "matricula", "periodo_mat", "Periodo de matrícula vacío", "CRÍTICO", "vacío"),
    (Matricula, "matricula", "regimen_matricula", "Régimen de matrícula vacío", "CRÍTICO", "vacío"),
    (Matricula, "matricula", "primer_mat", "Primer periodo de matrícula vacío", "CRÍTICO", "vacío"),
    (Matricula, "matricula", "modalidad_estudio", "Modalidad de estudio vacía", "ALTO", "vacío"),
    (Matricula, "matricula", "creditos_acum_sem", "Créditos matriculados en el semestre", "CRÍTICO", "vacío"),
    (Matricula, "matricula", "promedio_pond", "Nota promedio / Promedio ponderado acumulado", "CRÍTICO", "vacío"),
    (Matricula, "matricula", "permanencia", "Permanencia", "CRÍTICO", "largo"),
)


def _condicion_inconsistencia(columna, tipo):
    if tipo == "largo":
        return func.length(columna) > 10
    if isinstance(columna.type, (Integer, Numeric)):
        return columna.is_(None)
    if isinstance(columna.type, String):
        return or_(columna.is_(None), columna == "")
    return columna.is_(None)


def _carga_activa():
    return (
        HistorialCarga.query
        .join(ReporteValidacion, ReporteValidacion.id_carga == HistorialCarga.id_carga)
        .filter(HistorialCarga.estado.in_(("Analizada", "En corrección", "Apta")))
        .order_by(HistorialCarga.id_carga.desc())
        .first()
    )


@correcciones_bp.get("/api/correcciones/reporte-activo")
def reporte_activo():
    carga = _carga_activa()
    if not carga:
        return jsonify({"reporte": None, "id_carga": None})
    reporte = ReporteValidacion.query.filter_by(id_carga=carga.id_carga).first()
    return jsonify({
        "id_carga": carga.id_carga,
        "archivo": carga.nombre_archivo,
        "reporte": {
            "estado": "APTO" if reporte.estado == "apta" else "NO_APTO",
            "total_filas": reporte.total_filas,
            "total_inconsistencias": reporte.total_inconsistencias,
            "resumen_inconsistencias": reporte.resumen_inconsistencias or [],
            "id_carga": reporte.id_carga,
        } if reporte else None,
    })


@correcciones_bp.get("/api/correcciones/inconsistencias")
def listar_inconsistencias():
    limite = min(max(request.args.get("limite", 100, type=int), 1), 500)
    grupos = []
    carga = _carga_activa()
    reporte = (
        ReporteValidacion.query.filter_by(id_carga=carga.id_carga).first()
        if carga else None
    )

    if reporte:
        grupos = [{
            "clave": f"archivo:{indice}",
            "tabla": "archivo",
            "campo": item.get("campo", ""),
            "etiqueta": item.get("campo", "Inconsistencia del archivo"),
            "severidad": item.get("tipo", "CRÍTICO"),
            "cantidad": item.get("cantidad", 0),
            "muestra": [],
            "origen": "archivo",
            "archivo": reporte.nombre_archivo,
            "detalle_disponible": True,
            "id_carga": reporte.id_carga,
        } for indice, item in enumerate(reporte.resumen_inconsistencias or [])
        ]

    return jsonify({
        "total": sum(grupo["cantidad"] for grupo in grupos),
        "tipos": len(grupos),
        "inconsistencias": grupos,
        "reportes": [{
            "archivo": reporte.nombre_archivo,
            "total_filas": reporte.total_filas,
            "total_inconsistencias": reporte.total_inconsistencias,
            "creado_en": reporte.creado_en.isoformat(),
            "id_carga": reporte.id_carga,
            "estado": reporte.estado,
        }] if reporte else [],
        "id_carga": reporte.id_carga if reporte else None,
    })


@correcciones_bp.post("/api/correcciones/reporte-validacion")
def guardar_reporte_validacion():
    datos = request.get_json(silent=True) or {}
    archivo = str(datos.get("archivo", "")).strip()
    reporte = datos.get("reporte")
    if not archivo or not isinstance(reporte, dict):
        return jsonify({"error": "El archivo y el reporte son obligatorios."}), 400

    try:
        carga = HistorialCarga(
            nombre_archivo=archivo,
            total_filas=int(reporte.get("total_filas") or 0),
            inconsistencias=int(reporte.get("total_inconsistencias") or 0),
            estado="Analizada",
        )
        db.session.add(carga)
        db.session.flush()
        db.session.add(ReporteValidacion(
            id_carga=carga.id_carga,
            nombre_archivo=archivo,
            total_filas=int(reporte.get("total_filas") or 0),
            total_inconsistencias=int(reporte.get("total_inconsistencias") or 0),
            resumen_inconsistencias=(
                reporte.get("resumen_inconsistencias")
                if isinstance(reporte.get("resumen_inconsistencias"), list)
                else []
            ),
            estado="en_correccion" if reporte.get("estado") == "NO_APTO" else "apta",
        ))
        db.session.commit()
    except (TypeError, ValueError) as error:
        db.session.rollback()
        return jsonify({"error": f"El reporte no tiene un formato válido: {error}"}), 400
    except Exception as error:
        db.session.rollback()
        return jsonify({"error": "No se pudo guardar el reporte de validación.", "detalle": str(error)}), 500
    return jsonify({"mensaje": "Reporte de validación actualizado."})


@correcciones_bp.put("/api/correcciones/reporte-validacion/correccion")
def guardar_correccion_reporte():
    datos = request.get_json(silent=True) or {}
    campo = str(datos.get("campo", "")).strip()
    valor = datos.get("valor")
    motivo = str(datos.get("motivo", "")).strip()
    if not campo or valor is None or not str(valor).strip() or not motivo:
        return jsonify({"error": "Campo, valor y motivo son obligatorios."}), 400

    carga = _carga_activa()
    reporte = (
        ReporteValidacion.query.filter_by(id_carga=carga.id_carga).first()
        if carga else None
    )
    if not reporte:
        return jsonify({"error": "No hay un reporte de archivo pendiente."}), 404

    existente = CorreccionReporte.query.filter_by(
        nombre_archivo=reporte.nombre_archivo,
        huella_archivo=reporte.huella_archivo,
        id_carga=reporte.id_carga,
        campo=campo,
    ).first()
    if existente:
        valor_anterior = existente.valor
        existente.valor = str(valor).strip()
        existente.motivo = motivo
        existente.creado_en = datetime.now()
    else:
        valor_anterior = None
        db.session.add(CorreccionReporte(
            nombre_archivo=reporte.nombre_archivo,
            huella_archivo=reporte.huella_archivo,
            id_carga=reporte.id_carga,
            campo=campo,
            valor=str(valor).strip(),
            motivo=motivo,
        ))
    db.session.add(AuditoriaCorreccion(
        tabla="archivo",
        id_registro=f"carga:{reporte.id_carga}",
        campo=campo,
        valor_anterior=valor_anterior,
        valor_nuevo=str(valor).strip(),
        motivo=motivo,
        usuario=str(datos.get("usuario") or "Administrador"),
    ))
    pendientes = [
        item for item in (reporte.resumen_inconsistencias or [])
        if item.get("campo") != campo
    ]
    reporte.resumen_inconsistencias = pendientes
    reporte.total_inconsistencias = sum(
        int(item.get("cantidad") or 0) for item in pendientes
    )
    reporte.correcciones_pendientes = [
        *(
            item for item in (reporte.correcciones_pendientes or [])
            if item.get("campo") != campo
        ),
        {"campo": campo, "valor": str(valor).strip(), "motivo": motivo},
    ]
    if reporte.total_inconsistencias == 0:
        reporte.estado = "apta"
        carga.estado = "Apta"
    else:
        reporte.estado = "en_correccion"
        carga.estado = "En corrección"
    db.session.commit()
    return jsonify({
        "mensaje": "Corrección pendiente guardada para el archivo.",
        "id_carga": reporte.id_carga,
        "total_inconsistencias": reporte.total_inconsistencias,
        "estado": reporte.estado,
    })


@correcciones_bp.get("/api/correcciones/inconsistencias/detalle")
def detalle_inconsistencias():
    tabla = request.args.get("tabla", "").strip()
    campo = request.args.get("campo", "").strip()
    definicion = MODELOS_CORREGIBLES.get(tabla)
    if not definicion or campo not in {
        "nombres", "distrito_domicilio", "modalidad_ingreso",
        "periodo_mat", "primer_mat", "modalidad_estudio",
        "regimen_matricula", "creditos_acum_sem", "promedio_pond",
        "permanencia",
    }:
        return jsonify({"error": "Componente de inconsistencia no válido."}), 400
    modelo, clave, _ = definicion
    columna = getattr(modelo, campo)
    condicion = _condicion_inconsistencia(
        columna,
        "largo" if campo == "permanencia" else "vacío",
    )
    filas = modelo.query.filter(condicion).all()
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
    try:
        if valor_nuevo is not None and isinstance(columna.type, Integer):
            valor_nuevo = int(valor_nuevo)
        elif valor_nuevo is not None and isinstance(columna.type, Numeric):
            valor_nuevo = columna.type.python_type(valor_nuevo)
        elif valor_nuevo is not None and hasattr(columna.type, "python_type") and columna.type.python_type.__name__ == "date":
            valor_nuevo = datetime.strptime(str(valor_nuevo), "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return jsonify({"error": f"El valor no tiene un formato válido para {campo}."}), 400
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
    pagina = max(request.args.get("pagina", 1, type=int), 1)
    por_pagina = 10
    registros = AuditoriaCorreccion.query.order_by(
        AuditoriaCorreccion.creado_en.desc()
    ).all()
    auditadas = {
        (item.tabla, item.id_registro, item.campo, item.creado_en)
        for item in registros
    }
    for correccion in CorreccionReporte.query.order_by(
        CorreccionReporte.creado_en.desc()
    ).all():
        clave = (
            "archivo",
            f"carga:{correccion.id_carga}",
            correccion.campo,
            correccion.creado_en,
        )
        if clave not in auditadas:
            registros.append(AuditoriaCorreccion(
                tabla="archivo",
                id_registro=f"carga:{correccion.id_carga}",
                campo=correccion.campo,
                valor_anterior=None,
                valor_nuevo=correccion.valor,
                motivo=correccion.motivo,
                creado_en=correccion.creado_en,
            ))
    registros.sort(key=lambda item: item.creado_en, reverse=True)
    total = len(registros)
    inicio = (pagina - 1) * por_pagina
    registros = registros[inicio:inicio + por_pagina]
    return jsonify({
        "auditoria": [{
        "id": item.id_auditoria,
        "tabla": item.tabla,
        "id_registro": item.id_registro,
        "campo": item.campo,
        "anterior": item.valor_anterior,
        "nuevo": item.valor_nuevo,
        "motivo": item.motivo,
        "usuario": item.usuario,
        "creado_en": item.creado_en.isoformat(),
        } for item in registros],
        "pagina": pagina,
        "por_pagina": por_pagina,
        "total": total,
        "paginas": max((total + por_pagina - 1) // por_pagina, 1),
    })


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
