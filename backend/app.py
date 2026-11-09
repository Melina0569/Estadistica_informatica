from flask import Flask
from flask_cors import CORS
from sqlalchemy import text

from config import Config
from extensions import db
from routes.estudiantes import estudiante_bp
from routes.dashboard import dashboard_bp
from routes.correcciones import correcciones_bp
from models.historial_cargas import HistorialCarga

app = Flask(__name__)
app.config.from_object(Config)

# Permite que el frontend se comunique con Flask
CORS(app)

# Conexión de SQLAlchemy con PostgreSQL
db.init_app(app)

# Registrar rutas de estudiantes
app.register_blueprint(estudiante_bp)
# Registrar rutas del dashboard
app.register_blueprint(dashboard_bp)
app.register_blueprint(correcciones_bp)

with app.app_context():
    db.create_all()
    db.session.execute(text(
        "ALTER TABLE reportes_validacion "
        "ADD COLUMN IF NOT EXISTS correcciones_pendientes JSON"
    ))
    db.session.execute(text(
        "UPDATE reportes_validacion "
        "SET correcciones_pendientes = '[]' "
        "WHERE correcciones_pendientes IS NULL"
    ))
    db.session.execute(text(
        "ALTER TABLE reportes_validacion "
        "ADD COLUMN IF NOT EXISTS huella_archivo VARCHAR(64)"
    ))
    db.session.execute(text(
        "ALTER TABLE correcciones_reportes "
        "ADD COLUMN IF NOT EXISTS huella_archivo VARCHAR(64)"
    ))
    db.session.execute(text(
        "ALTER TABLE historial_cargas "
        "ADD COLUMN IF NOT EXISTS archivo_contenido BYTEA"
    ))
    db.session.execute(text(
        "ALTER TABLE reportes_validacion "
        "ADD COLUMN IF NOT EXISTS id_carga INTEGER"
    ))
    db.session.execute(text(
        "ALTER TABLE reportes_validacion "
        "ADD COLUMN IF NOT EXISTS estado VARCHAR(20) NOT NULL DEFAULT 'analizada'"
    ))
    db.session.execute(text(
        "ALTER TABLE correcciones_reportes "
        "ADD COLUMN IF NOT EXISTS id_carga INTEGER"
    ))
    db.session.commit()

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )
