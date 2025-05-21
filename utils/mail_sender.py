# utils/mail_sender.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from celery_app import celery

SMTP_HOST = 'mail.smtp2go.com'
SMTP_PORT = 2525
SMTP_USER = os.environ.get('SMTP_USER')
SMTP_PASS = os.environ.get('SMTP_PASS')

@celery.task
def enviar_correo_task(cliente_nombre, orden_id, equipo, estado, fecha_creacion_str, destinatario_email):
    if not SMTP_USER or not SMTP_PASS:
        # This will be logged by Celery worker
        print("CRITICAL: SMTP_USER or SMTP_PASS not set. Cannot send email.")
        # Optional: raise an error to have Celery retry or mark as failed
        raise ValueError("SMTP_USER and SMTP_PASS environment variables must be set for task execution.")

    asunto = "Equipo ingresado al servicio técnico"
    cuerpo = f"""Estimado/a {cliente_nombre},

Su equipo ha sido ingresado correctamente al servicio técnico.

Detalles:
- Orden ID: {orden_id}
- Equipo: {equipo}
- Estado: {estado}
- Fecha: {fecha_creacion_str}

Gracias por confiar en nosotros.
"""
    msg = MIMEMultipart()
    msg['From'] = SMTP_USER
    msg['To'] = destinatario_email
    msg['Subject'] = asunto
    msg.attach(MIMEText(cuerpo, 'plain'))

    try:
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)
        server.quit()
        return f"Email sent to {destinatario_email} for order {orden_id}"
    except Exception as e:
        print(f"Failed to send email for order {orden_id}: {e}")
        # Re-raise the exception so Celery can handle it (e.g., retry)
        raise

@celery.task
def enviar_notificacion_admin_task(subject, html_body, recipient):
    if not SMTP_USER or not SMTP_PASS:
        # This will be logged by Celery worker
        print("CRITICAL: SMTP_USER or SMTP_PASS not set. Cannot send admin notification.")
        # Optional: raise an error to have Celery retry or mark as failed
        raise ValueError("SMTP_USER and SMTP_PASS environment variables must be set for task execution.")

    msg = MIMEMultipart()
    msg['From'] = SMTP_USER
    msg['To'] = recipient
    msg['Subject'] = subject
    msg.attach(MIMEText(html_body, 'html')) # Send as HTML

    try:
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)
        server.quit()
        return f"Admin notification '{subject}' sent to {recipient}"
    except Exception as e:
        print(f"Failed to send admin notification email to {recipient}: {e}")
        # Re-raise the exception so Celery can handle it
        raise
