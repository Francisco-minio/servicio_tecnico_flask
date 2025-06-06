"""
Configuración del sistema de gestión de servicio técnico.
Este módulo define las diferentes configuraciones para los entornos de desarrollo,
producción y pruebas. Utiliza variables de entorno para valores sensibles.
"""

import os
from datetime import timedelta

class Config:
    """
    Configuración base que contiene los valores por defecto y comunes
    para todos los entornos. Las clases específicas heredan de esta.
    """
    
    # Configuración básica de la aplicación
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-super-secret'
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Desactiva el sistema de eventos de SQLAlchemy
    
    # Configuración de la base de datos
    # Soporta MySQL/MariaDB a través de PyMySQL
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'mysql+pymysql://root@localhost/ordenes_db'
    
    # Configuración de la sesión
    # Usa el sistema de archivos para almacenar sesiones
    SESSION_TYPE = 'filesystem'
    SESSION_FILE_DIR = 'flask_session'
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)  # Duración máxima de la sesión
    
    # Configuración de archivos
    # Límites y ubicaciones para la carga de archivos
    UPLOAD_FOLDER = 'static/uploads'  # Directorio para archivos subidos
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # Límite de 16MB por archivo
    
    # Configuración del servidor de correo
    # Soporta cualquier servidor SMTP, configurado por defecto para Gmail
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')

    # Configuración de la impresora Zebra
    # Sistema flexible que soporta múltiples modos de conexión
    ZEBRA_TEST_MODE = os.environ.get('ZEBRA_TEST_MODE', 'True').lower() in ['true', 'on', '1']
    ZEBRA_CONNECTION_TYPE = os.environ.get('ZEBRA_CONNECTION_TYPE', 'pdf')  # Tipos: 'pdf', 'network', 'usb', 'cups'
    ZEBRA_PRINTER_NAME = os.environ.get('ZEBRA_PRINTER_NAME', 'Zebra')  # Nombre de la impresora en CUPS
    ZEBRA_PRINTER_IP = os.environ.get('ZEBRA_PRINTER_IP', 'localhost')  # IP para conexión de red
    ZEBRA_PRINTER_PORT = int(os.environ.get('ZEBRA_PRINTER_PORT', 9100))  # Puerto para conexión de red
    ZEBRA_USB_DEVICE = os.environ.get('ZEBRA_USB_DEVICE',  # Ruta del dispositivo USB
        'USB001' if os.name == 'nt' else '/dev/usb/lp0')
    ZEBRA_LABEL_DIR = os.path.join('static', 'labels')  # Directorio para PDFs temporales

    # Configuración de seguridad para cookies
    # Valores recomendados para producción
    SESSION_COOKIE_SECURE = True  # Solo enviar cookies por HTTPS
    SESSION_COOKIE_HTTPONLY = True  # Prevenir acceso JavaScript a cookies
    SESSION_COOKIE_SAMESITE = 'Lax'  # Protección contra CSRF
    REMEMBER_COOKIE_SECURE = True
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = 'Lax'
    CSRF_COOKIE_SECURE = True
    CSRF_COOKIE_HTTPONLY = True
    CSRF_COOKIE_SAMESITE = 'Lax'

    # Configuración de protección CSRF
    WTF_CSRF_TIME_LIMIT = 3600  # Tiempo de vida del token en segundos
    WTF_CSRF_SSL_STRICT = True  # Requiere HTTPS
    WTF_CSRF_ENABLED = True  # Habilita protección CSRF
    WTF_CSRF_CHECK_DEFAULT = True  # Verifica tokens por defecto
    WTF_CSRF_METHODS = ['POST', 'PUT', 'PATCH', 'DELETE']  # Métodos protegidos

    # Configuración de logging
    LOG_TYPE = os.environ.get('LOG_TYPE', 'stream')  # Tipo de logger (stream/file)
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')  # Nivel de logging

    # Correos administrativos
    CORREO_ADMIN = 'admin@backupcode.cl'  # Correo principal de administración
    CORREO_REPUESTOS = os.environ.get('CORREO_REPUESTOS') or 'franciscominio@backupcode.cl'  # Para solicitudes de repuestos
    CORREO_PRESUPUESTOS = os.environ.get('CORREO_PRESUPUESTOS') or 'franciscominio@backupcode.cl'  # Para solicitudes de presupuestos

class DevelopmentConfig(Config):
    """
    Configuración para el entorno de desarrollo.
    Activa herramientas de depuración y desactiva restricciones de seguridad.
    """
    DEBUG = True  # Activa el modo debug de Flask
    SQLALCHEMY_ECHO = True  # Muestra queries SQL en la consola
    
    # Desactiva restricciones de cookies para desarrollo local
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
    """
    Configuración para el entorno de producción.
    Maximiza la seguridad y el rendimiento.
    """
    DEBUG = False  # Desactiva el modo debug
    SQLALCHEMY_ECHO = False  # Desactiva el logging de SQL

class TestingConfig(Config):
    """
    Configuración para pruebas automatizadas.
    Usa una base de datos separada y desactiva características no necesarias para testing.
    """
    TESTING = True  # Activa el modo de pruebas de Flask
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root@localhost/ordenes_test_db'  # Base de datos de prueba
    WTF_CSRF_ENABLED = False  # Desactiva CSRF para facilitar testing
    SESSION_COOKIE_SECURE = False  # Permite cookies sin HTTPS
    REMEMBER_COOKIE_SECURE = False

# Diccionario para seleccionar la configuración según el entorno
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}