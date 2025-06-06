from flask import render_template, redirect, url_for, request, flash, send_file, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import json
from models import Orden, Cliente, Imagen, Usuario, Historial, Solicitud, CorreoLog, OrdenEliminada
from extensions import db
from utils.mail_sender import enviar_correo, enviar_notificacion_admin
from utils.db_context import db_session, atomic_transaction
from utils.zebra_printer import ZebraPrinter
from . import orden_bp
import logging
from functools import wraps

logger = logging.getLogger(__name__)

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.rol == 'admin':
            flash('No tienes permisos para realizar esta acción.', 'error')
            return redirect(url_for('orden.listar_ordenes'))
        return f(*args, **kwargs)
    return decorated_function

@orden_bp.route('/')
@login_required
def listar_ordenes():
    ordenes = Orden.query.all()
    return render_template('orden/listar_ordenes.html', ordenes=ordenes)

@orden_bp.route('/nueva', methods=['GET', 'POST'])
@login_required
def nueva_orden():
    if request.method == 'POST':
        try:
            # Validar datos básicos
            if not all([
                request.form.get('cliente_id'),
                request.form.get('correo'),
                request.form.get('equipo'),
                request.form.get('marca'),
                request.form.get('modelo'),
                request.form.get('descripcion')
            ]):
                flash('Por favor complete todos los campos obligatorios.', 'error')
                return redirect(url_for('orden.nueva_orden'))

            cliente_id = request.form.get('cliente_id')

            # Procesar tecnico_id
            tecnico_id = request.form.get('tecnico_id')
            if tecnico_id in ['', '0', None]:
                tecnico_id = None
            else:
                tecnico_id = int(tecnico_id)

            # Crear nueva orden
            with atomic_transaction() as session:
                # Verificar que el cliente existe
                cliente = session.query(Cliente).get(cliente_id)
                if not cliente:
                    flash('El cliente seleccionado no existe.', 'error')
                    return redirect(url_for('orden.nueva_orden'))

                # Crear nueva orden
                nueva = Orden(
                    cliente_id=cliente_id,
                    correo=cliente.correo,  # Usar el correo del cliente
                    equipo=request.form['equipo'],
                    marca=request.form['marca'],
                    modelo=request.form['modelo'],
                    descripcion=request.form['descripcion'],
                    procesador=request.form.get('procesador') or None,
                    ram=request.form.get('ram') or None,
                    disco=request.form.get('disco') or None,
                    pantalla=request.form.get('pantalla') or None,
                    estado='Ingresado',
                    fecha_creacion=datetime.now(),
                    tecnico_id=tecnico_id
                )
                session.add(nueva)
                session.flush()

                # Procesar imágenes
                imagenes = request.files.getlist('imagenes')
                imagenes_procesadas = 0
                MAX_IMAGENES = 5
                
                for imagen in imagenes:
                    if imagenes_procesadas >= MAX_IMAGENES:
                        flash('Se ha alcanzado el límite máximo de 5 imágenes.', 'warning')
                        break
                        
                    if imagen and imagen.filename and allowed_file(imagen.filename):
                        try:
                            filename = secure_filename(imagen.filename)
                            timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
                            filename = f"{timestamp}_{filename}"
                            imagen.save(os.path.join('static/uploads/images', filename))
                            nueva_imagen = Imagen(orden_id=nueva.id, filename=filename)
                            session.add(nueva_imagen)
                            imagenes_procesadas += 1
                        except Exception as e:
                            logger.error(f"Error al procesar imagen: {str(e)}")
                            flash(f'Error al procesar la imagen {imagen.filename}.', 'error')
                    elif imagen.filename:
                        flash(f'Formato de archivo no permitido para {imagen.filename}. Use PNG, JPG o GIF.', 'warning')

                # Registrar en historial
                nuevo_evento = Historial(
                    orden_id=nueva.id,
                    usuario_id=current_user.id,
                    descripcion=f"Orden creada por {current_user.username}"
                )
                session.add(nuevo_evento)

                # Enviar correo
                try:
                    enviar_correo(nueva.id, tipo='ingreso')
                    flash('Orden ingresada exitosamente y correo enviado al cliente.', 'success')
                except Exception as e:
                    logger.error(f"Error al enviar correo: {str(e)}")
                    flash('Orden ingresada pero ocurrió un error al enviar el correo.', 'warning')

                return redirect(url_for('orden.ver_orden', orden_id=nueva.id))
            
        except Exception as e:
            logger.error(f"Error al crear orden: {str(e)}")
            flash(f'Error al crear la orden: {str(e)}', 'error')
            return redirect(url_for('orden.nueva_orden'))

    tecnicos = Usuario.query.filter_by(rol='tecnico').all()
    clientes = Cliente.query.all()
    return render_template('orden/orden_form.html', tecnicos=tecnicos, clientes=clientes)

