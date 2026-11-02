from flask import Flask
from flask_cors import CORS

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

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )
