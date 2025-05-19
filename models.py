from extensions import db
from datetime import datetime
from flask_login import UserMixin

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    correo = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    rol = db.Column(db.String(20), nullable=False)

    # Relación con historial
    historiales = db.relationship('Historial', back_populates='usuario', lazy='select')

    # Relación con órdenes como creador
    ordenes_creadas = db.relationship('Orden', back_populates='usuario', foreign_keys='Orden.usuario_id', lazy='select')

    # Relación con órdenes como técnico asignado
    ordenes_asignadas = db.relationship('Orden', back_populates='tecnico', foreign_keys='Orden.tecnico_id', lazy='select')

    def __repr__(self):
        return f"<Usuario {self.username}, Rol: {self.rol}>"

class Orden(db.Model):
    __tablename__ = 'ordenes'

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    cliente = db.relationship('Cliente', backref=db.backref('ordenes', lazy=True))
    correo = db.Column(db.String(100), nullable=False)
    equipo = db.Column(db.String(100), nullable=False)
    marca = db.Column(db.String(100), nullable=False)
    modelo = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    estado = db.Column(db.String(50), nullable=False, default='Ingresado')
    imagen = db.Column(db.String(255))
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_cierre = db.Column(db.DateTime, nullable=True)

    # Características del equipo
    procesador = db.Column(db.String(100), nullable=True)
    ram = db.Column(db.String(50), nullable=True)
    disco = db.Column(db.String(50), nullable=True)
    pantalla = db.Column(db.String(50), nullable=True)

    # FK y relación con el técnico asignado
    tecnico_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    tecnico = db.relationship('Usuario', back_populates='ordenes_asignadas', foreign_keys=[tecnico_id])

    # FK y relación con el usuario que creó la orden
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    usuario = db.relationship('Usuario', back_populates='ordenes_creadas', foreign_keys=[usuario_id])

    # Historial
    historial = db.relationship('Historial', back_populates='orden', lazy='select')

    def __repr__(self):
        return f"<Orden {self.id}, Estado: {self.estado}>"

class Historial(db.Model):
    __tablename__ = 'historiales'

    id = db.Column(db.Integer, primary_key=True)
    orden_id = db.Column(db.Integer, db.ForeignKey('ordenes.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    orden = db.relationship('Orden', back_populates='historial', lazy='select')
    usuario = db.relationship('Usuario', back_populates='historiales', lazy='select')

    def __repr__(self):
        return f"<Historial Orden {self.orden_id}, Usuario {self.usuario_id}>"

class Imagen(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    orden_id = db.Column(db.Integer, db.ForeignKey('ordenes.id'), nullable=False)
    filename = db.Column(db.String(120), nullable=False)

    orden = db.relationship('Orden', backref=db.backref('imagenes', lazy=True))

class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    correo = db.Column(db.String(120), nullable=True)
    telefono = db.Column(db.String(20), nullable=True)
    direccion = db.Column(db.String(200), nullable=True)
    rut = db.Column(db.String(20), nullable=True, unique=True)  # Si aplica en Chile

class Solicitud(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(50))  # 'Repuesto' o 'Presupuesto'
    descripcion = db.Column(db.Text, nullable=False)
    orden_id = db.Column(db.Integer, db.ForeignKey('ordenes.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

    orden = db.relationship('Orden', backref='solicitudes')
    usuario = db.relationship('Usuario')
