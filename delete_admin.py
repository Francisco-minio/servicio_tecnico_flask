from app import create_app
from models import db, Usuario

def delete_admin_user():
    app = create_app()
    with app.app_context():
        Usuario.query.filter_by(username='admin').delete()
        db.session.commit()
        print("Usuario administrador eliminado exitosamente")

if __name__ == '__main__':
    delete_admin_user() 