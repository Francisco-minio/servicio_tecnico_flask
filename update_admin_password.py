from werkzeug.security import generate_password_hash
from app import create_app
from models import db, Usuario

def update_admin_password():
    app = create_app()
    with app.app_context():
        admin = Usuario.query.filter_by(username='admin').first()
        if admin:
            admin.password = generate_password_hash('admin123', method='pbkdf2:sha256')
            db.session.commit()
            print("Contraseña del administrador actualizada exitosamente")
        else:
            print("El usuario administrador no existe")

if __name__ == '__main__':
    update_admin_password() 