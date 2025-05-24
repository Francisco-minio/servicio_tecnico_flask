from flask import render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from models import Usuario, Orden, CorreoLog
from extensions import db
from . import admin_bp
from functools import wraps

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
    if request.method == 'POST':
        usuario = Usuario(
            username=request.form['username'],
            password=generate_password_hash(request.form['password']),
            rol=request.form['rol']
        )
        db.session.add(usuario)
        db.session.commit()
        flash('Usuario creado exitosamente', 'success')
        return redirect(url_for('admin.ver_usuarios'))
    return render_template('admin/usuario_form.html')

@admin_bp.route('/usuario/<int:usuario_id>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_usuario(usuario_id):
    usuario = Usuario.query.get_or_404(usuario_id)
    if request.method == 'POST':
        usuario.username = request.form['username']
        if request.form.get('password'):
            usuario.password = generate_password_hash(request.form['password'])
        usuario.rol = request.form['rol']
        db.session.commit()
        flash('Usuario actualizado exitosamente', 'success')
        return redirect(url_for('admin.ver_usuarios'))
    return render_template('admin/usuario_form.html', usuario=usuario)

@admin_bp.route('/correos')
@login_required
@admin_required
def ver_logs_correos():
    logs = CorreoLog.query.order_by(CorreoLog.fecha_envio.desc()).all()
    return render_template('admin/correos.html', logs=logs) 