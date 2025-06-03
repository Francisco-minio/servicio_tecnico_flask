import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class EmailSender:
    def __init__(self):
        self.smtp_server = os.environ.get('MAIL_SERVER', 'mail.smtp2go.com')
        self.smtp_port = int(os.environ.get('MAIL_PORT', 2525))
        self.smtp_user = os.environ.get('SMTP_USER')
        self.smtp_pass = os.environ.get('SMTP_PASS')
        self.sender_email = os.environ.get('MAIL_DEFAULT_SENDER')

    def send_email(self, to_email, subject, body, is_html=True):
        """
        Envía un correo electrónico usando SMTP.
        
        Args:
            to_email (str): Dirección de correo del destinatario
            subject (str): Asunto del correo
            body (str): Contenido del correo (puede ser HTML)
            is_html (bool): Indica si el contenido es HTML
        """
        try:
            # Crear mensaje
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.sender_email
            msg['To'] = to_email

            # Agregar contenido
            content_type = 'html' if is_html else 'plain'
            msg.attach(MIMEText(body, content_type))

            # Conectar y enviar
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_pass)
                server.send_message(msg)

            logger.info(f"Correo enviado exitosamente a {to_email}")
            return True

        except Exception as e:
            logger.error(f"Error al enviar correo a {to_email}: {str(e)}")
            raise

    def send_orden_ingreso(self, orden, cliente):
        """Envía correo de confirmación de ingreso de orden."""
        subject = f"Orden de Servicio #{orden.id} - Ingreso"
        body = f"""
        <html>
        <body>
            <h2>Orden de Servicio #{orden.id}</h2>
            <p>Estimado/a {cliente.nombre},</p>
            <p>Su equipo ha sido ingresado exitosamente a nuestro sistema.</p>
            <h3>Detalles del equipo:</h3>
            <ul>
                <li><strong>Equipo:</strong> {orden.equipo}</li>
                <li><strong>Marca:</strong> {orden.marca}</li>
                <li><strong>Modelo:</strong> {orden.modelo}</li>
                <li><strong>Fecha de ingreso:</strong> {orden.fecha_creacion.strftime('%d/%m/%Y %H:%M')}</li>
            </ul>
            <p>Estado actual: <strong>{orden.estado}</strong></p>
            <p>Le mantendremos informado sobre el avance de la reparación.</p>
            <hr>
            <p><small>Este es un correo automático, por favor no responder.</small></p>
        </body>
        </html>
        """
        return self.send_email(cliente.correo, subject, body)

    def send_orden_actualizacion(self, orden, cliente):
        """Envía correo de actualización de estado de orden."""
        subject = f"Actualización Orden #{orden.id} - {orden.estado}"
        body = f"""
        <html>
        <body>
            <h2>Actualización de Orden #{orden.id}</h2>
            <p>Estimado/a {cliente.nombre},</p>
            <p>El estado de su orden ha sido actualizado.</p>
            <h3>Estado actual: <strong>{orden.estado}</strong></h3>
            <h3>Detalles del equipo:</h3>
            <ul>
                <li><strong>Equipo:</strong> {orden.equipo}</li>
                <li><strong>Marca:</strong> {orden.marca}</li>
                <li><strong>Modelo:</strong> {orden.modelo}</li>
                <li><strong>Última actualización:</strong> {orden.fecha_actualizacion.strftime('%d/%m/%Y %H:%M')}</li>
            </ul>
            <hr>
            <p><small>Este es un correo automático, por favor no responder.</small></p>
        </body>
        </html>
        """
        return self.send_email(cliente.correo, subject, body)

    def send_admin_notification(self, orden, tipo_notificacion):
        """Envía notificación a administradores."""
        subject = f"[Admin] {tipo_notificacion} - Orden #{orden.id}"
        body = f"""
        <html>
        <body>
            <h2>{tipo_notificacion}</h2>
            <h3>Orden #{orden.id}</h3>
            <ul>
                <li><strong>Cliente:</strong> {orden.cliente.nombre}</li>
                <li><strong>Equipo:</strong> {orden.equipo}</li>
                <li><strong>Estado:</strong> {orden.estado}</li>
                <li><strong>Fecha:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M')}</li>
            </ul>
            <hr>
            <p><small>Este es un correo automático, por favor no responder.</small></p>
        </body>
        </html>
        """
        # Aquí podrías obtener la lista de administradores de la base de datos
        admin_emails = ['admin@example.com']  # Reemplazar con emails reales
        
        for email in admin_emails:
            self.send_email(email, subject, body) 