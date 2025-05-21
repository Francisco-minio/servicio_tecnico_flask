# utils/pdf_generator.py
import os
from weasyprint import HTML
from flask import render_template # Keep for now, will be used within app context

from celery_app import celery
# Models and db will be imported within the task, assuming app context is handled by Celery app setup

# Keep these if still needed by weasyprint runtime, though often better handled in Dockerfile or system setup
# os.environ['PATH'] += os.pathsep + '/opt/homebrew/lib'
# os.environ['DYLD_LIBRARY_PATH'] = '/opt/homebrew/lib'

@celery.task(bind=True) # bind=True gives access to self (the task instance)
def generar_pdf_task(self, orden_id, output_path):
    # self.app.flask_app should be available if Celery app is configured with it.
    # This flask_app instance provides the necessary context.
    flask_app = self.app.flask_app
    if not flask_app:
        # Fallback or error if flask_app is not configured in celery_app
        # This indicates a setup issue with Celery and Flask integration.
        raise RuntimeError("Flask app context not found in Celery task. Ensure celery_app.py configures flask_app.")

    with flask_app.app_context():
        from models import Orden, Historial # Import models here, within app context
        # db is typically available via flask_app.extensions['sqlalchemy'].db or similar
        # or if extensions.py.db is initialized with an app.
        # For simplicity, assuming models can be queried directly if db was init'd with app.

        orden = Orden.query.get(orden_id)
        if not orden:
            # Log error or handle as appropriate for your application
            print(f"Order with ID {orden_id} not found.") # Or use actual logging
            # You might want to raise an error that Celery can catch
            raise ValueError(f"Order with ID {orden_id} not found for PDF generation.")

        historial = Historial.query.filter_by(orden_id=orden_id).order_by(Historial.fecha.desc()).all()
        
        # Ensure the directory for output_path exists
        pdf_dir = os.path.dirname(output_path)
        if not os.path.exists(pdf_dir):
            try:
                os.makedirs(pdf_dir)
            except OSError as e: # Guard against race condition
                if not os.path.isdir(pdf_dir):
                    raise # Reraise if it's not a "directory already exists" error

        html_string = render_template("pdf_orden.html", orden=orden, historial=historial)
        HTML(string=html_string).write_pdf(output_path)
        return f"PDF for order {orden_id} generated at {output_path}"
