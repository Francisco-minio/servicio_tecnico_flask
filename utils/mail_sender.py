import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from models import CorreoLog  # Asegúrate de importar correctamente
from extensions import db
import os

SMTP_HOST = 'mail.smtp2go.com'
SMTP_PORT = 2525
SMTP_USER = os.environ.get('SMTP_USER', 'no-reply@backupcode.cl')
SMTP_PASS = os.environ.get('SMTP_PASS', 'NtUBu2TME0f22mHQ')

def enviar_correo(orden, tipo='ingreso'):
    if tipo == 'ingreso':
        asunto = "Equipo ingresado al servicio técnico"
        cuerpo = f"""Estimado/a {orden.cliente.nombre},

Su equipo ha sido ingresado correctamente al servicio técnico.

Detalles:
- Orden ID: {orden.id}
- Equipo: {orden.equipo}
- Estado: {orden.estado}
- Fecha: {orden.fecha_creacion.strftime('%d-%m-%Y %H:%M')}

Gracias por confiar en nosotros.
"""
    elif tipo == 'cerrada':
        asunto = "Orden de servicio cerrada"
        cuerpo = f"""Estimado/a {orden.cliente.nombre},

Su orden de servicio ha sido finalizada y cerrada.

Detalles:
- Orden ID: {orden.id}
- Equipo: {orden.equipo}
- Estado: {orden.estado}
- Fecha de cierre: {orden.fecha_cierre.strftime('%d-%m-%Y %H:%M')}

Gracias por confiar en nuestro servicio técnico.
"""
    else:
        asunto = "Notificación del servicio técnico"
        cuerpo = "Su orden ha sido actualizada."

    msg = MIMEMultipart()
    msg['From'] = SMTP_USER
    msg['To'] = orden.correo
    msg['Subject'] = asunto
    msg.attach(MIMEText(cuerpo, 'plain'))

    log = CorreoLog(
        orden_id=orden.id,
        destinatario=orden.correo,
        asunto=asunto,
        cuerpo=cuerpo,
        fecha_envio=datetime.utcnow(),
        estado="Pendiente"
    )

    try:
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)
        server.quit()

        log.estado = "Enviado"
    except Exception as e:
        log.estado = "Error"
        print(f"[CORREO ENVIADO] A: {orden.correo}, Asunto: {asunto}", flush=True)
        log.error = str(e)
        print(f"[ERROR AL ENVIAR CORREO] {e}", flush=True)

    db.session.add(log)
    db.session.commit()