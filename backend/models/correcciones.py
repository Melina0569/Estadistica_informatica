from datetime import datetime

from extensions import db


class DocumentoPendiente(db.Model):
    __tablename__ = "documentos_pendientes"

    id_documento = db.Column(db.Integer, primary_key=True)
    codigo_alumno = db.Column(db.String(8), nullable=True, index=True)
    tipo_documento = db.Column(db.String(120), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    responsable = db.Column(db.String(120), nullable=True)
    estado = db.Column(db.String(20), nullable=False, default="Pendiente")
    fecha_limite = db.Column(db.Date, nullable=True)
    creado_en = db.Column(db.DateTime, nullable=False, default=datetime.now)
    actualizado_en = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)


class AuditoriaCorreccion(db.Model):
    __tablename__ = "auditoria_correcciones"

    id_auditoria = db.Column(db.Integer, primary_key=True)
    tabla = db.Column(db.String(50), nullable=False)
    id_registro = db.Column(db.String(255), nullable=False)
    campo = db.Column(db.String(80), nullable=False)
    valor_anterior = db.Column(db.Text, nullable=True)
    valor_nuevo = db.Column(db.Text, nullable=True)
    motivo = db.Column(db.Text, nullable=False)
    usuario = db.Column(db.String(120), nullable=True)
    creado_en = db.Column(db.DateTime, nullable=False, default=datetime.now)


class ReporteValidacion(db.Model):
    __tablename__ = "reportes_validacion"

    id_reporte = db.Column(db.Integer, primary_key=True)
    id_carga = db.Column(
        db.Integer,
        db.ForeignKey("historial_cargas.id_carga", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    nombre_archivo = db.Column(db.String(255), nullable=False)
    huella_archivo = db.Column(db.String(64), nullable=True, index=True)
    total_filas = db.Column(db.Integer, nullable=False, default=0)
    total_inconsistencias = db.Column(db.Integer, nullable=False, default=0)
    resumen_inconsistencias = db.Column(db.JSON, nullable=False, default=list)
    correcciones_pendientes = db.Column(db.JSON, nullable=False, default=list)
    estado = db.Column(db.String(20), nullable=False, default="analizada")
    creado_en = db.Column(db.DateTime, nullable=False, default=datetime.now)


class CorreccionReporte(db.Model):
    __tablename__ = "correcciones_reportes"

    id_correccion = db.Column(db.Integer, primary_key=True)
    id_carga = db.Column(
        db.Integer,
        db.ForeignKey("historial_cargas.id_carga", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    nombre_archivo = db.Column(db.String(255), nullable=False, index=True)
    huella_archivo = db.Column(db.String(64), nullable=True, index=True)
    campo = db.Column(db.String(150), nullable=False)
    valor = db.Column(db.Text, nullable=False)
    motivo = db.Column(db.Text, nullable=False)
    creado_en = db.Column(db.DateTime, nullable=False, default=datetime.now)
