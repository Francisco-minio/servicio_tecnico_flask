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

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.rol != 'admin':
            flash('Acceso no autorizado', 'danger')
            return redirect(url_for('index'))
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
            correo=form.correo.data,
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
def ver_logs_correos():
    logs = CorreoLog.query.order_by(CorreoLog.fecha_envio.desc()).all()
    return render_template('admin/correos.html', logs=logs)

@admin_bp.route('/correos/<int:log_id>')
@login_required
@admin_required
def ver_detalle_correo(log_id):
    log = CorreoLog.query.get_or_404(log_id)
    return jsonify({
        'asunto': log.asunto,
        'cuerpo': log.cuerpo,
        'error': log.error
    })

@admin_bp.route('/correos/exportar')
@login_required
@admin_required
def exportar_logs_correos():
    logs = CorreoLog.query.order_by(CorreoLog.fecha_envio.desc()).all()
    
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['Fecha', 'Orden ID', 'Destinatario', 'Asunto', 'Estado', 'Error'])
    
    for log in logs:
        cw.writerow([
            log.fecha_envio.strftime('%d/%m/%Y %H:%M:%S'),
            log.orden_id or '',
            log.destinatario,
            log.asunto,
            log.estado,
            log.error or ''
        ])
    
    output = si.getvalue()
    si.close()
    
    return send_file(
        StringIO(output),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'logs_correos_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    )

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