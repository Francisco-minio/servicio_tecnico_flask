from flask import render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from datetime import datetime
from models import SolicitudCotizacion, Cliente, Orden, Usuario
from extensions import db
from . import cotizacion_bp

@cotizacion_bp.route('/nueva', methods=['GET', 'POST'])
@cotizacion_bp.route('/nueva/<int:orden_id>', methods=['GET', 'POST'])
@login_required
def nueva(orden_id=None):
    if request.method == 'POST':
        # Obtener datos del formulario
        asunto = request.form.get('asunto')
        descripcion = request.form.get('descripcion')
        urgencia = request.form.get('urgencia')
        enlace_compra = request.form.get('enlace_compra')
        cliente_id = request.form.get('cliente_id')
        orden_id = request.form.get('orden_id') or orden_id

        # Crear nueva solicitud
        nueva_solicitud = SolicitudCotizacion(
            asunto=asunto,
            descripcion=descripcion,
            usuario_id=current_user.id,
            cliente_id=cliente_id,
            orden_id=orden_id,
            fecha_creacion=datetime.now()
        )

        db.session.add(nueva_solicitud)
        db.session.commit()

        flash('Solicitud de cotización creada exitosamente', 'success')
        return redirect(url_for('admin.dashboard'))

    # GET: Mostrar formulario
    orden = None
    if orden_id:
        orden = Orden.query.get_or_404(orden_id)
        
    clientes = Cliente.query.all()
    ordenes = Orden.query.all()
    return render_template('cotizacion_form.html', 
                         clientes=clientes, 
                         ordenes=ordenes, 
                         orden_preseleccionada=orden)

@cotizacion_bp.route('/listar')
@login_required
def listar():
    cotizaciones = SolicitudCotizacion.query.all()
    return render_template('cotizacion/listar_cotizaciones.html', cotizaciones=cotizaciones) 