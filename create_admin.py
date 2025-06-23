from werkzeug.security import generate_password_hash
from datetime import datetime
from app import create_app
from models import db, Usuario

def create_admin_user():
    app = create_app()
    with app.app_context():
        # Verificar si ya existe un usuario admin
        admin = Usuario.query.filter_by(username='admin').first()
        if admin is None:
            admin = Usuario(
                username='admin',
                password=generate_password_hash('admin123', method='pbkdf2:sha256'),
                email='admin@example.com',
                nombre='Administrador',
                rol='admin',
                activo=True,
                fecha_registro=datetime.now(),
                ultimo_acceso=datetime.now(),
                notificaciones_email=True,
                tema_oscuro=False,
                idioma='es'
            )
            db.session.add(admin)
            db.session.commit()
            print("Usuario administrador creado exitosamente")
        else:
            print("El usuario administrador ya existe")

if __name__ == '__main__':
    create_admin_user() 