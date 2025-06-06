"""
Extensiones de Flask para el sistema de gestión de servicio técnico.
Este módulo inicializa y configura todas las extensiones necesarias para la aplicación.

Extensiones incluidas:
- SQLAlchemy: ORM para la base de datos
- LoginManager: Gestión de autenticación
- Migrate: Migraciones de base de datos
- Mail: Envío de correos
- CSRFProtect: Protección contra CSRF
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from markupsafe import Markup

# Inicializar extensiones con configuración lazy
db = SQLAlchemy()  # Base de datos principal
login_manager = LoginManager()  # Sistema de autenticación
migrate = Migrate()  # Sistema de migraciones
mail = Mail()  # Sistema de correos
csrf = CSRFProtect()  # Protección CSRF

def nl2br(value):
    """
    Filtro Jinja2 para convertir saltos de línea en etiquetas HTML <br>.
    
    Args:
        value (str): Texto a convertir
        
    Returns:
        Markup: Texto HTML seguro con los saltos de línea convertidos
    """
    if not value:
        return ""
    return Markup(value.replace('\n', '<br>\n'))

def init_app(app):
    """
    Inicializa todas las extensiones con la aplicación Flask.
    
    Args:
        app (Flask): Instancia de la aplicación Flask
        
    Esta función:
    1. Inicializa cada extensión con la app
    2. Configura el sistema de login
    3. Registra filtros personalizados de Jinja2
    """
    # Inicializar cada extensión
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    csrf.init_app(app)
    
    # Configurar el sistema de login
    login_manager.login_view = 'auth.login'  # Vista para el login
    login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'
    login_manager.login_message_category = 'info'  # Categoría para los mensajes flash
    
    # Registrar filtros personalizados de Jinja2
    app.jinja_env.filters['nl2br'] = nl2br  # Convertir \n a <br>
