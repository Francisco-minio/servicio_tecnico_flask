from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app, send_file
from flask_login import login_required, current_user
from models import db, Orden, Cliente, Usuario, Historial, Imagen, SolicitudCotizacion
from datetime import datetime
from utils.zebra_printer import ZebraPrinter
from utils.barcode_generator import BarcodeGenerator
import os

bp = Blueprint('ordenes', __name__)

# ... (código existente) ...

@bp.route('/orden/<int:orden_id>/imprimir_etiqueta')
@login_required
def imprimir_etiqueta(orden_id):
    """Imprime una etiqueta para una orden usando una impresora Zebra"""
    orden = Orden.query.get_or_404(orden_id)
    
    # Crear instancia de la impresora con la configuración actual
    printer = ZebraPrinter(current_app.config)
    
    # Intentar imprimir la etiqueta
    result = printer.print_label(orden)
    
    # Si estamos en modo de prueba o PDF, el resultado es la ruta del archivo
    if isinstance(result, str) and result.endswith('.pdf'):
        # Registrar en el historial
        historial = Historial(
            orden_id=orden.id,
            usuario_id=current_user.id,
            descripcion=f"Se generó un PDF con la etiqueta para la orden #{orden.id}",
            fecha=datetime.now()
        )
        db.session.add(historial)
        db.session.commit()
        
        # Devolver el archivo PDF
        return send_file(
            result,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'etiqueta_orden_{orden.id}.pdf'
        )
    
    # Si no es PDF, verificar si la impresión fue exitosa
    if result:
        flash('Etiqueta enviada a la impresora correctamente.', 'success')
        
        # Registrar en el historial
        historial = Historial(
            orden_id=orden.id,
            usuario_id=current_user.id,
            descripcion=f"Se imprimió una etiqueta para la orden #{orden.id}",
            fecha=datetime.now()
        )
        db.session.add(historial)
        db.session.commit()
    else:
        flash('Error al enviar la etiqueta a la impresora. Verifique la conexión.', 'error')
    
    return redirect(url_for('ordenes.ver_orden', orden_id=orden_id))

@bp.route('/orden/<int:orden_id>/generar_etiqueta_pdf')
@login_required
def generar_etiqueta_pdf(orden_id):
    """Genera un PDF con la etiqueta para una orden"""
    orden = Orden.query.get_or_404(orden_id)
    
    # Crear instancia del generador de códigos de barra
    generator = BarcodeGenerator()
    
    try:
        # Generar el PDF
        pdf_path = generator.generate_label_pdf(orden)
        
        # Registrar en el historial
        historial = Historial(
            orden_id=orden.id,
            usuario_id=current_user.id,
            descripcion=f"Se generó un PDF con la etiqueta para la orden #{orden.id}",
            fecha=datetime.now()
        )
        db.session.add(historial)
        db.session.commit()
        
        # Devolver el archivo PDF
        return send_file(
            pdf_path,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'etiqueta_orden_{orden.id}.pdf'
        )
    except Exception as e:
        flash(f'Error al generar la etiqueta: {str(e)}', 'error')
        return redirect(url_for('ordenes.ver_orden', orden_id=orden_id))

@bp.route('/imprimir_test')
@login_required
def imprimir_test():
    """Imprime una etiqueta de prueba"""
    if not current_user.rol == 'admin':
        flash('No tiene permisos para realizar esta acción.', 'error')
        return redirect(url_for('main.index'))
    
    # Crear instancia de la impresora con la configuración actual
    printer = ZebraPrinter(current_app.config)
    
    # Intentar imprimir la etiqueta de prueba
    result = printer.print_test()
    
    # Si estamos en modo de prueba o PDF, el resultado es la ruta del archivo
    if isinstance(result, str) and result.endswith('.pdf'):
        return send_file(
            result,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='etiqueta_test.pdf'
        )
    
    # Si no es PDF, verificar si la impresión fue exitosa
    if result:
        flash('Etiqueta de prueba enviada correctamente.', 'success')
    else:
        flash('Error al enviar la etiqueta de prueba.', 'error')
    
    return redirect(url_for('main.index')) 