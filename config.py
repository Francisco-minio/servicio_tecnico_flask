import os
from datetime import timedelta

class Config:
    # Configuración básica
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-super-secret'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configuración de la base de datos
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'mysql+pymysql://servicio_tecnico:servicio_tecnico_password@db/ordenes_db'
    
    # Configuración de la sesión
    SESSION_TYPE = 'filesystem'
    SESSION_FILE_DIR = 'flask_session'
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # Configuración de archivos
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max-limit
    
    # Configuración de correo
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')

    # Configuración de cookies para producción
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    REMEMBER_COOKIE_SECURE = True
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = 'Lax'
    CSRF_COOKIE_SECURE = True
    CSRF_COOKIE_HTTPONLY = True
    CSRF_COOKIE_SAMESITE = 'Lax'

    WTF_CSRF_TIME_LIMIT = 3600
    WTF_CSRF_SSL_STRICT = True
    WTF_CSRF_ENABLED = True
    WTF_CSRF_CHECK_DEFAULT = True
    WTF_CSRF_METHODS = ['POST', 'PUT', 'PATCH', 'DELETE']

    LOG_TYPE = os.environ.get('LOG_TYPE', 'stream')
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

    CORREO_ADMIN = 'admin@backupcode.cl'
    CORREO_REPUESTOS = os.environ.get('CORREO_REPUESTOS') or 'franciscominio@backupcode.cl'
    CORREO_PRESUPUESTOS = os.environ.get('CORREO_PRESUPUESTOS') or 'franciscominio@backupcode.cl'

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = True
    
    # Desactivar restricciones de cookies para desarrollo local
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = False
    SESSION_COOKIE_SAMESITE = None
    
    REMEMBER_COOKIE_SECURE = False
    REMEMBER_COOKIE_HTTPONLY = False
    REMEMBER_COOKIE_SAMESITE = None
    
    CSRF_COOKIE_SECURE = False
    CSRF_COOKIE_HTTPONLY = False
    CSRF_COOKIE_SAMESITE = None
    
    WTF_CSRF_SSL_STRICT = False

class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_ECHO = False

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://servicio_tecnico:servicio_tecnico_password@db/ordenes_test_db'
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}