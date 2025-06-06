"""
Modelos de la base de datos para el sistema de gestión de servicio técnico.
Este módulo define todas las entidades principales del sistema y sus relaciones.
"""

from extensions import db
from datetime import datetime
from flask_login import UserMixin

class Usuario(UserMixin, db.Model):
    """
    Modelo que representa a un usuario del sistema.
    Hereda de UserMixin para integración con Flask-Login.
    
    Roles disponibles:
    - admin: Acceso total al sistema
    - tecnico: Gestión de órdenes asignadas
    - recepcionista: Creación y seguimiento de órdenes
    """
    __tablename__ = 'usuarios'

    # Campos de identificación y acceso
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)  # Almacenado con hash
    email = db.Column(db.String(120), unique=True, nullable=False)
    nombre = db.Column(db.String(120))
    rol = db.Column(db.String(20), default='tecnico')
    activo = db.Column(db.Boolean, default=True)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    ultimo_acceso = db.Column(db.DateTime)
    
    # Preferencias de usuario
    notificaciones_email = db.Column(db.Boolean, default=True)
    tema_oscuro = db.Column(db.Boolean, default=False)
    idioma = db.Column(db.String(2), default='es')

    # Relaciones con otras entidades
    ordenes_asignadas = db.relationship('Orden', back_populates='tecnico', lazy='dynamic', 
                                      foreign_keys='Orden.tecnico_id')
    historiales = db.relationship('Historial', back_populates='usuario', lazy='dynamic')
    cotizaciones = db.relationship('SolicitudCotizacion', back_populates='usuario', lazy='dynamic')
    solicitudes = db.relationship('Solicitud', back_populates='usuario', lazy='dynamic')

    def __repr__(self):
        return f"<Usuario {self.username}, Rol: {self.rol}>"

class Orden(db.Model):
    """
    Modelo que representa una orden de servicio técnico.
    Contiene toda la información relacionada con un servicio técnico,
    incluyendo detalles del equipo, cliente, técnico asignado y estado.
    """
    __tablename__ = 'ordenes'
    
    # Identificación y relaciones principales
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    tecnico_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    
    # Especificaciones del equipo
    equipo = db.Column(db.String(100), nullable=False)  # Tipo de equipo (laptop, desktop, etc.)
    marca = db.Column(db.String(50))
    modelo = db.Column(db.String(50))
    procesador = db.Column(db.String(50))
    ram = db.Column(db.String(20))
    disco = db.Column(db.String(50))
    pantalla = db.Column(db.String(20))
    
    # Detalles del servicio
    descripcion = db.Column(db.Text, nullable=False)  # Descripción del problema
    estado = db.Column(db.String(20), default='Pendiente')  # Estado actual del servicio
    fecha_creacion = db.Column(db.DateTime, default=datetime.now)
    fecha_actualizacion = db.Column(db.DateTime, onupdate=datetime.now)
    correo = db.Column(db.String(120))  # Correo alternativo para notificaciones
    
    # Relaciones
    cliente = db.relationship('Cliente', back_populates='ordenes', lazy='joined')
    tecnico = db.relationship('Usuario', back_populates='ordenes_asignadas', lazy='joined')
    imagenes = db.relationship('Imagen', back_populates='orden', lazy='joined', cascade='all, delete-orphan')
    historial = db.relationship('Historial', back_populates='orden', lazy='dynamic', cascade='all, delete-orphan')
    solicitudes = db.relationship('Solicitud', back_populates='orden', lazy='dynamic', cascade='all, delete-orphan')
    cotizaciones = db.relationship('SolicitudCotizacion', back_populates='orden', lazy='dynamic')
    correos = db.relationship('CorreoLog', back_populates='orden', lazy='dynamic')

    def __init__(self, **kwargs):
        """Inicializa una nueva orden con fechas actuales."""
        super(Orden, self).__init__(**kwargs)
        self.fecha_creacion = datetime.now()
        self.fecha_actualizacion = self.fecha_creacion
    
    def actualizar_estado(self, nuevo_estado, usuario_id):
        """
        Actualiza el estado de la orden y registra el cambio en el historial.
        
        Args:
            nuevo_estado (str): El nuevo estado de la orden
            usuario_id (int): ID del usuario que realiza el cambio
            
        Returns:
            bool: True si el cambio fue exitoso
            
        Raises:
            Exception: Si hay un error en la transacción
        """
        from utils.db_context import atomic_transaction
        
        with atomic_transaction() as session:
            estado_anterior = self.estado
            self.estado = nuevo_estado
            self.fecha_actualizacion = datetime.now()
            
            historial = Historial(
                orden_id=self.id,
                usuario_id=usuario_id,
                accion=f"Cambio de estado de '{estado_anterior}' a '{nuevo_estado}'",
                fecha=datetime.now()
            )
            session.add(historial)
            
            return True
    
    def agregar_imagen(self, ruta, nombre):
        """
        Agrega una nueva imagen a la orden.
        
        Args:
            ruta (str): Ruta del archivo de imagen
            nombre (str): Nombre descriptivo de la imagen
            
        Returns:
            Imagen: Objeto imagen creado
            
        Raises:
            ValueError: Si se excede el límite de imágenes
        """
        from utils.db_context import atomic_transaction
        
        with atomic_transaction() as session:
            if len(self.imagenes) >= 5:
                raise ValueError("Máximo 5 imágenes por orden")
                
            imagen = Imagen(
                orden_id=self.id,
                ruta=ruta,
                nombre=nombre
            )
            session.add(imagen)
            
            return imagen

