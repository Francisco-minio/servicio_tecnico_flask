from app import app  # Asegúrate de importar la app correcta si está en otro lugar
from extensions import db
from models import Usuario
from werkzeug.security import generate_password_hash

with app.app_context():
    # Datos del nuevo usuario admin
    username = "admin"
    correo = "franciscominio@backupcode.cl"
    password_plano = "Yov61331"
    rol = "admin"

    # Verifica si ya existe
    existente = Usuario.query.filter_by(correo=correo).first()
    if existente:
        print("Ya existe un usuario con ese correo.")
    else:
        nuevo_usuario = Usuario(
            username=username,
            correo=correo,
            password=generate_password_hash(password_plano),
            rol=rol
        )
        db.session.add(nuevo_usuario)
        db.session.commit()
        print(f"Usuario administrador creado: {username} ({correo})")