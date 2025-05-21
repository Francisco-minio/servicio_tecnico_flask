from flask import Flask, render_template, redirect, url_for, request, session, flash, send_file, abort
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_migrate import Migrate
from extensions import db
from datetime import datetime
import os
from models import Historial, Usuario, Orden
from utils.pdf_generator import generar_pdf_task # <--- IMPORT NEW Celery task for PDF
# Updated import for Celery tasks
from utils.mail_sender import enviar_correo_task, enviar_notificacion_admin_task
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_wtf.csrf import CSRFProtect
from flask_session import Session # Import Flask-Session
from flask_talisman import Talisman # Import Flask-Talisman
from models import Orden, Imagen
from models import Cliente  # Asegúrate de importar el modelo Cliente
from models import Solicitud #agregar solicitudes de repuestos

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'a_strong_default_secret_key_for_development_only')
csrf = CSRFProtect(app) # Initialize CSRFProtect
basedir = os.path.abspath(os.path.dirname(__file__))
#app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(basedir, 'instance', 'database.db')}"
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'mysql+pymysql://user:password@localhost/default_db')
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAIL_DEFAULT_SENDER'] = 'tucorreo@ejemplo.com'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB

# Flask-Session Configuration
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_FILE_DIR'] = os.path.join(basedir, 'instance', 'flask_session')
# app.config['SESSION_FILE_THRESHOLD'] = 500 # Optional

