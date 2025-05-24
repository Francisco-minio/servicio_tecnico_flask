# utils/mail_sender.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from models import CorreoLog
from extensions import db
import os
from celery_app import celery
from flask_mail import Message

SMTP_HOST = 'mail.smtp2go.com'
SMTP_PORT = 2525
SMTP_USER = os.environ.get('SMTP_USER')
SMTP_PASS = os.environ.get('SMTP_PASS')

@celery.task
def enviar_correo_task(orden_id, tipo='ingreso'):
    """Envía un correo relacionado con una orden."""
    from app import create_app
    app = create_app()
    
    with app.app_context():
        from models import Orden, CorreoLog
        from extensions import mail, db
        
        orden = Orden.query.get(orden_id)
        if not orden:
            return False
            
        templates = {
            'ingreso': {
                'asunto': 'Equipo ingresado al servicio técnico',
                'mensaje': f"""
                    Estimado/a {orden.cliente.nombre},

                    Su equipo ha sido ingresado correctamente al servicio técnico.

                    Detalles:
                    - Orden ID: {orden.id}
                    - Equipo: {orden.equipo}
                    - Estado: {orden.estado}
                    - Fecha: {orden.fecha_creacion.strftime('%d-%m-%Y %H:%M')}

                    Gracias por confiar en nosotros.
                """
            },
            'actualización': {
                'asunto': 'Actualización de su orden de servicio',
                'mensaje': f"""
                    Estimado/a {orden.cliente.nombre},

                    Su orden de servicio ha sido actualizada.

                    Estado actual: {orden.estado}
                    
                    Puede revisar los detalles en nuestro sistema.

                    Gracias por su preferencia.
                """
            }
        }
        
        template = templates.get(tipo, templates['ingreso'])
        
        try:
            msg = Message(
                subject=template['asunto'],
                recipients=[orden.correo],
                body=template['mensaje']
            )
            mail.send(msg)
            
            # Registrar el envío
            log = CorreoLog(
                orden_id=orden.id,
                tipo=tipo,
                destinatario=orden.correo,
                fecha_envio=datetime.now(),
                exitoso=True
            )
            db.session.add(log)
            db.session.commit()
            
            return True
        except Exception as e:
            app.logger.error(f"Error al enviar correo: {str(e)}")
            return False

@celery.task
def enviar_notificacion_admin_task(orden_id, tipo, mensaje):
    """Envía una notificación al administrador."""
    from app import create_app
    app = create_app()
    
    with app.app_context():
        from extensions import mail
        
        try:
            msg = Message(
                subject=f'Notificación de Orden #{orden_id}',
                recipients=[app.config['CORREO_ADMIN']],
                body=f"""
                    Tipo: {tipo}
                    Orden: #{orden_id}
                    Mensaje: {mensaje}
                """
            )
            mail.send(msg)
            return True
        except Exception as e:
            app.logger.error(f"Error al enviar notificación: {str(e)}")
            return False

    