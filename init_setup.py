import os
import sys
from flask_migrate import upgrade
from werkzeug.security import generate_password_hash
from models import Usuario
from extensions import db
from factory import create_app
import logging

def setup_logging():
    """Configurar el sistema de logging."""
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    logging.basicConfig(
        filename='logs/setup.log',
        level=logging.INFO,
        format='%(asctime)s %(levelname)s: %(message)s'
    )

def crear_directorios():
    """Crear los directorios necesarios."""
    directorios = [
        'static/uploads/images',
        'logs',
        'instance',
        'flask_session'
    ]
    
    for directorio in directorios:
        if not os.path.exists(directorio):
            os.makedirs(directorio)
            logging.info(f'Directorio creado: {directorio}')

def crear_admin():
    """Crear usuario administrador si no existe."""
    app = create_app('development')
    with app.app_context():
        if not Usuario.query.filter_by(username='admin').first():
            admin = Usuario(
                username='admin',
                password=generate_password_hash('admin'),
                email='admin@backupcode.cl',
                rol='admin',
                nombre='Administrador'
            )
            db.session.add(admin)
            db.session.commit()
            logging.info('Usuario administrador creado')

def main():
    """Función principal de inicialización."""
    try:
        print("Iniciando configuración del sistema...")
        
        # Configurar logging
        setup_logging()
        logging.info('Iniciando setup del sistema')
        
        # Crear directorios necesarios
        crear_directorios()
        logging.info('Directorios creados')
        
        # Crear base de datos y aplicar migraciones
        app = create_app('development')
        with app.app_context():
            db.create_all()
            logging.info('Base de datos creada')
            
            # Aplicar migraciones
            upgrade()
            logging.info('Migraciones aplicadas')
            
            # Crear usuario admin
            crear_admin()
        
        print("Configuración completada exitosamente.")
        logging.info('Setup completado exitosamente')
        return 0
        
    except Exception as e:
        print(f"Error durante la configuración: {str(e)}")
        logging.error(f'Error durante el setup: {str(e)}')
        return 1

if __name__ == '__main__':
    sys.exit(main()) 