@orden_bp.route('/<int:orden_id>')
@login_required
def ver_orden(orden_id):
    """Ver detalles de una orden específica."""
    try:
        logger.info(f"=== Iniciando carga de orden {orden_id} ===")
        with atomic_transaction() as session:
            # Cargar la orden con sus relaciones
            logger.info(f"Intentando cargar orden básica {orden_id}")
            orden = session.query(Orden).filter(Orden.id == orden_id).first()
            
            if not orden:
                logger.warning(f"Orden {orden_id} no encontrada")
                flash('Orden no encontrada', 'error')
                return redirect(url_for('orden.listar_ordenes'))
            
            logger.info(f"Orden {orden_id} encontrada, cargando relaciones...")
            
            # Cargar las relaciones manualmente
            try:
                session.refresh(orden)
                logger.info("Refresh de orden completado")
            except Exception as e:
                logger.error(f"Error al refrescar orden: {str(e)}")
            
            # Asegurarse de que todas las relaciones estén cargadas
            try:
                if orden.cliente:
                    session.refresh(orden.cliente)
                    logger.info(f"Cliente cargado: {orden.cliente.nombre}")
                if orden.tecnico:
                    session.refresh(orden.tecnico)
                    logger.info(f"Técnico cargado: {orden.tecnico.nombre}")
            except Exception as e:
                logger.error(f"Error al cargar cliente/técnico: {str(e)}")
                
            # Cargar y ordenar el historial
            try:
                logger.info("Cargando historial...")
                historial_query = session.query(Historial).filter(
                    Historial.orden_id == orden_id
                ).order_by(Historial.fecha.desc()).all()
                logger.info(f"Historial cargado: {len(historial_query)} registros")
                
                # Cargar usuarios del historial
                for h in historial_query:
                    if h.usuario:
                        try:
                            session.refresh(h.usuario)
                        except Exception as e:
                            logger.error(f"Error al refrescar usuario de historial: {str(e)}")
            except Exception as e:
                logger.error(f"Error al cargar historial: {str(e)}")
                historial_query = []
            
            # Cargar solicitudes
            try:
                logger.info("Cargando solicitudes...")
                solicitudes = session.query(Solicitud).filter(
                    Solicitud.orden_id == orden_id
                ).all()
                logger.info(f"Solicitudes cargadas: {len(solicitudes)} registros")
                
                # Cargar usuarios de las solicitudes
                for s in solicitudes:
                    if s.usuario:
                        try:
                            session.refresh(s.usuario)
                        except Exception as e:
                            logger.error(f"Error al refrescar usuario de solicitud: {str(e)}")
            except Exception as e:
                logger.error(f"Error al cargar solicitudes: {str(e)}")
                solicitudes = []

            # Cargar correos
            try:
                logger.info("Cargando correos...")
                correos = session.query(CorreoLog).filter(
                    CorreoLog.orden_id == orden_id
                ).order_by(CorreoLog.fecha_envio.desc()).all()
                logger.info(f"Correos cargados: {len(correos)} registros")
            except Exception as e:
                logger.error(f"Error al cargar correos: {str(e)}")
                logger.error(f"Detalles del error de correos: {type(e).__name__}")
                logger.exception("Stacktrace completo del error de correos:")
                correos = []
            
            logger.info("=== Resumen de carga ===")
            logger.info(f"Cliente: {orden.cliente.nombre if orden.cliente else 'No asignado'}")
            logger.info(f"Técnico: {orden.tecnico.nombre if orden.tecnico else 'No asignado'}")
            logger.info(f"Número de imágenes: {len(orden.imagenes)}")
            logger.info(f"Entradas en historial: {len(historial_query)}")
            logger.info(f"Número de solicitudes: {len(solicitudes)}")
            logger.info(f"Número de correos: {len(correos)}")
            logger.info("=== Fin de carga ===")
            
            return render_template(
                'orden/ver_orden.html',
                orden=orden,
                historial=historial_query,
                correos=correos
            )
            
    except Exception as e:
        logger.error(f"Error general al ver orden {orden_id}: {str(e)}")
        logger.error(f"Tipo de error: {type(e).__name__}")
        logger.exception("Stacktrace completo:")
        flash('Error al cargar la orden: ' + str(e), 'error')
        return redirect(url_for('orden.listar_ordenes'))

