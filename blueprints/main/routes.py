from flask import redirect, url_for
from flask_login import current_user
from . import main_bp

@main_bp.route('/')
def index():
    """
    Ruta principal que redirige según el estado de autenticación:
    - Usuarios autenticados: al dashboard o lista de órdenes según rol
    - Usuarios no autenticados: a la página de login
    """
    if current_user.is_authenticated:
        if current_user.rol == 'admin':
            return redirect(url_for('admin.dashboard'))
        else:
            return redirect(url_for('orden.listar_ordenes'))
    return redirect(url_for('auth.login')) 