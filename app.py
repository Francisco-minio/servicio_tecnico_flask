import os
from flask import Flask, render_template, redirect, url_for
from flask_migrate import Migrate
from flask_login import LoginManager, current_user
from flask_wtf.csrf import CSRFProtect
from flask_session import Session
from flask_talisman import Talisman
from extensions import db, mail
from models import Usuario

# Importar configuración
from config import config

# Importar utilidades
from utils.logger import setup_logger
from utils.file_handler import FileHandler

# Importar blueprints
from blueprints.auth import auth_bp
from blueprints.orden import orden_bp
from blueprints.cliente import cliente_bp
from blueprints.admin import admin_bp
from blueprints.cotizacion import cotizacion_bp
from blueprints.perfil import perfil_bp

def create_app(config_name='default'):
    app = Flask(__name__)
    
    # Cargar configuración
    app.config.from_object(config[config_name])
    
    # Inicializar extensiones
    db.init_app(app)
    mail.init_app(app)
    migrate = Migrate(app, db)
    csrf = CSRFProtect(app)
    Session(app)
    Talisman(app)
    
    # Configurar Login Manager
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))
    
    # Configurar logger
    setup_logger(app)
    
    # Inicializar manejador de archivos
    app.file_handler = FileHandler(app)
    
    # Registrar blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(orden_bp, url_prefix='/orden')
    app.register_blueprint(cliente_bp, url_prefix='/cliente')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(cotizacion_bp, url_prefix='/cotizacion')
    app.register_blueprint(perfil_bp, url_prefix='/perfil')
    
    # Rutas principales
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            if current_user.rol == 'admin':
                return redirect(url_for('admin.dashboard'))
            else:
                return redirect(url_for('orden.listar_ordenes'))
        return redirect(url_for('auth.login'))
    
    # Crear directorios necesarios al iniciar la aplicación
    with app.app_context():
        os.makedirs('static/uploads/images', exist_ok=True)
        os.makedirs('static/uploads/documents', exist_ok=True)
        os.makedirs('static/uploads/temp', exist_ok=True)
        os.makedirs('static/pdfs', exist_ok=True)
        os.makedirs('logs', exist_ok=True)
    
    return app

if __name__ == '__main__':
    app = create_app(os.getenv('FLASK_ENV', 'development'))
    app.run(debug=True)
