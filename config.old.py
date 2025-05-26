import os
from datetime import timedelta

class Config:
    # Configuración básica
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'mysql+pymysql://root@localhost/ordenes_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configuración de sesión
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Configuración CSRF mejorada
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hora
    WTF_CSRF_SSL_STRICT = True
    WTF_CSRF_ENABLED = True
    WTF_CSRF_CHECK_DEFAULT = True
    WTF_CSRF_METHODS = ['POST', 'PUT', 'PATCH', 'DELETE']
    CSRF_COOKIE_SECURE = True
    CSRF_COOKIE_HTTPONLY = True
    CSRF_COOKIE_SAMESITE = 'Lax'
    
    # Configuración de correo
    MAIL_SERVER = 'smtp.smtp2go.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = 'no-reply@backupcode.cl'
    
    # Configuración de archivos
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx'}
    
    # Configuración de logging
    LOG_TYPE = os.environ.get('LOG_TYPE', 'stream')
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

    # Configuración de seguridad adicionales
    REMEMBER_COOKIE_SECURE = True
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = 'Lax'

    CORREO_ADMIN = 'admin@backupcode.cl'
    CORREO_REPUESTOS = os.environ.get('CORREO_REPUESTOS') or 'franciscominio@backupcode.cl'
    CORREO_PRESUPUESTOS = os.environ.get('CORREO_PRESUPUESTOS') or 'franciscominio@backupcode.cl'

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root@localhost/ordenes_db'
    SQLALCHEMY_ECHO = True
    
    # Desactivar configuraciones de seguridad SSL en desarrollo
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False
    
    # Desactivar restricciones de cookies para desarrollo
    SESSION_COOKIE_SAMESITE = None
    CSRF_COOKIE_SAMESITE = None
    REMEMBER_COOKIE_SAMESITE = None
    
    # Configuraciones adicionales para desarrollo
    WTF_CSRF_SSL_STRICT = False
    SESSION_COOKIE_HTTPONLY = False
    CSRF_COOKIE_HTTPONLY = False
    REMEMBER_COOKIE_HTTPONLY = False

class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'mysql+pymysql://root@localhost/ordenes_db'
    SQLALCHEMY_ECHO = False

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root@localhost/ordenes_test_db'
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
} 