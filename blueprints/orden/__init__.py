from flask import Blueprint

orden_bp = Blueprint('orden', __name__)

from . import routes 