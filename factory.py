"""
Factory de la aplicación Flask para el sistema de gestión de servicio técnico.
Este módulo implementa el patrón Factory para crear y configurar la aplicación Flask.

Características principales:
- Configuración de seguridad con Talisman
- Sistema de logging con rotación
- Manejo de errores personalizado
- Registro de blueprints
- Configuración de extensiones
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, redirect, url_for, render_template
from flask_migrate import Migrate
from flask_login import LoginManager, current_user
from flask_wtf.csrf import CSRFProtect
from flask_session import Session
from flask_talisman import Talisman
from extensions import db, mail
from models import Usuario
from datetime import timedelta

# Importar configuración
from config import config

# Importar utilidades
from utils.logger import setup_logger
from utils.file_handler import FileHandler

def register_blueprints(app):
    """
    Registra todos los blueprints de la aplicación.
    
    Args:
        app (Flask): Instancia de la aplicación Flask
        
    Esta función:
    1. Importa los blueprints necesarios
    2. Define la configuración de cada blueprint (URL prefix)
    3. Registra cada blueprint en la aplicación
    """
    # Importar blueprints
    from blueprints.auth import auth_bp
    from blueprints.orden import orden_bp
    from blueprints.admin import admin_bp
    from blueprints.cliente import cliente_bp
    from blueprints.cotizacion import cotizacion_bp
    from blueprints.perfil import perfil_bp
    from blueprints.main import main_bp
    from blueprints.usuario import usuario_bp

    # Lista de blueprints con sus configuraciones
    blueprints = [
        main_bp,  # Blueprint principal (sin prefijo)
        auth_bp,  # Autenticación (sin prefijo)
        (orden_bp, {'url_prefix': '/orden'}),  # Gestión de órdenes
        (cliente_bp, {'url_prefix': '/cliente'}),  # Gestión de clientes
        (admin_bp, {'url_prefix': '/admin'}),  # Panel de administración
        (cotizacion_bp, {'url_prefix': '/cotizacion'}),  # Gestión de cotizaciones
        (perfil_bp, {'url_prefix': '/perfil'}),  # Perfil de usuario
        (usuario_bp, {'url_prefix': '/usuarios'})  # Gestión de usuarios
    ]

    # Registrar cada blueprint
    for blueprint in blueprints:
        if isinstance(blueprint, tuple):
            bp, options = blueprint
            app.register_blueprint(bp, **options)
        else:
            app.register_blueprint(blueprint)

def create_app(config_name='development'):
    """
    Crea y configura una instancia de la aplicación Flask.
    
    Args:
        config_name (str): Nombre de la configuración a usar ('development' o 'production')
        
    Returns:
        Flask: Instancia configurada de la aplicación Flask
        
    Esta función:
    1. Crea la aplicación Flask
    2. Carga la configuración según el entorno
    3. Configura la seguridad y el logging
    4. Inicializa las extensiones
    5. Registra los blueprints y rutas
    """
    app = Flask(__name__)
    
    # Configuración básica
    app.config.from_object(config[config_name])
    
    # Configuración del servidor de correo
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.smtp2go.com')
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 2525))
    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')
    app.config['CORREO_ADMIN'] = os.environ.get('CORREO_ADMIN')
    
    # Inicialización de extensiones Flask
    db.init_app(app)  # Base de datos
    mail.init_app(app)  # Sistema de correo
    migrate = Migrate(app, db)  # Migraciones
    csrf = CSRFProtect(app)  # Protección CSRF
    Session(app)  # Manejo de sesiones
    
    # Configuración del sistema de autenticación
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor inicie sesión para acceder a esta página.'
    login_manager.login_message_category = 'warning'
    
    @login_manager.user_loader
    def load_user(user_id):
        """Carga un usuario desde la base de datos por su ID."""
        return Usuario.query.get(int(user_id))
    
    # Manejadores de errores personalizados
    @app.errorhandler(404)
    def not_found_error(error):
        """Maneja errores 404 (Página no encontrada)."""
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        """
        Maneja errores 500 (Error interno).
        Hace rollback de la sesión de base de datos.
        """
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    # Configuración del sistema de logging
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    file_handler = RotatingFileHandler(
        'logs/app.log',
        maxBytes=10240,  # 10KB por archivo
        backupCount=10  # Mantener 10 archivos de backup
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Aplicación iniciada')
    
    # Registrar blueprints
    register_blueprints(app)
    
    # Registrar filtro nl2br para Jinja
    def nl2br(value):
        if not value:
            return ''
        return value.replace('\n', '<br>\n')
    app.jinja_env.filters['nl2br'] = nl2br
    
    return app 