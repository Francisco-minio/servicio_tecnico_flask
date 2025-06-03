from flask import Blueprint

cotizacion_bp = Blueprint('cotizacion', __name__)

from . import routes 