from app import create_app
from models import CorreoLog

app = create_app()
with app.app_context():
    logs = CorreoLog.query.order_by(CorreoLog.fecha_envio.desc()).limit(5).all()
    for log in logs:
        print(f'ID: {log.id}, Estado: {log.estado}, Error: {log.error}') 