from datetime import datetime

from extensions import db


class HistorialCarga(db.Model):
    __tablename__ = "historial_cargas"

    id_carga = db.Column(
        db.Integer,
        primary_key=True
    )

    nombre_archivo = db.Column(
        db.String(255),
        nullable=False
    )

    fecha_carga = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.now
    )

    tipo_planilla = db.Column(
        db.String(50),
        nullable=False,
        default="Estudiantes"
    )

    total_filas = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    registros_procesados = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    inconsistencias = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    estado = db.Column(
        db.String(30),
        nullable=False,
        default="Analizada"
    )

    observaciones = db.Column(
        db.Text,
        nullable=True
    )

    archivo_contenido = db.Column(
        db.LargeBinary,
        nullable=True
    )

    cambios = db.relationship(
        "HistorialCargaCambio",
        back_populates="carga",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class HistorialCargaCambio(db.Model):
    __tablename__ = "historial_cargas_cambios"

    id_cambio = db.Column(
        db.Integer,
        primary_key=True
    )

    id_carga = db.Column(
        db.Integer,
        db.ForeignKey("historial_cargas.id_carga", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    tabla = db.Column(
        db.String(50),
        nullable=False
    )

    clave_registro = db.Column(
        db.String(255),
        nullable=False
    )

    operacion = db.Column(
        db.String(20),
        nullable=False
    )

    valores_anteriores = db.Column(
        db.JSON,
        nullable=True
    )

    valores_nuevos = db.Column(
        db.JSON,
        nullable=True
    )

    carga = db.relationship(
        "HistorialCarga",
        back_populates="cambios"
    )