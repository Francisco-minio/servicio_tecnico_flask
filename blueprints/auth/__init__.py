from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from models import Usuario
import logging

logger = logging.getLogger(__name__)

# Crear el blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # Si el usuario ya está autenticado, redirigir
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Por favor ingrese usuario y contraseña', 'warning')
            return render_template('auth/login.html')
            
        try:
            user = Usuario.query.filter_by(username=username).first()
            
            if user and check_password_hash(user.password, password):
                login_user(user)
                logger.info(f'Usuario {username} ha iniciado sesión exitosamente')
                
                # Obtener la página siguiente o redirigir a la página principal
                next_page = request.args.get('next')
                if next_page:
                    return redirect(next_page)
                return redirect(url_for('index'))
            else:
                flash('Usuario o contraseña incorrectos', 'danger')
                logger.warning(f'Intento fallido de inicio de sesión para el usuario {username}')
                
        except Exception as e:
            logger.error(f'Error durante el inicio de sesión: {str(e)}')
            flash('Error al procesar el inicio de sesión. Por favor, inténtelo de nuevo.', 'danger')
            
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    if current_user.is_authenticated:
        username = current_user.username
        logout_user()
        logger.info(f'Usuario {username} ha cerrado sesión')
        flash('Has cerrado sesión exitosamente', 'success')
    return redirect(url_for('auth.login')) 