from flask import Blueprint

# Crear el blueprint con el prefijo de URL correcto
orden_bp = Blueprint('orden', __name__, url_prefix='/orden')

from . import routes 