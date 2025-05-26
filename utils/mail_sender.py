# utils/mail_sender.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from models import CorreoLog, Orden
from extensions import db
import os
import logging
from flask import current_app
from email.utils import formataddr
from socket import gaierror
from smtplib import SMTPException, SMTPAuthenticationError

logger = logging.getLogger(__name__)

class EmailError(Exception):
    """Excepción personalizada para errores de correo."""
    pass

def enviar_correo_smtp(destinatario, asunto, mensaje, retry_count=2):
    """
    Función auxiliar para enviar correos usando SMTP.
    
    Args:
        destinatario (str): Dirección de correo del destinatario
        asunto (str): Asunto del correo
        mensaje (str): Cuerpo del mensaje
        retry_count (int): Número de intentos en caso de error
        
    Returns:
        bool: True si el envío fue exitoso
        
    Raises:
        EmailError: Si hay un error en el envío después de todos los intentos
    """
    for intento in range(retry_count + 1):
        try:
            # Validar configuración
            if not all([
                current_app.config.get('MAIL_SERVER'),
                current_app.config.get('MAIL_PORT'),
                current_app.config.get('MAIL_USERNAME'),
                current_app.config.get('MAIL_PASSWORD'),
                current_app.config.get('MAIL_DEFAULT_SENDER')
            ]):
                raise EmailError("Configuración de correo incompleta")

            # Crear mensaje
            msg = MIMEMultipart()
            msg['From'] = formataddr(('Servicio Técnico', current_app.config['MAIL_DEFAULT_SENDER']))
            msg['To'] = destinatario
            msg['Subject'] = asunto

            # Agregar cuerpo del mensaje
            msg.attach(MIMEText(mensaje, 'plain'))

            # Conectar al servidor SMTP
            with smtplib.SMTP(current_app.config['MAIL_SERVER'], current_app.config['MAIL_PORT'], timeout=30) as server:
                if current_app.config.get('MAIL_USE_TLS', True):
                    server.starttls()
                
                # Autenticar
                server.login(
                    current_app.config['MAIL_USERNAME'],
                    current_app.config['MAIL_PASSWORD']
                )
                
                # Enviar correo
                server.send_message(msg)
                
                logger.info(f"Correo enviado exitosamente a {destinatario}")
                return True

        except SMTPAuthenticationError as e:
            logger.error(f"Error de autenticación SMTP: {str(e)}")
            raise EmailError("Error de autenticación con el servidor SMTP")
            
        except gaierror as e:
            logger.error(f"Error de conexión al servidor SMTP: {str(e)}")
            if intento == retry_count:
                raise EmailError("No se pudo conectar al servidor SMTP")
            
        except SMTPException as e:
            logger.error(f"Error SMTP: {str(e)}")
            if intento == retry_count:
                raise EmailError(f"Error al enviar correo: {str(e)}")
            
        except Exception as e:
            logger.error(f"Error inesperado al enviar correo: {str(e)}")
            if intento == retry_count:
                raise EmailError(f"Error inesperado al enviar correo: {str(e)}")
            
        # Esperar antes de reintentar
        if intento < retry_count:
            import time
            time.sleep(2 ** intento)  # Espera exponencial

def enviar_correo(orden_id, tipo='ingreso'):
    """
    Envía un correo relacionado con una orden.
    
    Args:
        orden_id (int): ID de la orden
        tipo (str): Tipo de correo ('ingreso' o 'actualización')
        
    Returns:
        bool: True si el envío fue exitoso
    """
    orden = Orden.query.get(orden_id)
    if not orden:
        logger.error(f"No se encontró la orden {orden_id}")
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
        },
        'reenvio': {
            'asunto': 'Reenvío: Información de su orden de servicio',
            'mensaje': f"""
                Estimado/a {orden.cliente.nombre},

                Le reenviamos la información de su orden de servicio.

                Detalles:
                - Orden ID: {orden.id}
                - Equipo: {orden.equipo}
                - Estado: {orden.estado}
                - Última actualización: {orden.fecha_actualizacion.strftime('%d-%m-%Y %H:%M') if orden.fecha_actualizacion else 'N/A'}

                Gracias por su preferencia.
            """
        }
    }
    
    template = templates.get(tipo, templates['ingreso'])
    
    try:
        # Enviar correo usando SMTP
        enviar_correo_smtp(
            destinatario=orden.correo,
            asunto=template['asunto'],
            mensaje=template['mensaje']
        )
        
        # Registrar el envío exitoso
        log = CorreoLog(
            orden_id=orden.id,
            destinatario=orden.correo,
            asunto=template['asunto'],
            cuerpo=template['mensaje'],
            fecha_envio=datetime.now(),
            estado='Enviado'
        )
        db.session.add(log)
        db.session.commit()
        
        logger.info(f"Correo de {tipo} enviado exitosamente para la orden {orden_id}")
        return True
        
    except Exception as e:
        # Registrar el error
        log = CorreoLog(
            orden_id=orden.id,
            destinatario=orden.correo,
            asunto=template['asunto'],
            cuerpo=template['mensaje'],
            fecha_envio=datetime.now(),
            estado='Error',
            error=str(e)
        )
        db.session.add(log)
        db.session.commit()
        
        logger.error(f"Error al enviar correo de {tipo} para la orden {orden_id}: {str(e)}")
        return False

def enviar_notificacion_admin(orden_id, tipo, mensaje):
    """
    Envía una notificación al administrador.
    
    Args:
        orden_id (int): ID de la orden
        tipo (str): Tipo de notificación
        mensaje (str): Mensaje adicional
        
    Returns:
        bool: True si el envío fue exitoso
    """
    asunto = f'Notificación de Orden #{orden_id}'
    cuerpo = f"""
        Tipo: {tipo}
        Orden: #{orden_id}
        Mensaje: {mensaje}
        
        Fecha: {datetime.now().strftime('%d-%m-%Y %H:%M')}
    """
    
    try:
        # Validar que existe CORREO_ADMIN
        if not current_app.config.get('CORREO_ADMIN'):
            raise EmailError("No se ha configurado CORREO_ADMIN")
            
        # Enviar correo usando SMTP
        enviar_correo_smtp(
            destinatario=current_app.config['CORREO_ADMIN'],
            asunto=asunto,
            mensaje=cuerpo
        )
        
        # Registrar el envío exitoso
        log = CorreoLog(
            orden_id=orden_id,
            destinatario=current_app.config['CORREO_ADMIN'],
            asunto=asunto,
            cuerpo=cuerpo,
            fecha_envio=datetime.now(),
            estado='Enviado'
        )
        db.session.add(log)
        db.session.commit()
        
        logger.info(f"Notificación admin enviada para la orden {orden_id}")
        return True
        
    except Exception as e:
        # Registrar el error
        log = CorreoLog(
            orden_id=orden_id,
            destinatario=current_app.config.get('CORREO_ADMIN', 'no-configurado'),
            asunto=asunto,
            cuerpo=cuerpo,
            fecha_envio=datetime.now(),
            estado='Error',
            error=str(e)
        )
        db.session.add(log)
        db.session.commit()
        
        logger.error(f"Error al enviar notificación admin para la orden {orden_id}: {str(e)}")
        return False

# Exportar las funciones
__all__ = ['enviar_correo', 'enviar_notificacion_admin']

    