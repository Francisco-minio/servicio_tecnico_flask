from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, TextAreaField, FileField
from wtforms.validators import DataRequired, Email, Length, Optional, ValidationError
from models import Usuario, Cliente

class LoginForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired()])
    password = PasswordField('Contraseña', validators=[DataRequired()])

class UsuarioForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired(), Length(min=4)])
    email = StringField('Correo electrónico', validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[Optional(), Length(min=6)])
    rol = SelectField('Rol', choices=[('admin', 'Administrador'), ('tecnico', 'Técnico'), ('cliente', 'Cliente')])
    
    def validate_username(self, field):
        user = Usuario.query.filter_by(username=field.data).first()
        if user and user.username != field.data:
            raise ValidationError('Este nombre de usuario ya está en uso.')
            
    def validate_email(self, field):
        user = Usuario.query.filter_by(email=field.data).first()
        if user and user.email != field.data:
            raise ValidationError('Este correo electrónico ya está registrado.')

class ClienteForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired(), Length(min=3)])
    correo = StringField('Correo', validators=[DataRequired(), Email()])
    telefono = StringField('Teléfono', validators=[Optional()])
    direccion = TextAreaField('Dirección', validators=[Optional()])
    
    def validate_correo(self, field):
        cliente = Cliente.query.filter_by(correo=field.data).first()
        if cliente:
            raise ValidationError('Este correo ya está registrado.')

class OrdenForm(FlaskForm):
    cliente = StringField('Cliente', validators=[DataRequired()])
    correo = StringField('Correo', validators=[DataRequired(), Email()])
    equipo = StringField('Equipo', validators=[DataRequired()])
    marca = StringField('Marca', validators=[DataRequired()])
    modelo = StringField('Modelo', validators=[DataRequired()])
    descripcion = TextAreaField('Descripción', validators=[DataRequired()])
    procesador = StringField('Procesador', validators=[Optional()])
    ram = StringField('RAM', validators=[Optional()])
    disco = StringField('Disco', validators=[Optional()])
    pantalla = StringField('Pantalla', validators=[Optional()])
    imagenes = FileField('Imágenes', validators=[Optional()])
    tecnico_id = SelectField('Técnico', coerce=int, validators=[Optional()])
    
    def __init__(self, *args, **kwargs):
        super(OrdenForm, self).__init__(*args, **kwargs)
        self.tecnico_id.choices = [(0, 'Sin asignar')] + [
            (u.id, u.username) for u in Usuario.query.filter_by(rol='tecnico').all()
        ]

class SolicitudForm(FlaskForm):
    tipo = SelectField('Tipo', choices=[
        ('Repuesto', 'Solicitud de Repuesto'),
        ('Presupuesto', 'Solicitud de Presupuesto')
    ])
    descripcion = TextAreaField('Descripción', validators=[DataRequired()]) 