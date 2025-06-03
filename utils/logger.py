import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime
from flask import request

def setup_logger(app):
    # Crear directorio de logs si no existe
    log_dir = os.path.join(app.root_path, 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Configurar el formato del log
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(module)s - %(message)s',
        '%Y-%m-%d %H:%M:%S,%f'
    )

    # Log principal de la aplicación
    app_log = os.path.join(log_dir, 'app.log')
    file_handler = RotatingFileHandler(
        app_log, maxBytes=10485760, backupCount=10
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    # Configurar logger de la aplicación
    app.logger.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)

    # Configurar logger para debugging en desarrollo
    if app.debug:
        debug_log = os.path.join(log_dir, 'debug.log')
        debug_handler = RotatingFileHandler(
            debug_log, maxBytes=10485760, backupCount=10
        )
        debug_handler.setFormatter(formatter)
        debug_handler.setLevel(logging.DEBUG)
        app.logger.addHandler(debug_handler)

    # Configurar logger para errores
    error_log = os.path.join(log_dir, 'error.log')
    error_handler = RotatingFileHandler(
        error_log, maxBytes=10485760, backupCount=10
    )
    error_handler.setFormatter(formatter)
    error_handler.setLevel(logging.ERROR)
    app.logger.addHandler(error_handler)

    # Logging después de cada request
    @app.after_request
    def after_request(response):
        if response.status_code != 500:
            app.logger.info(
                f'{request.remote_addr} - {request.method} {request.url} - {response.status_code}'
            )
        return response

    # Logging de errores no manejados
    @app.errorhandler(Exception)
    def handle_exception(e):
        app.logger.error(f'Error no manejado: {str(e)}', exc_info=True)
        return 'Error interno del servidor', 500

def log_info(app, message, **kwargs):
    extra = ' '.join(f'[{k}:{v}]' for k, v in kwargs.items())
    app.logger.info(f'{message} {extra}')

def log_error(app, message, exc_info=None, **kwargs):
    extra = ' '.join(f'[{k}:{v}]' for k, v in kwargs.items())
    app.logger.error(f'{message} {extra}', exc_info=exc_info)

def log_access(app, endpoint, user=None, **kwargs):
    extra = ' '.join(f'[{k}:{v}]' for k, v in kwargs.items())
    message = f'Acceso a {endpoint}'
    if user:
        message += f' por usuario {user}'
    app.logger.info(f'{message} {extra}') 