# Inicializar extensiones
db.init_app(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

# Initialize Flask-Session AFTER other configurations
Session(app)

# Initialize Talisman for security headers
talisman = Talisman(app)

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

with app.app_context():
    db.create_all()

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.rol == 'admin':
            return redirect(url_for('dashboard_admin'))
        else:
            return redirect(url_for('dashboard_tecnico'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = Usuario.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        flash('Credenciales inválidas', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.errorhandler(403)
def forbidden(error):
    return render_template('403.html'), 403

@app.route('/dashboard/admin')
@login_required
def dashboard_admin():
    if current_user.rol != 'admin':
        return redirect(url_for('index'))
    ordenes = Orden.query.all()
    return render_template('dashboard_admin.html', ordenes=ordenes, usuario=current_user)

@app.route('/dashboard/tecnico')
@login_required
def dashboard_tecnico():
    if current_user.rol != 'tecnico':
        return redirect(url_for('index'))
    ordenes = Orden.query.filter_by(tecnico_id=current_user.id).all()
    return render_template('dashboard_tecnico.html', ordenes=ordenes, usuario=current_user)

@app.route('/orden/nueva', methods=['GET', 'POST'])
@login_required
def nueva_orden():
    if request.method == 'POST':
        # Datos del cliente (puede ser nuevo o existente)
        cliente_nombre = request.form['cliente']
        cliente_correo = request.form['correo']

        # Buscar si ya existe
        cliente_existente = Cliente.query.filter_by(nombre=cliente_nombre, correo=cliente_correo).first()
        if cliente_existente:
            cliente_id = cliente_existente.id
        else:
            nuevo_cliente = Cliente(nombre=cliente_nombre, correo=cliente_correo)
            db.session.add(nuevo_cliente)
            db.session.commit()
            cliente_id = nuevo_cliente.id

        # Datos de la orden
        equipo = request.form['equipo']
        marca = request.form['marca']
        modelo = request.form['modelo']
        descripcion = request.form['descripcion']
        procesador = request.form.get('procesador')
        ram = request.form.get('ram')
        disco = request.form.get('disco')
        pantalla = request.form.get('pantalla')
        tecnico_id = request.form.get('tecnico_id') or None

        nueva = Orden(
            cliente_id=cliente_id,
            correo=cliente_correo, 
            equipo=equipo,
            marca=marca,
            modelo=modelo,
            descripcion=descripcion,
            procesador=procesador,
            ram=ram,
            disco=disco,
            pantalla=pantalla,
            estado='Ingresado',
            fecha_creacion=datetime.now(),
            usuario_id=current_user.id,
            tecnico_id=tecnico_id
        )

        db.session.add(nueva)
        db.session.commit()

        # Guardar imágenes si hay
        imagenes = request.files.getlist('imagenes')
        for imagen in imagenes:
            if imagen and imagen.filename:
                if not allowed_file(imagen.filename):
                    flash(f"Tipo de archivo no permitido: {imagen.filename}. Permitidos: {', '.join(app.config['ALLOWED_EXTENSIONS'])}", 'danger')
                    continue  # Skip this file and proceed with the next
                filename = secure_filename(imagen.filename)
                imagen.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                nueva_imagen = Imagen(orden_id=nueva.id, filename=filename)
                db.session.add(nueva_imagen)

        db.session.commit()

        # Enviar correo
        try:
            cliente_nombre_para_email = nueva.cliente.nombre # Assuming 'nueva.cliente' is accessible and has 'nombre'
            fecha_creacion_str_para_email = nueva.fecha_creacion.strftime('%d-%m-%Y %H:%M')

            enviar_correo_task.delay(
                cliente_nombre=cliente_nombre_para_email,
                orden_id=nueva.id,
                equipo=nueva.equipo,
                estado=nueva.estado,
                fecha_creacion_str=fecha_creacion_str_para_email,
                destinatario_email=nueva.correo
            )
            flash('Orden ingresada exitosamente. Se enviará una confirmación por correo.', 'success')
        except Exception as e:
            app.logger.error(f"Error al encolar tarea de envío de correo: {e}") # Use app.logger
            flash('Orden ingresada pero ocurrió un error al programar el envío del correo.', 'warning')

        return redirect(url_for('dashboard_admin'))

    # 👇👇👇 Estas variables deben definirse para GET
    tecnicos = Usuario.query.filter_by(rol='tecnico').all()
    clientes = Cliente.query.all()

    return render_template('orden_form.html', tecnicos=tecnicos, clientes=clientes)


@app.route('/orden/<int:orden_id>/estado', methods=['POST'])
@login_required
def actualizar_estado(orden_id):
    orden = Orden.query.get_or_404(orden_id)
    nuevo_estado = request.form['estado']
    orden.estado = nuevo_estado
    db.session.commit()

    historial = Historial(
        orden_id=orden.id,
        usuario_id=current_user.id,
        descripcion=f"Orden editada: Estado cambiado a {nuevo_estado}"
    )
    db.session.add(historial)
    db.session.commit()

    flash('Estado actualizado correctamente.', 'success')
    return redirect(url_for('ver_orden', orden_id=orden.id))


@app.route('/orden/<int:orden_id>', methods=['GET', 'POST'])
@login_required
def ver_orden(orden_id):
    orden = Orden.query.get_or_404(orden_id)
    historial = Historial.query.filter_by(orden_id=orden_id).order_by(Historial.fecha.desc()).all()

    if request.method == 'POST':
        comentario = request.form.get('comentario')
        if comentario:
            nuevo_evento = Historial(
                orden_id=orden.id,
                usuario_id=current_user.id,
                descripcion=f"Comentario: {comentario}"
            )
            db.session.add(nuevo_evento)
            db.session.commit()
            flash("Comentario agregado exitosamente", "success")
            return redirect(url_for('ver_orden', orden_id=orden.id))

    return render_template('orden_detalle.html', orden=orden, historial=historial)

@app.route('/orden/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_orden(id):
    orden = Orden.query.get_or_404(id)

    if request.method == 'POST':
        orden.cliente = request.form['cliente']
        orden.correo = request.form['correo']
        orden.equipo = request.form['equipo']
        orden.marca = request.form['marca']
        orden.modelo = request.form['modelo']
        orden.descripcion = request.form['descripcion']
        orden.procesador = request.form.get('procesador')
        orden.ram = request.form.get('ram')
        orden.disco = request.form.get('disco')
        orden.pantalla = request.form.get('pantalla')
        
        
        db.session.commit()
        flash('Orden actualizada correctamente.', 'success')
        return redirect(url_for('ver_orden', orden_id=orden.id))

    return render_template('editar_orden.html', orden=orden)


@app.route('/orden/<int:orden_id>/asignar', methods=['POST'])
@login_required
def asignar_orden(orden_id):
    if current_user.rol != 'admin':
        flash('No tienes permiso para asignar esta orden')
        return redirect(url_for('dashboard_admin'))

    tecnico_id = request.form.get('tecnico_id')

    orden = Orden.query.get_or_404(orden_id)
    orden.tecnico_id = tecnico_id
    orden.fecha_asignacion = datetime.utcnow()
    orden.estado = 'Asignada'

    historial = Historial(
        orden_id=orden.id,
        usuario_id=current_user.id,
        descripcion=f"Orden asignada al técnico ID {tecnico_id}"
    )
    db.session.add(historial)
    db.session.commit()

    flash('Orden asignada con éxito')
    return redirect(url_for('dashboard_admin'))


@app.route('/orden/<int:orden_id>/cerrar', methods=['POST'])
@login_required
def cerrar_orden(orden_id):
    if current_user.rol != 'admin':
        flash('No tienes permiso para cerrar esta orden')
        return redirect(url_for('dashboard_admin'))

    orden = Orden.query.get_or_404(orden_id)
    orden.fecha_cierre = datetime.utcnow()
    orden.estado = 'Cerrada'

    historial = Historial(orden_id=orden.id, usuario_id=current_user.id,
                          descripcion="Orden cerrada")
    db.session.add(historial)
    db.session.commit()

    flash('Orden cerrada con éxito')
    return redirect(url_for('dashboard_admin'))

@app.route('/orden/<int:orden_id>/avances', methods=['GET', 'POST'])
@login_required
def modificar_avances(orden_id):
    orden = Orden.query.get_or_404(orden_id)

    if current_user.rol != 'tecnico':
        flash('No tienes permiso para modificar esta orden')
        return redirect(url_for('dashboard_tecnico'))

    if request.method == 'POST':
        avance = request.form['avance']
        orden.avances = (orden.avances or '') + f"\n{datetime.utcnow()}: {avance}"

        historial = Historial(orden_id=orden.id, usuario_id=current_user.id,
                              descripcion=f"Avance: {avance}")
        db.session.add(historial)
        db.session.commit()

        flash('Avance registrado con éxito')
        return redirect(url_for('ver_orden', orden_id=orden.id))

    return render_template('modificar_avances.html', orden=orden)
@app.route('/orden/<int:orden_id>/pdf')
@login_required
def descargar_pdf(orden_id):
    pdf_filename = f"orden_{orden_id}.pdf"
    # Ensure UPLOAD_FOLDER is defined and accessible, or use a dedicated PDF folder
    # For consistency with original code, using 'static/pdfs/'
    pdf_dir = os.path.join(app.static_folder, 'pdfs') 
    if not os.path.exists(pdf_dir):
        os.makedirs(pdf_dir) # Ensure the directory exists
    pdf_path = os.path.join(pdf_dir, pdf_filename)

    if not os.path.exists(pdf_path):
        try:
            # Call the task and wait for it to complete (interim step)
            # In a fully async setup, you'd redirect or notify the user.
            task_result = generar_pdf_task.apply_async(args=[orden_id, pdf_path])
            task_result.get(timeout=30)  # Wait up to 30 seconds for PDF generation
                                        # This will raise an exception on task error or timeout.
            flash('El PDF ha sido generado.', 'success')
        except TimeoutError: # Make sure TimeoutError is imported or handle celery.exceptions.TimeoutError
            app.logger.error(f"Timeout generando PDF para orden {orden_id}")
            flash('La generación del PDF tardó demasiado. Intente nuevamente.', 'danger')
            # Depending on desired UX, redirect to order details or another relevant page
            return redirect(url_for('ver_orden', orden_id=orden_id))
        except Exception as e:
            app.logger.error(f"Error generando PDF para orden {orden_id}: {e}")
            flash(f'Error al generar el PDF: {str(e)}', 'danger')
            return redirect(url_for('ver_orden', orden_id=orden_id))

    # If PDF exists (either pre-existing or just generated)
    if os.path.exists(pdf_path):
        return send_file(pdf_path, as_attachment=True)
    else:
        # This case should ideally not be reached if generation was successful
        # but task.get() didn't error and file still not there.
        flash('No se pudo encontrar el PDF generado. Por favor, intente generarlo de nuevo.', 'danger')
        return redirect(url_for('ver_orden', orden_id=orden_id))

#ingresar solicitudes de repuesto

@app.route('/orden/<int:orden_id>/solicitud', methods=['POST'])
@login_required
def solicitar_repuesto_presupuesto(orden_id):
    orden = Orden.query.get_or_404(orden_id)
    tipo = request.form.get('tipo')
    descripcion = request.form.get('descripcion')

    if tipo not in ['Repuesto', 'Presupuesto'] or not descripcion:
        flash("Debes completar todos los campos.", "danger")
        return redirect(url_for('ver_orden', orden_id=orden.id))

    solicitud = Solicitud(
        tipo=tipo,
        descripcion=descripcion,
        orden_id=orden.id,
        usuario_id=current_user.id
    )
    db.session.add(solicitud)

    evento = Historial(
        orden_id=orden.id,
        usuario_id=current_user.id,
        descripcion=f"Solicitud de {tipo.lower()}: {descripcion}"
    )

       # 🔥 Actualizar el estado de la orden
    orden = Orden.query.get_or_404(orden_id)
    orden.estado = "Enviado a Cotización"
    db.session.add(evento)
    db.session.commit()

   # 🔥 Actualizar el estado de la orden
    orden = Orden.query.get_or_404(orden_id)
    orden.estado = "Enviado a Cotización"

    # Enviar correo al administrador
    try:
        subject = f"Solicitud de {tipo} para orden #{orden.id}"
        html_body = f"""
            <h4>Solicitud de {tipo}</h4>
            <p><strong>Usuario:</strong> {current_user.username}</p>
            <p><strong>Orden ID:</strong> {orden.id}</p>
            <p><strong>Cliente:</strong> {orden.cliente.nombre}</p>
            <p><strong>Equipo:</strong> {orden.equipo}</p>
            <p><strong>Descripción de la solicitud:</strong><br>{descripcion}</p>
            <hr>
            <p><a href="{url_for('ver_orden', orden_id=orden.id, _external=True)}">Ver Orden en el sistema</a></p>
        """
        admin_email_recipient = 'franciscominio@bcode.cl' # Or from app.config

        enviar_notificacion_admin_task.delay(
            subject=subject,
            html_body=html_body,
            recipient=admin_email_recipient
        )
    except Exception as e:
        app.logger.error(f"Error al encolar tarea de notificación al admin: {e}")
        # The flash message about the error in scheduling email is optional, 
        # as the main operation (solicitud) was successful.
        # flash("La solicitud fue registrada, pero ocurrió un error al programar la notificación por correo.", "warning")

    flash(f"Solicitud de {tipo.lower()} registrada correctamente.", "success")
    return redirect(url_for('ver_orden', orden_id=orden.id))



@app.route('/usuarios')
@login_required
def ver_usuarios():
    if current_user.rol != 'admin':
        flash('No tienes permiso para ver los usuarios')
        return redirect(url_for('index'))

    usuarios = Usuario.query.all()
    return render_template('ver_usuarios.html', usuarios=usuarios)

@app.route('/crear_usuario', methods=['GET', 'POST'])
@login_required
def crear_usuario():
    if current_user.rol != 'admin':
        flash('No tienes permiso para crear usuarios')
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username']
        correo = request.form['correo']
        password = generate_password_hash(request.form['password'])
        rol = request.form['rol']

        nuevo_usuario = Usuario(username=username, correo=correo, password=password, rol=rol)
        db.session.add(nuevo_usuario)
        db.session.commit()

        flash('Usuario creado correctamente.', 'success')
        return redirect(url_for('dashboard_admin'))

    return render_template('crear_usuario.html')



@app.route('/usuario/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_usuario(id):
    usuario = Usuario.query.get_or_404(id)

    if request.method == 'POST':
        usuario.username = request.form['username']
        usuario.correo = request.form['correo']
        usuario.rol = request.form['rol']

        nueva_contraseña = request.form.get('password')
        if nueva_contraseña:
            usuario.password = generate_password_hash(nueva_contraseña)

        db.session.commit()
        flash('Usuario actualizado correctamente.', 'success')
        return redirect(url_for('ver_usuarios'))

    return render_template('editar_usuario.html', usuario=usuario)

@app.route('/clientes')
@login_required
def listar_clientes():
    clientes = Cliente.query.all()  # Trae todos los clientes
    return render_template('clientes.html', clientes=clientes)

@app.route('/cliente/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_cliente():
    if request.method == 'POST':
        nombre = request.form['nombre']
        correo = request.form['correo']
        telefono = request.form.get('telefono')
        direccion = request.form.get('direccion')

        # Verificar si el correo ya existe
        existente = Cliente.query.filter_by(correo=correo).first()
        if existente:
            flash('Ya existe un cliente con ese correo.', 'warning')
            return redirect(url_for('nuevo_cliente'))

        cliente = Cliente(nombre=nombre, correo=correo, telefono=telefono, direccion=direccion)
        db.session.add(cliente)
        db.session.commit()
        flash('Cliente creado exitosamente.', 'success')
        return redirect(url_for('listar_clientes'))
    # 👇 Este return es necesario para mostrar el formulario
    return render_template('Cliente_form.html')
@app.route('/cliente/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_cliente(id):
    cliente = Cliente.query.get_or_404(id)

    if request.method == 'POST':
        cliente.nombre = request.form['nombre']
        cliente.correo = request.form['correo']
        cliente.telefono = request.form.get('telefono')
        cliente.direccion = request.form.get('direccion')

        # Podrías validar que el correo no se duplique en otro cliente
        otro = Cliente.query.filter(Cliente.correo == cliente.correo, Cliente.id != cliente.id).first()
        if otro:
            flash('Ya existe otro cliente con ese correo.', 'warning')
            return redirect(url_for('editar_cliente', id=id))

        db.session.commit()
        flash('Cliente actualizado correctamente.', 'success')
        return redirect(url_for('listar_clientes'))

    return render_template('cliente_form.html', cliente=cliente)

@app.route('/cliente/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar_cliente(id):
    cliente = Cliente.query.get_or_404(id)
    try:
        db.session.delete(cliente)
        db.session.commit()
        flash('Cliente eliminado correctamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error al eliminar el cliente. Asegúrate de que no tenga órdenes asociadas.', 'danger')
    return redirect(url_for('listar_clientes'))




# IMPORTANT: debug=True should be False in a production environment.
if __name__ == '__main__':
    app.run(debug=True)
