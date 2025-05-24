from celery_app import celery
import os

@celery.task
def generar_pdf_task(orden_id):
    """Genera un PDF para una orden específica."""
    # Implementación temporal
    pdf_dir = 'static/pdfs'
    if not os.path.exists(pdf_dir):
        os.makedirs(pdf_dir)
    
    pdf_path = os.path.join(pdf_dir, f'orden_{orden_id}.pdf')
    # Por ahora solo retornamos la ruta
    return pdf_path