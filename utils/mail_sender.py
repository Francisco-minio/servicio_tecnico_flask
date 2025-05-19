import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

SMTP_HOST = 'mail.smtp2go.com'
SMTP_PORT = 2525
SMTP_USER = os.environ.get('SMTP_USER', 'no-reply@backupcode.cl')
SMTP_PASS = os.environ.get('SMTP_PASS', 'NtUBu2TME0f22mHQ')

def enviar_correo(orden):
    asunto = "Equipo ingresado al servicio técnico"
    cuerpo = f"""Estimado/a {orden.cliente},

Su equipo ha sido ingresado correctamente al servicio técnico.

Detalles:
- Orden ID: {orden.id}
- Equipo: {orden.equipo}
- Estado: {orden.estado}
- Fecha: {orden.fecha_creacion.strftime('%d-%m-%Y %H:%M')}

Gracias por confiar en nosotros.
"""

    msg = MIMEMultipart()
    msg['From'] = SMTP_USER
    msg['To'] = orden.correo
    msg['Subject'] = asunto
    msg.attach(MIMEText(cuerpo, 'plain'))

    server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10)
    server.starttls()
    server.login(SMTP_USER, SMTP_PASS)
    server.send_message(msg)
    server.quit()
