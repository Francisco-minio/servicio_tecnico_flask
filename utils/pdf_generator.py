import os
from celery_app import celery
from flask import render_template
from weasyprint import HTML

# Configuración de rutas para weasyprint (macOS)
os.environ['PATH'] += os.pathsep + '/opt/homebrew/lib'
os.environ['DYLD_LIBRARY_PATH'] = '/opt/homebrew/lib'

def generar_pdf(orden, historial, output_path):
    """Función sincrónica para generar PDF"""
    try:
        html = render_template("pdf_orden.html", orden=orden, historial=historial)
        HTML(string=html).write_pdf(output_path)
        return True
    except Exception as e:
        print(f"Error generando PDF: {e}")
        return False

@celery.task(bind=True)
def generar_pdf_task(self, orden_data, historial_data, output_path):
    """Tarea Celery para generación asíncrona de PDF"""
    try:
        # Importar aquí para evitar problemas de importación circular
        from models import Orden
        from utils.pdf_generator import generar_pdf
        
        # Reconstruir objetos desde los datos serializados
        orden = Orden.query.get(orden_data['id'])
        historial = historial_data  # Asume que ya está en formato adecuado
        
        result = generar_pdf(orden, historial, output_path)
        if result:
            return {"status": "success", "file_path": output_path}
        else:
            raise Exception("Error al generar PDF")
            
    except Exception as e:
        # Celery puede reintentar si falla
        raise self.retry(exc=e, countdown=60, max_retries=3)