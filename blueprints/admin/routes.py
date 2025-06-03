from flask import render_template, redirect, url_for, request, flash, jsonify, send_file
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from models import Usuario, Orden, CorreoLog, OrdenEliminada
from extensions import db
from . import admin_bp
from functools import wraps
from datetime import datetime
import os
import csv
from io import StringIO
import logging
from forms import UsuarioForm
from utils.db_context import atomic_transaction
from utils.mail_sender import enviar_correo
import shutil
from utils.decorators import admin_required

logger = logging.getLogger(__name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.rol != 'admin':
            flash('Acceso no autorizado', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    ordenes = Orden.query.all()
    return render_template('dashboard_admin.html', ordenes=ordenes)

@admin_bp.route('/usuarios')
@login_required
@admin_required
def ver_usuarios():
    usuarios = Usuario.query.all()
    return render_template('admin/usuarios.html', usuarios=usuarios)

@admin_bp.route('/usuario/nuevo', methods=['GET', 'POST'])
@login_required
@admin_required
def crear_usuario():
    form = UsuarioForm()
    if form.validate_on_submit():
        usuario = Usuario(
            username=form.username.data,
            email=form.email.data,
            password=generate_password_hash(form.password.data),
            rol=form.rol.data
        )
        db.session.add(usuario)
        db.session.commit()
        flash('Usuario creado exitosamente', 'success')
        return redirect(url_for('admin.ver_usuarios'))
    return render_template('admin/usuario_form.html', form=form)

@admin_bp.route('/usuario/<int:usuario_id>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_usuario(usuario_id):
    usuario = Usuario.query.get_or_404(usuario_id)
    form = UsuarioForm(obj=usuario)
    
    if form.validate_on_submit():
        form.populate_obj(usuario)
        if form.password.data:
            usuario.password = generate_password_hash(form.password.data)
        db.session.commit()
        flash('Usuario actualizado exitosamente', 'success')
        return redirect(url_for('admin.ver_usuarios'))
        
    return render_template('admin/usuario_form.html', usuario=usuario, form=form)

@admin_bp.route('/correos')
@login_required
@admin_required
def ver_correos():
    """Vista para ver el historial de correos enviados."""
    try:
        # Obtener los correos ordenados por fecha de envío descendente
        correos = CorreoLog.query\
            .order_by(CorreoLog.fecha_envio.desc())\
            .all()
        
        return render_template(
            'admin/correos.html',
            correos=correos,
            title='Historial de Correos'
        )
        
    except Exception as e:
        logger.error(f"Error al cargar historial de correos: {str(e)}")
        flash('Error al cargar el historial de correos', 'error')
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/correos/<int:correo_id>')
@login_required
@admin_required
def ver_correo(correo_id):
    """Vista para ver el detalle de un correo específico."""
    try:
        with atomic_transaction() as session:
            # Obtener el correo específico
            correo = session.query(CorreoLog).get(correo_id)
            if not correo:
                flash('Correo no encontrado', 'error')
                return redirect(url_for('admin.ver_correos'))
            
            return render_template(
                'admin/ver_correo.html',
                correo=correo,
                title='Detalle de Correo'
            )
            
    except Exception as e:
        logger.error(f"Error al cargar detalle de correo {correo_id}: {str(e)}")
        flash('Error al cargar el detalle del correo', 'error')
        return redirect(url_for('admin.ver_correos'))

@admin_bp.route('/correos/reenviar/<int:correo_id>', methods=['POST'])
@login_required
@admin_required
def reenviar_correo(correo_id):
    """Reenviar un correo específico."""
    try:
        with atomic_transaction() as session:
            # Obtener el correo a reenviar
            correo = session.query(CorreoLog).get(correo_id)
            if not correo:
                flash('Correo no encontrado', 'error')
                return redirect(url_for('admin.ver_correos'))
            
            # Reenviar el correo
            if correo.orden_id:
                enviar_correo(correo.orden_id, tipo='reenvio')
                flash('Correo reenviado correctamente', 'success')
            else:
                flash('No se puede reenviar este correo', 'error')
            
            return redirect(url_for('admin.ver_correo', correo_id=correo_id))
            
    except Exception as e:
        logger.error(f"Error al reenviar correo {correo_id}: {str(e)}")
        flash('Error al reenviar el correo', 'error')
        return redirect(url_for('admin.ver_correos'))

@admin_bp.route('/correos/exportar')
@login_required
@admin_required
def exportar_correos():
    """Exportar historial de correos a CSV."""
    try:
        with atomic_transaction() as session:
            correos = session.query(CorreoLog)\
                .order_by(CorreoLog.fecha_envio.desc())\
                .all()
            
            si = StringIO()
            cw = csv.writer(si)
            cw.writerow(['Fecha', 'Orden ID', 'Destinatario', 'Asunto', 'Estado', 'Error'])
            
            for correo in correos:
                cw.writerow([
                    correo.fecha_envio.strftime('%d/%m/%Y %H:%M:%S'),
                    correo.orden_id or '',
                    correo.destinatario,
                    correo.asunto,
                    correo.estado,
                    correo.error or ''
                ])
            
            output = si.getvalue()
            si.close()
            
            return send_file(
                StringIO(output),
                mimetype='text/csv',
                as_attachment=True,
                download_name=f'correos_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            )
    except Exception as e:
        logger.error(f"Error al exportar correos: {str(e)}")
        flash('Error al exportar los correos', 'error')
        return redirect(url_for('admin.ver_correos'))

@admin_bp.route('/logs')
@login_required
@admin_required
def ver_logs_sistema():
    # Obtener los logs del sistema desde el archivo de log
    log_entries = []
    try:
        with open('logs/app.log', 'r') as f:
            for line in f:
                try:
                    # Parsear cada línea del log
                    parts = line.split(' - ')
                    timestamp = datetime.strptime(parts[0], '%Y-%m-%d %H:%M:%S,%f')
                    level = parts[1]
                    module = parts[2]
                    message = ' - '.join(parts[3:]).strip()
                    
                    # Extraer usuario e IP si están disponibles
                    user = None
                    ip = None
                    if '[User:' in message:
                        user = message.split('[User:')[1].split(']')[0].strip()
                    if '[IP:' in message:
                        ip = message.split('[IP:')[1].split(']')[0].strip()
                    
                    log_entries.append({
                        'timestamp': timestamp,
                        'level': level,
                        'module': module,
                        'message': message,
                        'user': user,
                        'ip_address': ip
                    })
                except Exception as e:
                    continue
    except FileNotFoundError:
        pass
    
    return render_template('admin/logs_sistema.html', logs=log_entries)

@admin_bp.route('/logs/descargar')
@login_required
@admin_required
def descargar_logs():
    try:
        return send_file(
            'logs/app.log',
            mimetype='text/plain',
            as_attachment=True,
            download_name=f'sistema_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        )
    except FileNotFoundError:
        return jsonify({'error': 'Archivo de log no encontrado'}), 404

@admin_bp.route('/logs/limpiar', methods=['POST'])
@login_required
@admin_required
def limpiar_logs():
    """Limpia el archivo de logs manteniendo un backup."""
    try:
        log_file = 'logs/app.log'
        backup_dir = 'logs/backups'
        
        # Crear directorio de backups si no existe
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        # Verificar si existe el archivo de logs
        if not os.path.exists(log_file):
            return jsonify({
                'status': 'error',
                'message': 'No se encontró el archivo de logs'
            }), 404
        
        # Crear nombre para el backup
        backup_name = f'app_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        backup_path = os.path.join(backup_dir, backup_name)
        
        # Hacer backup del archivo actual
        shutil.copy2(log_file, backup_path)
        
        # Limpiar el archivo de logs
        with open(log_file, 'w') as f:
            f.write(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] INFO: Log limpiado y respaldado como {backup_name}\n')
        
        logger.info(f'Archivo de logs limpiado y respaldado como {backup_name}')
        
        return jsonify({
            'status': 'success',
            'message': 'Logs limpiados correctamente',
            'backup': backup_name
        })
        
    except Exception as e:
        logger.error(f'Error al limpiar logs: {str(e)}')
        return jsonify({
            'status': 'error',
            'message': f'Error al limpiar logs: {str(e)}'
        }), 500

@admin_bp.route('/ordenes_eliminadas')
@login_required
@admin_required
def ordenes_eliminadas():
    """Vista para mostrar el historial de órdenes eliminadas."""
    try:
        ordenes = OrdenEliminada.query.order_by(OrdenEliminada.fecha_eliminacion.desc()).all()
        return render_template('admin/ordenes_eliminadas.html', ordenes=ordenes)
    except Exception as e:
        logger.error(f"Error al cargar órdenes eliminadas: {str(e)}")
        flash('Error al cargar el historial de órdenes eliminadas', 'error')
        return redirect(url_for('admin.index'))

@admin_bp.route('/ordenes_eliminadas/<int:id>/detalles')
@login_required
@admin_required
def detalles_orden_eliminada(id):
    """Obtener detalles de una orden eliminada en formato JSON."""
    try:
        orden = OrdenEliminada.query.get_or_404(id)
        return jsonify({
            'id': orden.id,
            'orden_id_original': orden.orden_id_original,
            'cliente_nombre': orden.cliente_nombre,
            'cliente_correo': orden.cliente_correo,
            'equipo': orden.equipo,
            'marca': orden.marca,
            'modelo': orden.modelo,
            'descripcion': orden.descripcion,
            'estado': orden.estado,
            'fecha_creacion_original': orden.fecha_creacion_original.isoformat(),
            'fecha_eliminacion': orden.fecha_eliminacion.isoformat(),
            'eliminado_por': orden.eliminado_por,
            'motivo_eliminacion': orden.motivo_eliminacion,
            'datos_adicionales': orden.datos_adicionales
        })
    except Exception as e:
        logger.error(f"Error al obtener detalles de orden eliminada {id}: {str(e)}")
        return jsonify({'error': 'Error al obtener detalles'}), 500 