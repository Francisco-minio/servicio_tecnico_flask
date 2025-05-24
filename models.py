from extensions import db
from datetime import datetime
from flask_login import UserMixin

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    nombre = db.Column(db.String(120))
    rol = db.Column(db.String(20), default='tecnico')
    activo = db.Column(db.Boolean, default=True)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    ultimo_acceso = db.Column(db.DateTime)
    
    # Preferencias
    notificaciones_email = db.Column(db.Boolean, default=True)
    tema_oscuro = db.Column(db.Boolean, default=False)
    idioma = db.Column(db.String(2), default='es')

    # Relaciones
    ordenes_creadas = db.relationship('Orden', back_populates='usuario', foreign_keys='Orden.usuario_id', lazy='select')
    ordenes_asignadas = db.relationship('Orden', back_populates='tecnico', foreign_keys='Orden.tecnico_id', lazy='select')
    historiales = db.relationship('Historial', back_populates='usuario', lazy='select')
    cotizaciones = db.relationship('SolicitudCotizacion', back_populates='usuario', lazy='select')

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
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'))
    # Historial
    historial = db.relationship('Historial', back_populates='orden', lazy='select')
    
    #relaciones backref/back_populates
    
    correos = db.relationship('CorreoLog', backref='orden', lazy='select')


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

class CorreoLog(db.Model):
    __tablename__ = 'correo_log'

    id = db.Column(db.Integer, primary_key=True)
    orden_id = db.Column(db.Integer, db.ForeignKey('ordenes.id'), nullable=True)
    destinatario = db.Column(db.String(120), nullable=False)
    asunto = db.Column(db.String(255), nullable=False)
    cuerpo = db.Column(db.Text, nullable=False)
    fecha_envio = db.Column(db.DateTime, default=datetime.utcnow)
    estado = db.Column(db.String(50), nullable=False)  # "Enviado", "Error", etc.
    error = db.Column(db.Text, nullable=True)

class SolicitudCotizacion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    asunto = db.Column(db.String(255), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    orden_id = db.Column(db.Integer, db.ForeignKey('ordenes.id'), nullable=True)  # Referencia opcional
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    correo_encargado = db.Column(db.String(255), nullable=True)

    # Relaciones
    orden = db.relationship('Orden', backref='cotizaciones', lazy='select')
    usuario = db.relationship('Usuario', back_populates='cotizaciones', lazy='select')
    cliente = db.relationship('Cliente', backref='cotizaciones', lazy='select')

    def __repr__(self):
        return f"<SolicitudCotizacion de {self.usuario.username}, asunto: {self.asunto}>"