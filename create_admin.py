from flask import Flask
from extensions import db
from models import Usuario
from werkzeug.security import generate_password_hash
from config import config

def create_admin_user():
    app = Flask(__name__)
    app.config.from_object(config['development'])
    db.init_app(app)
    
    with app.app_context():
        # Verificar si ya existe un usuario admin
        admin = Usuario.query.filter_by(username='admin').first()
        if admin:
            print('El usuario admin ya existe')
            return
        
        # Crear nuevo usuario admin
        admin = Usuario(
            username='admin',
            password=generate_password_hash('admin123'),
            email='admin@backupcode.cl',
            nombre='Administrador',
            rol='admin',
            activo=True
        )
        
        try:
            db.session.add(admin)
            db.session.commit()
            print('Usuario admin creado exitosamente')
        except Exception as e:
            db.session.rollback()
            print(f'Error al crear usuario admin: {str(e)}')

if __name__ == '__main__':
    create_admin_user() 