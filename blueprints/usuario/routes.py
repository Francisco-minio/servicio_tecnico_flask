from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import Usuario
from extensions import db
from . import usuario_bp

@usuario_bp.route('/perfil')
@login_required
def perfil():
    """Vista del perfil del usuario."""
    return render_template('usuario/perfil.html')

@usuario_bp.route('/tecnicos')
@login_required
def listar_tecnicos():
    """Lista todos los técnicos."""
    tecnicos = Usuario.query.filter_by(rol='tecnico').all()
    return render_template('usuario/listar_tecnicos.html', tecnicos=tecnicos)

@usuario_bp.route('/tecnico/<int:tecnico_id>')
@login_required
def ver_tecnico(tecnico_id):
    """Ver detalles de un técnico."""
    tecnico = Usuario.query.get_or_404(tecnico_id)
    return render_template('usuario/ver_tecnico.html', tecnico=tecnico)

@usuario_bp.route('/tecnico/<int:tecnico_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_tecnico(tecnico_id):
    tecnico = Usuario.query.get_or_404(tecnico_id)
    if request.method == 'POST':
        tecnico.nombre = request.form.get('nombre')
        tecnico.email = request.form.get('email')
        tecnico.activo = bool(request.form.get('activo'))
        db.session.commit()
        flash('Información del técnico actualizada correctamente', 'success')
        return redirect(url_for('usuario.ver_tecnico', tecnico_id=tecnico.id))
    return render_template('usuario/editar_tecnico.html', tecnico=tecnico) 