from flask import Blueprint

cliente_bp = Blueprint('cliente', __name__)

from . import routes 