@orden_bp.route('/<int:orden_id>/actualizar', methods=['POST'])
@login_required
def actualizar_orden(orden_id):
    """Actualizar el estado de una orden."""
    try:
        with atomic_transaction() as session:
            orden = session.query(Orden).get(orden_id)
            if not orden:
                flash('Orden no encontrada', 'error')
                return redirect(url_for('orden.listar_ordenes'))
            
            nuevo_estado = request.form.get('estado')
            if nuevo_estado and nuevo_estado != orden.estado:
                estado_anterior = orden.estado
                orden.estado = nuevo_estado
                orden.fecha_actualizacion = datetime.now()
                
                # Registrar historial
                historial = Historial(
                    orden_id=orden.id,
                    usuario_id=current_user.id,
                    descripcion=f"Cambio de estado de '{estado_anterior}' a '{nuevo_estado}'",
                    fecha=datetime.now()
                )
                session.add(historial)
                
                # Enviar notificación por correo
                try:
                    enviar_correo(orden.id, tipo='actualizacion')
                    flash('Estado actualizado y notificación enviada', 'success')
                except Exception as e:
                    logger.error(f"Error al enviar correo: {str(e)}")
                    flash('Estado actualizado pero hubo un error al enviar la notificación', 'warning')
            
            return redirect(url_for('orden.ver_orden', orden_id=orden.id))
            
    except Exception as e:
        logger.error(f"Error al actualizar orden {orden_id}: {str(e)}")
        flash('Error al actualizar la orden', 'error')
        return redirect(url_for('orden.ver_orden', orden_id=orden_id))

