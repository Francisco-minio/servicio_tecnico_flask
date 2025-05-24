from flask import render_template, redirect, url_for, request, flash, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from datetime import datetime
import os
from models import Orden, Cliente, Imagen, Usuario, Historial, Solicitud
from extensions import db
from utils.pdf_generator import generar_pdf_task
from utils.mail_sender import enviar_correo_task
from . import orden_bp

@orden_bp.route('/')
@login_required
def listar_ordenes():
    ordenes = Orden.query.all()
    return render_template('orden/listar_ordenes.html', ordenes=ordenes)

@orden_bp.route('/nueva', methods=['GET', 'POST'])
@login_required
def nueva_orden():
    if request.method == 'POST':
        cliente_nombre = request.form['cliente']
        cliente_correo = request.form['correo']

        cliente_existente = Cliente.query.filter_by(nombre=cliente_nombre, correo=cliente_correo).first()
        if cliente_existente:
            cliente_id = cliente_existente.id
        else:
            nuevo_cliente = Cliente(nombre=cliente_nombre, correo=cliente_correo)
            db.session.add(nuevo_cliente)
            db.session.commit()
            cliente_id = nuevo_cliente.id

        nueva = Orden(
            cliente_id=cliente_id,
            correo=cliente_correo,
            equipo=request.form['equipo'],
            marca=request.form['marca'],
            modelo=request.form['modelo'],
            descripcion=request.form['descripcion'],
            procesador=request.form.get('procesador'),
            ram=request.form.get('ram'),
            disco=request.form.get('disco'),
            pantalla=request.form.get('pantalla'),
            estado='Ingresado',
            fecha_creacion=datetime.now(),
            usuario_id=current_user.id,
            tecnico_id=request.form.get('tecnico_id')
        )

        db.session.add(nueva)
        db.session.commit()

        # Procesar imágenes
        imagenes = request.files.getlist('imagenes')
        for imagen in imagenes:
            if imagen and imagen.filename:
                filename = secure_filename(imagen.filename)
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
                filename = f"{timestamp}_{filename}"
                imagen.save(os.path.join('static/uploads', filename))
                nueva_imagen = Imagen(orden_id=nueva.id, filename=filename)
                db.session.add(nueva_imagen)

        db.session.commit()

        # Enviar correo
        try:
            enviar_correo_task.delay(nueva.id, tipo='ingreso')
            flash('Orden ingresada exitosamente y correo enviado al cliente.', 'success')
        except Exception as e:
            flash('Orden ingresada pero ocurrió un error al enviar el correo.', 'warning')

        return redirect(url_for('orden.ver_orden', orden_id=nueva.id))

    tecnicos = Usuario.query.filter_by(rol='tecnico').all()
    clientes = Cliente.query.all()
    return render_template('orden/orden_form.html', tecnicos=tecnicos, clientes=clientes)

@orden_bp.route('/<int:orden_id>', methods=['GET', 'POST'])
@login_required
def ver_orden(orden_id):
    orden = Orden.query.get_or_404(orden_id)
    
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
            flash('Comentario agregado correctamente', 'success')
        return redirect(url_for('orden.ver_orden', orden_id=orden_id))

    # Obtener historial ordenado por fecha descendente
    historial = Historial.query.filter_by(orden_id=orden_id).order_by(Historial.fecha.desc()).all()
    return render_template('orden/ver_orden.html', orden=orden, historial=historial)

@orden_bp.route('/<int:orden_id>/estado', methods=['POST'])
@login_required
def actualizar_estado(orden_id):
    orden = Orden.query.get_or_404(orden_id)
    nuevo_estado = request.form.get('estado')
    if nuevo_estado and nuevo_estado != orden.estado:
        estado_anterior = orden.estado
        orden.estado = nuevo_estado
        
        # Registrar el cambio en el historial
        nuevo_evento = Historial(
            orden_id=orden.id,
            usuario_id=current_user.id,
            descripcion=f"Estado actualizado de '{estado_anterior}' a '{nuevo_estado}'"
        )
        db.session.add(nuevo_evento)
        db.session.commit()
        flash('Estado actualizado correctamente', 'success')
    return redirect(url_for('orden.ver_orden', orden_id=orden_id))

@orden_bp.route('/<int:orden_id>/pdf')
@login_required
def descargar_pdf(orden_id):
    orden = Orden.query.get_or_404(orden_id)
    try:
        pdf_path = generar_pdf_task.delay(orden_id).get()
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