import os
from barcode import Code128
from barcode.writer import ImageWriter
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Image, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import Table, TableStyle
from datetime import datetime

class BarcodeGenerator:
    def __init__(self, upload_folder='static/uploads'):
        self.upload_folder = upload_folder
        self.barcode_folder = os.path.join(upload_folder, 'barcodes')
        self.ensure_folders_exist()

    def ensure_folders_exist(self):
        """Asegura que existan las carpetas necesarias"""
        os.makedirs(self.barcode_folder, exist_ok=True)

    def generate_barcode(self, orden_id):
        """Genera un código de barras para una orden"""
        # Crear el código de barras
        barcode_class = Code128(str(orden_id).zfill(8), writer=ImageWriter())
        
        # Generar nombre de archivo único
        filename = f"barcode_{orden_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        filepath = os.path.join(self.barcode_folder, filename)
        
        # Guardar el código de barras
        barcode_path = barcode_class.save(filepath)
        
        return barcode_path

    def generate_label_pdf(self, orden, output_filename=None):
        """Genera un PDF con la etiqueta para una orden"""
        if output_filename is None:
            output_filename = f"etiqueta_orden_{orden.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
        
        output_path = os.path.join(self.upload_folder, 'labels', output_filename)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Generar el código de barras
        barcode_path = self.generate_barcode(orden.id)

        # Crear el PDF
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )

        # Estilos
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=14,
            spaceAfter=20
        )
        normal_style = styles['Normal']

        # Contenido
        elements = []

        # Título
        elements.append(Paragraph(f"Orden de Servicio #{orden.id}", title_style))
        elements.append(Spacer(1, 12))

        # Información del cliente y equipo
        data = [
            ['Cliente:', orden.cliente.nombre],
            ['Equipo:', orden.equipo],
            ['Marca:', orden.marca or ''],
            ['Modelo:', orden.modelo or ''],
            ['Fecha:', orden.fecha_creacion.strftime('%d/%m/%Y') if orden.fecha_creacion else ''],
        ]

        # Crear tabla con la información
        table = Table(data, colWidths=[100, 300])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.grey),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 12))

        # Agregar código de barras
        barcode_img = Image(barcode_path)
        barcode_img.drawHeight = 30 * mm
        barcode_img.drawWidth = 80 * mm
        elements.append(barcode_img)

        # Generar PDF
        doc.build(elements)

        # Eliminar imagen temporal del código de barras
        os.remove(barcode_path)

        return output_path 