@orden_bp.route('/<int:orden_id>/solicitud', methods=['POST'])
@login_required
def crear_solicitud(orden_id):
    """Crear una nueva solicitud para una orden."""
    try:
        with atomic_transaction() as session:
            orden = session.query(Orden).get(orden_id)
            if not orden:
                flash('Orden no encontrada', 'error')
                return redirect(url_for('orden.listar_ordenes'))
            
            tipo = request.form.get('tipo')
            descripcion = request.form.get('descripcion')
            
            if not tipo or not descripcion:
                flash('Por favor complete todos los campos', 'warning')
                return redirect(url_for('orden.ver_orden', orden_id=orden_id))
            
            # Crear nueva solicitud
            solicitud = Solicitud(
                tipo=tipo,
                descripcion=descripcion,
                orden_id=orden.id,
                usuario_id=current_user.id,
                fecha=datetime.now()
            )
            session.add(solicitud)
            
            # Actualizar estado de la orden según el tipo de solicitud
            if tipo == 'Repuesto':
                orden.estado = 'Esperando Repuestos'
            elif tipo == 'Presupuesto':
                orden.estado = 'En Cotización'
            
            # Registrar en historial
            historial = Historial(
                orden_id=orden.id,
                usuario_id=current_user.id,
                descripcion=f"Nueva solicitud de {tipo.lower()}: {descripcion}",
                fecha=datetime.now()
            )
            session.add(historial)
            
            # Enviar notificación según el tipo
            try:
                if tipo == 'Repuesto':
                    enviar_notificacion_admin('repuesto', orden.id)
                elif tipo == 'Presupuesto':
                    enviar_notificacion_admin('presupuesto', orden.id)
                flash(f'Solicitud de {tipo.lower()} creada y notificación enviada', 'success')
            except Exception as e:
                logger.error(f"Error al enviar notificación: {str(e)}")
                flash(f'Solicitud creada pero hubo un error al enviar la notificación', 'warning')
            
            return redirect(url_for('orden.ver_orden', orden_id=orden_id))
            
    except Exception as e:
        logger.error(f"Error al crear solicitud para orden {orden_id}: {str(e)}")
        flash('Error al crear la solicitud', 'error')
        return redirect(url_for('orden.ver_orden', orden_id=orden_id))

@orden_bp.route('/<int:orden_id>/imagenes', methods=['POST'])
@login_required
def agregar_imagenes(orden_id):
    """Agregar imágenes a una orden."""
    try:
        with atomic_transaction() as session:
            orden = session.query(Orden).get(orden_id)
            if not orden:
                flash('Orden no encontrada', 'error')
                return redirect(url_for('orden.listar_ordenes'))
            
            if 'imagenes' not in request.files:
                flash('No se seleccionaron archivos', 'error')
                return redirect(url_for('orden.ver_orden', orden_id=orden_id))
            
            archivos = request.files.getlist('imagenes')
            imagenes_actuales = len(orden.imagenes)
            
            for archivo in archivos:
                if archivo and allowed_file(archivo.filename):
                    if imagenes_actuales >= 5:
                        flash('Máximo 5 imágenes por orden', 'warning')
                        break
                    
                    filename = secure_filename(archivo.filename)
                    ruta = os.path.join('static/uploads', filename)
                    archivo.save(ruta)
                    
                    imagen = Imagen(
                        orden_id=orden.id,
                        ruta=ruta,
                        nombre=filename
                    )
                    session.add(imagen)
                    imagenes_actuales += 1
            
            flash('Imágenes agregadas correctamente', 'success')
            return redirect(url_for('orden.ver_orden', orden_id=orden_id))
            
    except Exception as e:
        logger.error(f"Error al agregar imágenes a orden {orden_id}: {str(e)}")
        flash('Error al subir las imágenes', 'error')
        return redirect(url_for('orden.ver_orden', orden_id=orden_id))

@orden_bp.route('/<int:orden_id>/pdf')
@login_required
def descargar_pdf(orden_id):
    orden = Orden.query.get_or_404(orden_id)
    try:
        # Generar PDF directamente
        pdf_dir = 'static/pdfs'
        if not os.path.exists(pdf_dir):
            os.makedirs(pdf_dir)
        
        pdf_path = os.path.join(pdf_dir, f'orden_{orden_id}.pdf')
        # Aquí va tu lógica de generación de PDF
        return send_file(pdf_path, as_attachment=True)
    except Exception as e:
        flash('Error al generar el PDF', 'error')
        return redirect(url_for('orden.ver_orden', orden_id=orden_id))

@orden_bp.route('/<int:orden_id>/asignar', methods=['GET', 'POST'])
@login_required
def asignar_tecnico(orden_id):
    orden = Orden.query.get_or_404(orden_id)
    if request.method == 'POST':
        tecnico_id = request.form.get('tecnico_id')
        if tecnico_id:
            orden.tecnico_id = tecnico_id
            db.session.commit()
            flash('Técnico asignado correctamente', 'success')
        return redirect(url_for('orden.ver_orden', orden_id=orden_id))
    
    tecnicos = Usuario.query.filter_by(rol='tecnico').all()
    return render_template('orden/asignar_tecnico.html', orden=orden, tecnicos=tecnicos)