class Historial(db.Model):
    """
    Modelo para registrar cambios y eventos en las órdenes.
    Mantiene un registro cronológico de todas las modificaciones.
    """
    __tablename__ = 'historiales'

    id = db.Column(db.Integer, primary_key=True)
    orden_id = db.Column(db.Integer, db.ForeignKey('ordenes.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)  # Descripción del cambio
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    orden = db.relationship('Orden', back_populates='historial')
    usuario = db.relationship('Usuario', back_populates='historiales')

    def __repr__(self):
        return f"<Historial Orden {self.orden_id}, Usuario {self.usuario_id}>"

class Imagen(db.Model):
    """
    Modelo para almacenar imágenes asociadas a las órdenes.
    Permite adjuntar fotos del equipo o documentos relevantes.
    """
    __tablename__ = 'imagenes'
    
    id = db.Column(db.Integer, primary_key=True)
    orden_id = db.Column(db.Integer, db.ForeignKey('ordenes.id'), nullable=False)
    filename = db.Column(db.String(120), nullable=False)  # Nombre del archivo en el sistema

    # Relaciones
    orden = db.relationship('Orden', back_populates='imagenes')

class Cliente(db.Model):
    """
    Modelo que representa a un cliente del servicio técnico.
    Almacena información de contacto y relación con órdenes.
    """
    __tablename__ = 'clientes'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    correo = db.Column(db.String(120), nullable=True)
    telefono = db.Column(db.String(20), nullable=True)
    direccion = db.Column(db.String(200), nullable=True)
    rut = db.Column(db.String(20), nullable=True, unique=True)  # RUT chileno único

    # Relaciones
    ordenes = db.relationship('Orden', back_populates='cliente', lazy='dynamic')
    cotizaciones = db.relationship('SolicitudCotizacion', back_populates='cliente', lazy='dynamic')

class Solicitud(db.Model):
    """
    Modelo para gestionar solicitudes de repuestos o presupuestos.
    Permite hacer seguimiento a pedidos especiales.
    """
    __tablename__ = 'solicitudes'
    
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(50))  # 'Repuesto' o 'Presupuesto'
    descripcion = db.Column(db.Text, nullable=False)
    orden_id = db.Column(db.Integer, db.ForeignKey('ordenes.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    orden = db.relationship('Orden', back_populates='solicitudes')
    usuario = db.relationship('Usuario', back_populates='solicitudes')

class CorreoLog(db.Model):
    """
    Modelo para registrar el historial de correos enviados.
    Permite hacer seguimiento de las notificaciones y errores.
    """
    __tablename__ = 'correo_log'

    id = db.Column(db.Integer, primary_key=True)
    orden_id = db.Column(db.Integer, db.ForeignKey('ordenes.id'), nullable=True)
    destinatario = db.Column(db.String(120), nullable=False)
    asunto = db.Column(db.String(255), nullable=False)
    cuerpo = db.Column(db.Text, nullable=False)
    fecha_envio = db.Column(db.DateTime, default=datetime.utcnow)
    estado = db.Column(db.String(50), nullable=False, default='pendiente')  # "enviado", "error", "pendiente"
    error = db.Column(db.Text, nullable=True)  # Detalles del error si ocurrió

    # Relaciones
    orden = db.relationship('Orden', back_populates='correos')

    def __repr__(self):
        return f"<CorreoLog {self.id} - {self.asunto}>"

class SolicitudCotizacion(db.Model):
    """
    Modelo para gestionar solicitudes de cotización.
    Permite manejar presupuestos independientes o asociados a órdenes.
    """
    __tablename__ = 'solicitud_cotizacion'
    
    id = db.Column(db.Integer, primary_key=True)
    asunto = db.Column(db.String(255), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    orden_id = db.Column(db.Integer, db.ForeignKey('ordenes.id'), nullable=True)  # Opcional
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=True)  # Opcional
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    correo_encargado = db.Column(db.String(255), nullable=True)  # Correo del encargado de cotizar

    # Relaciones
    orden = db.relationship('Orden', back_populates='cotizaciones')
    usuario = db.relationship('Usuario', back_populates='cotizaciones')
    cliente = db.relationship('Cliente', back_populates='cotizaciones')

    def __repr__(self):
        return f"<SolicitudCotizacion de {self.usuario.username}, asunto: {self.asunto}>"

class OrdenEliminada(db.Model):
    """
    Modelo para registrar órdenes eliminadas.
    Mantiene un registro histórico de órdenes borradas para auditoría.
    """
    __tablename__ = 'ordenes_eliminadas'

    id = db.Column(db.Integer, primary_key=True)
    orden_id_original = db.Column(db.Integer, nullable=False)
    cliente_nombre = db.Column(db.String(100))
    cliente_correo = db.Column(db.String(120))
    equipo = db.Column(db.String(50))
    marca = db.Column(db.String(50))
    modelo = db.Column(db.String(50))
    descripcion = db.Column(db.Text)
    estado = db.Column(db.String(20))
    fecha_creacion_original = db.Column(db.DateTime, nullable=False)
    fecha_eliminacion = db.Column(db.DateTime, nullable=False, default=datetime.now)
    eliminado_por = db.Column(db.String(100), nullable=False)  # Username del admin
    motivo_eliminacion = db.Column(db.Text)
    datos_adicionales = db.Column(db.JSON)  # Para almacenar cualquier otro dato relevante

    def __repr__(self):
        return f'<OrdenEliminada {self.orden_id_original}>'