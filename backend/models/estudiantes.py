from extensions import db


class Beca(db.Model):
    __tablename__ = "beca"

    id_beca = db.Column(db.Integer, primary_key=True)
    nomb_beca = db.Column(db.String(100), nullable=False)

    estudiantes = db.relationship(
        "Estudiante",
        back_populates="beca"
    )


class Colegio(db.Model):
    __tablename__ = "colegio"

    id_colegio = db.Column(db.Integer, primary_key=True)
    colegio_procedencia = db.Column(db.String(6), nullable=True)
    tipo_procedencia = db.Column(db.String(15), nullable=True)
    nomb_colegio = db.Column(db.String(100), nullable=True)
    distrito_colegio = db.Column(db.String(40), nullable=True)

    estudiantes = db.relationship(
        "Estudiante",
        back_populates="colegio"
    )


class Discapacidad(db.Model):
    __tablename__ = "discapacidad"

    id_discapacidad = db.Column(db.Integer, primary_key=True)
    tipo_discapacidad = db.Column(db.String(50), nullable=False)
    discapacidad_si_no = db.Column(db.CHAR(2), nullable=False)

    estudiantes = db.relationship(
        "Estudiante",
        back_populates="discapacidad"
    )


class Movilidad(db.Model):
    __tablename__ = "movilidad"

    id_movilidad = db.Column(db.Integer, primary_key=True)
    nomb_movilidad = db.Column(db.String(15), nullable=True)

    estudiantes = db.relationship(
        "Estudiante",
        back_populates="movilidad"
    )


class Ubigeo(db.Model):
    __tablename__ = "ubigeo"

    id_ubigeo = db.Column(db.Integer, primary_key=True)
    pais_nac = db.Column(db.String(100), nullable=False)
    dep_nac = db.Column(db.String(100), nullable=False)
    provincia_nac = db.Column(db.String(100), nullable=True)
    distrito_nac = db.Column(db.String(100), nullable=True)

    estudiantes = db.relationship(
        "Estudiante",
        back_populates="ubigeo"
    )


class Facultad(db.Model):
    __tablename__ = "facultad"

    id_facultad = db.Column(db.String(2), primary_key=True)
    nomb_facultad = db.Column(db.String(100), nullable=False)

    programas = db.relationship(
        "Programa",
        back_populates="facultad"
    )


class Programa(db.Model):
    __tablename__ = "programa"

    id_prog = db.Column(db.Integer, primary_key=True)
    cod_prog = db.Column(db.String(3), nullable=False)
    nombre_prog = db.Column(db.String(300), nullable=False)

    id_facultad = db.Column(
        db.String(2),
        db.ForeignKey("facultad.id_facultad"),
        nullable=True
    )

    facultad = db.relationship(
        "Facultad",
        back_populates="programas"
    )

    especialidades = db.relationship(
        "Especialidad",
        back_populates="programa"
    )

    ingresos = db.relationship(
        "Ingreso",
        back_populates="programa"
    )


class Especialidad(db.Model):
    __tablename__ = "especialidad"

    id_especialidad = db.Column(db.Integer, primary_key=True)
    codigo_especialidad = db.Column(db.String(2), nullable=False)
    nomb_especialidad = db.Column(db.String(100), nullable=False)

    id_prog = db.Column(
        db.Integer,
        db.ForeignKey("programa.id_prog"),
        nullable=True
    )

    programa = db.relationship(
        "Programa",
        back_populates="especialidades"
    )

    ingresos = db.relationship(
        "Ingreso",
        back_populates="especialidad"
    )


class Sede(db.Model):
    __tablename__ = "sede"

    id_sede = db.Column(db.Integer, primary_key=True)
    nomb_sede = db.Column(db.String(120), nullable=True)

    locales = db.relationship(
        "Local",
        back_populates="sede"
    )

    ingresos = db.relationship(
        "Ingreso",
        back_populates="sede"
    )


class Local(db.Model):
    __tablename__ = "local"

    id_local = db.Column(db.Integer, primary_key=True)
    nomb_local = db.Column(db.String(50), nullable=True)

    id_sede = db.Column(
        db.Integer,
        db.ForeignKey("sede.id_sede"),
        nullable=True
    )

    sede = db.relationship(
        "Sede",
        back_populates="locales"
    )


