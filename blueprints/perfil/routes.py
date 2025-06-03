from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from models import Usuario, Orden, Historial
from extensions import db
from . import perfil_bp

@perfil_bp.route('/mi-perfil', methods=['GET', 'POST'])
@login_required
def mi_perfil():
    if request.method == 'POST':
        # Actualizar información del perfil
        current_user.nombre = request.form.get('nombre')
        current_user.email = request.form.get('email')
        
        # Si se proporciona una nueva contraseña
        nueva_password = request.form.get('nueva_password')
        if nueva_password:
            if check_password_hash(current_user.password, request.form.get('password_actual')):
                current_user.password = generate_password_hash(nueva_password)
                flash('Contraseña actualizada exitosamente', 'success')
            else:
                flash('Contraseña actual incorrecta', 'danger')
                return redirect(url_for('perfil.mi_perfil'))
        
        db.session.commit()
        flash('Perfil actualizado exitosamente', 'success')
        return redirect(url_for('perfil.mi_perfil'))
    
    return render_template('perfil/mi_perfil.html')

@perfil_bp.route('/configuracion', methods=['GET', 'POST'])
@login_required
def configuracion():
    if request.method == 'POST':
        # Actualizar preferencias
        current_user.notificaciones_email = 'notificaciones_email' in request.form
        current_user.tema_oscuro = 'tema_oscuro' in request.form
        current_user.idioma = request.form.get('idioma', 'es')
        
        db.session.commit()
        flash('Configuración actualizada exitosamente', 'success')
        return redirect(url_for('perfil.configuracion'))
    
    return render_template('perfil/configuracion.html')

@perfil_bp.route('/actividad')
@login_required
def actividad():
    # Obtener historial de actividad del usuario
    historial = Historial.query.filter_by(usuario_id=current_user.id)\
        .order_by(Historial.fecha.desc()).limit(50).all()
    
    # Obtener estadísticas
    total_ordenes = len(current_user.ordenes_creadas) + len(current_user.ordenes_asignadas)
    
    return render_template('perfil/actividad.html', 
                         historial=historial,
                         total_ordenes=total_ordenes) 