@orden_bp.route('/<int:orden_id>/solicitar', methods=['POST'])
@login_required
def solicitar_repuesto_presupuesto(orden_id):
    orden = Orden.query.get_or_404(orden_id)
    tipo = request.form.get('tipo')
    descripcion = request.form.get('descripcion')
    
    if tipo and descripcion:
        # Crear nueva solicitud
        nueva_solicitud = Solicitud(
            tipo=tipo,
            descripcion=descripcion,
            orden_id=orden.id,
            usuario_id=current_user.id
        )
        db.session.add(nueva_solicitud)
        
        # Actualizar estado de la orden
        if tipo == 'Repuesto':
            orden.estado = 'En Espera de Repuestos'
        elif tipo == 'Presupuesto':
            orden.estado = 'Enviado a Cotización'
            
        # Registrar en el historial
        nuevo_evento = Historial(
            orden_id=orden.id,
            usuario_id=current_user.id,
            descripcion=f"Solicitud de {tipo.lower()} creada: {descripcion}"
        )
        db.session.add(nuevo_evento)
        
        db.session.commit()
        flash(f'Solicitud de {tipo.lower()} creada exitosamente', 'success')
    else:
        flash('Por favor complete todos los campos requeridos', 'error')
    
    return redirect(url_for('orden.ver_orden', orden_id=orden_id))

@orden_bp.route('/<int:orden_id>/eliminar', methods=['POST'])
@login_required
@admin_required
def eliminar_orden(orden_id):
    """Eliminar una orden y todos sus datos asociados."""
    try:
        with atomic_transaction() as session:
            orden = session.query(Orden).get(orden_id)
            if not orden:
                flash('Orden no encontrada', 'error')
                return redirect(url_for('orden.listar_ordenes'))
            
            motivo = request.form.get('motivo_eliminacion')
            if not motivo:
                flash('Debe especificar un motivo para eliminar la orden', 'error')
                return redirect(url_for('orden.listar_ordenes'))

            # Crear registro histórico antes de eliminar
            datos_adicionales = {
                'procesador': orden.procesador,
                'ram': orden.ram,
                'disco': orden.disco,
                'pantalla': orden.pantalla,
                'tecnico': orden.tecnico.username if orden.tecnico else None,
                'historial': [
                    {
                        'fecha': h.fecha.isoformat(),
                        'usuario': h.usuario.username if h.usuario else None,
                        'descripcion': h.descripcion
                    } for h in orden.historial
                ],
                'solicitudes': [
                    {
                        'tipo': s.tipo,
                        'descripcion': s.descripcion,
                        'fecha': s.fecha.isoformat(),
                        'usuario': s.usuario.username if s.usuario else None
                    } for s in orden.solicitudes
                ],
                'correos': [
                    {
                        'destinatario': c.destinatario,
                        'asunto': c.asunto,
                        'fecha': c.fecha_envio.isoformat(),
                        'estado': c.estado
                    } for c in orden.correos
                ] if hasattr(orden, 'correos') else []
            }

            orden_eliminada = OrdenEliminada(
                orden_id_original=orden.id,
                cliente_nombre=orden.cliente.nombre if orden.cliente else None,
                cliente_correo=orden.cliente.correo if orden.cliente else None,
                equipo=orden.equipo,
                marca=orden.marca,
                modelo=orden.modelo,
                descripcion=orden.descripcion,
                estado=orden.estado,
                fecha_creacion_original=orden.fecha_creacion,
                eliminado_por=current_user.username,
                motivo_eliminacion=motivo,
                datos_adicionales=datos_adicionales
            )
            session.add(orden_eliminada)
            
            # Registrar en el log antes de eliminar
            logger.info(f"Eliminando orden #{orden_id} por el usuario {current_user.username}. Motivo: {motivo}")
            
            # Eliminar imágenes físicas
            for imagen in orden.imagenes:
                try:
                    ruta_imagen = os.path.join('static/uploads/images', imagen.filename)
                    if os.path.exists(ruta_imagen):
                        os.remove(ruta_imagen)
                except Exception as e:
                    logger.error(f"Error al eliminar imagen {imagen.filename}: {str(e)}")
            
            # La eliminación en cascada se encargará de eliminar:
            # - Imágenes (registros en BD)
            # - Historial
            # - Solicitudes
            # - Correos
            session.delete(orden)
            
            flash('Orden eliminada exitosamente', 'success')
            return redirect(url_for('orden.listar_ordenes'))
            
    except Exception as e:
        logger.error(f"Error al eliminar orden {orden_id}: {str(e)}")
        flash('Error al eliminar la orden', 'error')
        return redirect(url_for('orden.listar_ordenes'))

