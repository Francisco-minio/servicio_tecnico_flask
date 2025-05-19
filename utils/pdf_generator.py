import os

# Ajusta según arquitectura (Apple Silicon usa /opt/homebrew/lib, Intel usa /usr/local/lib)
os.environ['PATH'] += os.pathsep + '/opt/homebrew/lib'
os.environ['DYLD_LIBRARY_PATH'] = '/opt/homebrew/lib'
from weasyprint import HTML
from flask import render_template

def generar_pdf(orden, historial, output_path):
    html = render_template("pdf_orden.html", orden=orden, historial=historial)
    HTML(string=html).write_pdf(output_path)
