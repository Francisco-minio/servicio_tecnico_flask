from celery import Celery

celery = Celery('servicio_tecnico',
                broker='redis://localhost:6379/0',
                backend='redis://localhost:6379/0',
                include=['utils.pdf_generator', 'utils.mail_sender'])

# Configuración opcional
celery.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='America/Santiago',
    enable_utc=True,
) 