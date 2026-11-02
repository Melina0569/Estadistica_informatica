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
