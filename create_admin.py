from flask import Flask
from werkzeug.security import generate_password_hash
from models import Usuario, db
from factory import create_app
import os

def create_admin():
    app = create_app('development')
    
    with app.app_context():
        # Verificar si ya existe un usuario admin
        admin = Usuario.query.filter_by(username='admin').first()
        if admin:
            print("El usuario administrador ya existe.")
            return
        
        # Crear nuevo usuario admin
        admin = Usuario(
            username='admin',
            password=generate_password_hash('admin123'),  # Contraseña por defecto
            email='admin@backupcode.cl',
            nombre='Administrador',
            rol='admin',
            activo=True
        )
        
        try:
            db.session.add(admin)
            db.session.commit()
            print("Usuario administrador creado exitosamente.")
            print("Username: admin")
            print("Password: admin123")
        except Exception as e:
            db.session.rollback()
            print(f"Error al crear el usuario administrador: {str(e)}")

if __name__ == '__main__':
    create_admin() 