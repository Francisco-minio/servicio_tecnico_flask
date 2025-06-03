import os
from flask import Flask, redirect, url_for, render_template
from flask_migrate import Migrate
from flask_login import LoginManager, current_user
from flask_wtf.csrf import CSRFProtect
from flask_session import Session
from flask_talisman import Talisman
from extensions import db, mail
from models import Usuario
import logging
from logging.handlers import RotatingFileHandler
from datetime import timedelta

# Importar configuración
from config import config

# Importar utilidades
from utils.logger import setup_logger
from utils.file_handler import FileHandler

def register_blueprints(app):
    """Registra todos los blueprints de la aplicación."""
    # Importar blueprints
    from blueprints.auth import auth_bp
    from blueprints.orden import orden_bp
    from blueprints.admin import admin_bp
    from blueprints.cliente import cliente_bp
    from blueprints.cotizacion import cotizacion_bp
    from blueprints.perfil import perfil_bp

    # Lista de blueprints con sus configuraciones
    blueprints = [
        auth_bp,
        (orden_bp, {'url_prefix': '/orden'}),
        (cliente_bp, {'url_prefix': '/cliente'}),
        (admin_bp, {'url_prefix': '/admin'}),
        (cotizacion_bp, {'url_prefix': '/cotizacion'}),
        (perfil_bp, {'url_prefix': '/perfil'})
    ]

    # Registrar cada blueprint
    for blueprint in blueprints:
        if isinstance(blueprint, tuple):
            bp, options = blueprint
            app.register_blueprint(bp, **options)
        else:
            app.register_blueprint(blueprint)

def create_app(config_name='development'):
    app = Flask(__name__)
    
    # Configuración básica
    if config_name == 'development':
        app.config.from_object('config.DevelopmentConfig')
    else:
        app.config.from_object('config.ProductionConfig')
    
    # Agregar filtro nl2br
    @app.template_filter('nl2br')
    def nl2br_filter(s):
        if s is None:
            return ""
        return s.replace('\n', '<br>')
    
    # Configuración de Talisman (HTTPS y CSP)
    csp = {
        'default-src': [
            '\'self\'',
            '\'unsafe-inline\'',
            '\'unsafe-eval\'',
            'cdn.datatables.net',
            'cdn.jsdelivr.net',
            'fonts.googleapis.com',
            'fonts.gstatic.com',
            'code.jquery.com',
            'localhost:8080'
        ],
        'img-src': ['\'self\'', 'data:', '*'],
        'script-src': [
            '\'self\'',
            '\'unsafe-inline\'',
            '\'unsafe-eval\'',
            'cdn.datatables.net',
            'cdn.jsdelivr.net',
            'code.jquery.com',
            'localhost:8080'
        ],
        'style-src': [
            '\'self\'',
            '\'unsafe-inline\'',
            'cdn.datatables.net',
            'fonts.googleapis.com',
            'cdn.jsdelivr.net'
        ],
        'font-src': ['\'self\'', 'fonts.gstatic.com'],
        'connect-src': [
            '\'self\'',
            'localhost:8080',
            'cdn.datatables.net',
            'https://cdn.datatables.net'
        ]
    }

    permissions_policy = {
        'accelerometer': '()',
        'autoplay': '()',
        'camera': '()',
        'display-capture': '()',
        'encrypted-media': '()',
        'fullscreen': '()',
        'geolocation': '()',
        'gyroscope': '()',
        'magnetometer': '()',
        'microphone': '()',
        'midi': '()',
        'payment': '()',
        'picture-in-picture': '()',
        'publickey-credentials-get': '()',
        'screen-wake-lock': '()',
        'sync-xhr': '()',
        'usb': '()',
        'web-share': '()',
        'xr-spatial-tracking': '()'
    }

    # Configurar Talisman (desactivado en desarrollo)
    if config_name == 'development':
        Talisman(app, force_https=False, content_security_policy=None)
    else:
        Talisman(app)
    
    # Asegurarse de que las variables de entorno de correo estén configuradas
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.smtp2go.com')
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 2525))
    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')
    app.config['CORREO_ADMIN'] = os.environ.get('CORREO_ADMIN')
    
    # Inicializar extensiones
    db.init_app(app)
    mail.init_app(app)
    migrate = Migrate(app, db)
    csrf = CSRFProtect(app)
    Session(app)
    
    # Configurar Login Manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor inicie sesión para acceder a esta página.'
    login_manager.login_message_category = 'warning'
    
    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))
    
    # Configurar manejo de errores
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    # Configurar logger
    setup_logger(app)
    
    # Configurar manejo de archivos
    FileHandler.init_app(app)
    
    # Configurar logging
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Aplicación iniciada')
    
    # Registrar blueprints
    register_blueprints(app)
    
    # Ruta principal
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            if current_user.rol == 'admin':
                return redirect(url_for('admin.dashboard'))
            else:
                return redirect(url_for('orden.listar_ordenes'))
        return redirect(url_for('auth.login'))
    
    return app 