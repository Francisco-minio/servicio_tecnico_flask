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

def enviar_correo(objeto, tipo='ingreso'):
    """
    Envía correos para distintos tipos de notificaciones:
    - ingreso: notifica ingreso de orden
    - cerrada: notifica cierre de orden
    - solicitud_cotizacion: notifica nueva solicitud de cotización
    """
    asunto = ""
    cuerpo = ""
    destinatario = ""

    if tipo in ['ingreso', 'cerrada']:
        orden = objeto
        if not orden or not hasattr(orden, 'correo') or not orden.correo:
            print("[ERROR] Orden inválida o sin correo.")
            return

        destinatario = orden.correo

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

    elif tipo == 'solicitud_cotizacion':
        solicitud = objeto
    if not solicitud or not hasattr(solicitud, 'correo_encargado'):
        print("[ERROR] Solicitud inválida o sin correo.")
        return

    # Verificar si hay una orden asociada
    orden = solicitud.orden if hasattr(solicitud, 'orden') else None
    destinatario = solicitud.correo_encargado

    if orden:
        asunto = f"Solicitud de cotización para Orden #{orden.id}"
        cuerpo = f"""Estimado/a encargado,

Se ha generado una nueva solicitud de cotización.

Detalles:
- Solicitud ID: {solicitud.id}
- Orden ID: {orden.id}
- Equipo: {orden.equipo}
- Descripción de la solicitud: {solicitud.descripcion}
- Fecha: {solicitud.fecha_creacion.strftime('%d-%m-%Y %H:%M')}

Por favor, revise esta solicitud a la brevedad.
"""
    else:
        asunto = "Solicitud de cotización sin orden asociada"
        cuerpo = f"""Estimado/a encargado,

Se ha generado una nueva solicitud de cotización sin orden asociada.

Detalles:
- Solicitud ID: {solicitud.id}
- Quien Solicita: {solicitud.usuario.username}
- Descripción de la solicitud: {solicitud.descripcion}
- Fecha: {solicitud.fecha_creacion.strftime('%d-%m-%Y %H:%M')}

Por favor, revise esta solicitud a la brevedad.
"""

    # Crear mensaje
    msg = MIMEMultipart()
    msg['From'] = SMTP_USER
    msg['To'] = destinatario
    msg['Subject'] = asunto
    msg.attach(MIMEText(cuerpo, 'plain', _charset='utf-8'))

    # Log
    log = CorreoLog(
        orden_id=getattr(objeto, 'orden_id', None) or getattr(objeto, 'id', None),
        destinatario=destinatario,
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
        print(f"[CORREO ENVIADO] A: {destinatario}, Asunto: {asunto}", flush=True)

    except Exception as e:
        log.estado = "Error"
        log.error = str(e)
        print(f"[ERROR AL ENVIAR CORREO] {e}", flush=True)

    db.session.add(log)
    db.session.commit()