@orden_bp.route('/<int:orden_id>/imprimir_etiqueta')
@login_required
def imprimir_etiqueta(orden_id):
    try:
        orden = Orden.query.get_or_404(orden_id)
        printer = ZebraPrinter()
        
        # Generar el código ZPL
        zpl_code = printer.generate_zpl(orden)
        
        # Imprimir la etiqueta
        result = printer.print_label(zpl_code)
        
        if result:
            flash('Etiqueta enviada a la impresora correctamente.', 'success')
        else:
            flash('Error al imprimir la etiqueta. Verifique la conexión con la impresora.', 'error')
            
        return redirect(url_for('orden.ver_orden', orden_id=orden_id))
        
    except Exception as e:
        current_app.logger.error(f"Error al imprimir etiqueta: {str(e)}")
        flash('Error al imprimir la etiqueta.', 'error')
        return redirect(url_for('orden.ver_orden', orden_id=orden_id))

@orden_bp.route('/<int:orden_id>/generar_etiqueta_pdf')
@login_required
def generar_etiqueta_pdf(orden_id):
    """Genera un PDF con la etiqueta para una orden"""
    orden = Orden.query.get_or_404(orden_id)
    
    # Crear instancia de la impresora con la configuración actual
    printer = ZebraPrinter(current_app.config)
    
    # Generar el PDF
    result = printer.print_label(orden)  # En modo de prueba, siempre genera PDF
    
    if isinstance(result, str) and result.endswith('.pdf'):
        # Registrar en el historial
        historial = Historial(
            orden_id=orden.id,
            usuario_id=current_user.id,
            descripcion=f"Se generó un PDF con la etiqueta para la orden #{orden.id}",
            fecha=datetime.now()
        )
        db.session.add(historial)
        db.session.commit()
        
        # Devolver el archivo PDF
        return send_file(
            result,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'etiqueta_orden_{orden.id}.pdf'
        )
    else:
        flash('Error al generar el PDF de la etiqueta.', 'error')
        return redirect(url_for('orden.ver_orden', orden_id=orden_id))

@orden_bp.route('/imprimir_test')
@login_required
@admin_required
def imprimir_test():
    """Imprime una etiqueta de prueba"""
    # Crear instancia de la impresora con la configuración actual
    printer = ZebraPrinter(current_app.config)
    
    # Intentar imprimir la etiqueta de prueba
    result = printer.print_test()
    
    # Si estamos en modo de prueba o PDF, el resultado es la ruta del archivo
    if isinstance(result, str) and result.endswith('.pdf'):
        return send_file(
            result,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='etiqueta_test.pdf'
        )
    
    # Si no es PDF, verificar si la impresión fue exitosa
    if result:
        flash('Etiqueta de prueba enviada correctamente.', 'success')
    else:
        flash('Error al enviar la etiqueta de prueba.', 'error')
    
    return redirect(url_for('orden.listar_ordenes')) 