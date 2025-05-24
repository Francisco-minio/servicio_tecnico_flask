import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime

def setup_logger(app):
    # Crear directorio de logs si no existe
    log_dir = os.path.join(app.root_path, 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Configurar el formato del log
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    )

    # Log para errores
    error_log = os.path.join(log_dir, 'error.log')
    error_file_handler = RotatingFileHandler(
        error_log, maxBytes=10485760, backupCount=10
    )
    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.setFormatter(formatter)

    # Log para accesos
    access_log = os.path.join(log_dir, 'access.log')
    access_file_handler = RotatingFileHandler(
        access_log, maxBytes=10485760, backupCount=10
    )
    access_file_handler.setLevel(logging.INFO)
    access_file_handler.setFormatter(formatter)

    # Configurar logger de la aplicación
    app.logger.setLevel(logging.INFO)
    app.logger.addHandler(error_file_handler)
    app.logger.addHandler(access_file_handler)

    # Log para debugging en desarrollo
    if app.debug:
        debug_log = os.path.join(log_dir, 'debug.log')
        debug_file_handler = RotatingFileHandler(
            debug_log, maxBytes=10485760, backupCount=10
        )
        debug_file_handler.setLevel(logging.DEBUG)
        debug_file_handler.setFormatter(formatter)
        app.logger.addHandler(debug_file_handler)

def log_info(app, message):
    app.logger.info(message)

def log_error(app, message, exc_info=None):
    app.logger.error(message, exc_info=exc_info)

def log_access(app, endpoint, user=None):
    message = f"Acceso a {endpoint}"
    if user:
        message += f" por usuario {user}"
    app.logger.info(message) 