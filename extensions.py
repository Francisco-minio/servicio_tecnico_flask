from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from markupsafe import Markup

# Inicializar extensiones
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
mail = Mail()
csrf = CSRFProtect()

def nl2br(value):
    """Convierte saltos de línea en etiquetas <br>"""
    if not value:
        return ""
    return Markup(value.replace('\n', '<br>\n'))

def init_app(app):
    """Inicializa todas las extensiones"""
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    csrf.init_app(app)
    
    # Configurar el login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'
    login_manager.login_message_category = 'info'
    
    # Registrar filtros personalizados
    app.jinja_env.filters['nl2br'] = nl2br
