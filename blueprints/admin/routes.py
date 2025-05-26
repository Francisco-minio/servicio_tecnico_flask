from flask import render_template, redirect, url_for, request, flash, jsonify, send_file
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from models import Usuario, Orden, CorreoLog
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
    try:
        # Hacer backup del archivo actual
        if os.path.exists('logs/app.log'):
            backup_name = f'logs/app_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log.bak'
            os.rename('logs/app.log', backup_name)
        
        # Crear nuevo archivo de log
        open('logs/app.log', 'w').close()
        
        # Registrar la acción de limpieza
        logging.info(f'Logs limpiados por {current_user.username} [User:{current_user.username}] [IP:{request.remote_addr}]')
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}) 