class Estudiante(db.Model):
    __tablename__ = "estudiante"

    id_codigo_alumno = db.Column(db.String(8), primary_key=True)
    tipo_doc_id = db.Column(db.String(4), nullable=False)
    num_dni = db.Column(db.String(20), nullable=True, index=True)
    apellido_pat = db.Column(db.String(100), nullable=True)
    apellido_mat = db.Column(db.String(100), nullable=True)
    nombres = db.Column(db.String(50), nullable=False)
    sexo = db.Column(db.CHAR(1), nullable=False)
    fecha_nac = db.Column(db.Date, nullable=True)
    anio_fin_sec = db.Column(db.Integer, nullable=True)
    nacionalidad = db.Column(db.String(15), nullable=True)
    estado_civil = db.Column(db.CHAR(1), nullable=True)
    correo_inst = db.Column(db.String(50), nullable=True)
    correo_per = db.Column(db.String(50), nullable=True)
    distrito_domicilio = db.Column(db.String(50), nullable=False)
    identi_etnica = db.Column(db.String(20), nullable=True)
    lengua_nativa = db.Column(db.String(20), nullable=True)
    idioma_extranjero = db.Column(db.String(20), nullable=True)
    telefono_fijo = db.Column(db.String(25), nullable=True)
    telefono_movil = db.Column(db.String(25), nullable=True)

    id_colegio = db.Column(
        db.Integer,
        db.ForeignKey("colegio.id_colegio"),
        nullable=True
    )

    id_movilidad = db.Column(
        db.Integer,
        db.ForeignKey("movilidad.id_movilidad"),
        nullable=True
    )

    id_beca = db.Column(
        db.Integer,
        db.ForeignKey("beca.id_beca"),
        nullable=True
    )

    id_discapacidad = db.Column(
        db.Integer,
        db.ForeignKey("discapacidad.id_discapacidad"),
        nullable=True
    )

    id_ubigeo = db.Column(
        db.Integer,
        db.ForeignKey("ubigeo.id_ubigeo"),
        nullable=True
    )

    beca = db.relationship(
        "Beca",
        back_populates="estudiantes"
    )

    colegio = db.relationship(
        "Colegio",
        back_populates="estudiantes"
    )

    discapacidad = db.relationship(
        "Discapacidad",
        back_populates="estudiantes"
    )

    movilidad = db.relationship(
        "Movilidad",
        back_populates="estudiantes"
    )

    ubigeo = db.relationship(
        "Ubigeo",
        back_populates="estudiantes"
    )

    ingresos = db.relationship(
        "Ingreso",
        back_populates="estudiante"
    )


class Ingreso(db.Model):
    __tablename__ = "ingreso"

    id_ingreso = db.Column(db.Integer, primary_key=True)
    tipo_preparacion = db.Column(db.String(6), nullable=True)
    modalidad_ingreso = db.Column(db.String(100), nullable=False)
    periodo_ingreso = db.Column(db.CHAR(5), nullable=True)

    id_codigo_alumno = db.Column(
        db.CHAR(8),
        db.ForeignKey("estudiante.id_codigo_alumno"),
        nullable=True
    )

    id_prog = db.Column(
        db.Integer,
        db.ForeignKey("programa.id_prog"),
        nullable=True
    )

    id_especialidad = db.Column(
        db.Integer,
        db.ForeignKey("especialidad.id_especialidad"),
        nullable=True
    )

    id_sede = db.Column(
        db.Integer,
        db.ForeignKey("sede.id_sede"),
        nullable=True
    )

    estudiante = db.relationship(
        "Estudiante",
        back_populates="ingresos"
    )

    programa = db.relationship(
        "Programa",
        back_populates="ingresos"
    )

    especialidad = db.relationship(
        "Especialidad",
        back_populates="ingresos"
    )

    sede = db.relationship(
        "Sede",
        back_populates="ingresos"
    )

    matriculas = db.relationship(
        "Matricula",
        back_populates="ingreso"
    )


class Matricula(db.Model):
    __tablename__ = "matricula"

    id_matricula = db.Column(db.Integer, primary_key=True)
    nivel = db.Column(db.String(10), nullable=True)
    modalidad_estudio = db.Column(db.String(120), nullable=True)
    periodo_mat = db.Column(db.CHAR(5), nullable=False)
    regimen_matricula = db.Column(db.CHAR(1), nullable=False)
    ciclo = db.Column(db.Integer, nullable=True)
    permanencia = db.Column(db.String(10), nullable=False)
    primer_mat = db.Column(db.CHAR(5), nullable=False)
    creditos_acum_sem = db.Column(db.Integer, nullable=False)
    creditos_acum_total = db.Column(db.Integer, nullable=True)
    cursos_mat_cat = db.Column(db.Integer, nullable=True)
    promedio_pond = db.Column(db.Numeric(5, 3), nullable=False)
    ranking = db.Column(db.Integer, nullable=True)

    id_ingreso = db.Column(
        db.Integer,
        db.ForeignKey("ingreso.id_ingreso"),
        nullable=True
    )

    ingreso = db.relationship(
        "Ingreso",
        back_populates="matriculas"
    )