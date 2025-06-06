import os
import platform
from datetime import datetime
import subprocess
import socket
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch, mm
import tempfile
from reportlab.graphics.barcode import code128

class ZebraPrinter:
    def __init__(self, config):
        """
        Inicializa la impresora Zebra con la configuración proporcionada
        :param config: Objeto de configuración con los parámetros necesarios
        """
        self.test_mode = config.get('ZEBRA_TEST_MODE', True)
        self.connection_type = config.get('ZEBRA_CONNECTION_TYPE', 'pdf')
        self.printer_name = config.get('ZEBRA_PRINTER_NAME', 'Zebra')
        self.printer_ip = config.get('ZEBRA_PRINTER_IP', 'localhost')
        self.printer_port = config.get('ZEBRA_PRINTER_PORT', 9100)
        self.usb_device = config.get('ZEBRA_USB_DEVICE', '/dev/usb/lp0')
        self.label_dir = config.get('ZEBRA_LABEL_DIR', os.path.join('static', 'labels'))
        self.system = platform.system()
        
        # Crear directorio para etiquetas si no existe
        os.makedirs(self.label_dir, exist_ok=True)

    def generate_zpl(self, orden):
        """
        Genera el código ZPL para la etiqueta
        :param orden: Objeto orden con la información a imprimir
        :return: String con el código ZPL
        """
        # Formatear el ID de la orden con ceros a la izquierda
        orden_id = str(orden.id).zfill(8)
        
        # Código ZPL para la etiqueta
        zpl_code = f"""^XA

^FO50,50^BY3
^BCN,100,Y,N,N
^FD{orden_id}^FS

^FO50,200^CF0,40
^FD{orden.equipo or ''}^FS

^FO50,250^CF0,40
^FD{orden.marca or ''} {orden.modelo or ''}^FS

^FO50,300^CF0,40
^FD{orden.cliente.nombre}^FS

^XZ"""
        return zpl_code.strip()

    def generate_pdf(self, zpl_code, orden_id=None):
        """
        Genera un PDF simulando la etiqueta ZPL
        :param zpl_code: Código ZPL a convertir
        :param orden_id: ID de la orden (opcional)
        :return: Ruta del archivo PDF generado
        """
        # Crear nombre de archivo temporal si no se proporciona orden_id
        if orden_id is None:
            pdf_path = os.path.join(self.label_dir, f'label_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf')
        else:
            pdf_path = os.path.join(self.label_dir, f'label_orden_{orden_id}.pdf')

        # Asegurarse de que el directorio existe
        os.makedirs(os.path.dirname(pdf_path), exist_ok=True)

        # Crear el PDF
        c = canvas.Canvas(pdf_path, pagesize=(100*mm, 50*mm))  # Tamaño típico de etiqueta Zebra
        c.setFont("Helvetica", 10)

        # Extraer información del ZPL
        data = {}
        for line in zpl_code.split('\n'):
            if '^FD' in line and '^FS' in line:
                content = line.split('^FD')[1].split('^FS')[0]
                if '^BCN' in line or '^BC' in line:  # Es un código de barras
                    data['barcode'] = content
                else:
                    data[len(data)] = content

        # Generar el código de barras
        if 'barcode' in data:
            barcode = code128.Code128(data['barcode'], barHeight=20*mm)
            barcode.drawOn(c, 10*mm, 35*mm)
            # Dibujar el número debajo del código de barras
            c.setFont("Helvetica", 8)
            c.drawString(10*mm, 32*mm, data['barcode'])

        # Dibujar el resto del texto
        y_position = 25
        c.setFont("Helvetica", 10)
        for key in sorted(data.keys()):
            if key != 'barcode' and isinstance(key, int):
                c.drawString(10*mm, y_position*mm, data[key])
                y_position -= 5

        c.save()
        return pdf_path

    def print_network(self, zpl_code):
        """Imprime usando conexión de red"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.printer_ip, self.printer_port))
            sock.send(zpl_code.encode())
            sock.close()
            return True
        except Exception as e:
            print(f"Error de impresión en red: {str(e)}")
            return False

    def print_usb(self, zpl_code):
        """Imprime usando conexión USB directa"""
        try:
            if self.system == 'Windows':
                import win32print
                import win32ui
                
                printer_name = win32print.GetDefaultPrinter()
                hprinter = win32print.OpenPrinter(printer_name)
                try:
                    hdc = win32ui.CreateDC()
                    hdc.CreatePrinterDC(printer_name)
                    hdc.StartDoc('Label')
                    hdc.StartPage()
                    hdc.WritePrinter(zpl_code.encode())
                    hdc.EndPage()
                    hdc.EndDoc()
                finally:
                    win32print.ClosePrinter(hprinter)
            else:
                with open(self.usb_device, 'wb') as printer:
                    printer.write(zpl_code.encode())
            return True
        except Exception as e:
            print(f"Error de impresión USB: {str(e)}")
            return False

    def print_cups(self, zpl_code):
        """Imprime usando CUPS"""
        try:
            # Crear archivo temporal con el código ZPL
            with tempfile.NamedTemporaryFile(mode='w', suffix='.zpl', delete=False) as temp:
                temp.write(zpl_code)
                temp_path = temp.name

            # Imprimir usando lp
            result = subprocess.run(['lp', '-d', self.printer_name, temp_path], 
                                 capture_output=True, text=True)
            
            # Eliminar archivo temporal
            os.unlink(temp_path)
            
            if result.returncode != 0:
                print(f"Error CUPS: {result.stderr}")
                return False
            return True
        except Exception as e:
            print(f"Error de impresión CUPS: {str(e)}")
            return False

    def print_label(self, orden):
        """
        Imprime una etiqueta para una orden
        :param orden: Objeto orden con la información a imprimir
        :return: True si la impresión fue exitosa, False en caso contrario
        """
        try:
            # Generar el código ZPL
            zpl_code = self.generate_zpl(orden)
            
            # En modo de prueba, siempre generar PDF
            if self.test_mode:
                pdf_path = self.generate_pdf(zpl_code, orden.id)
                return pdf_path

            # En modo normal, usar el método de conexión configurado
            if self.connection_type == 'network':
                return self.print_network(zpl_code)
            elif self.connection_type == 'usb':
                return self.print_usb(zpl_code)
            elif self.connection_type == 'cups':
                return self.print_cups(zpl_code)
            elif self.connection_type == 'pdf':
                pdf_path = self.generate_pdf(zpl_code, orden.id)
                return pdf_path
            else:
                raise ValueError(f"Tipo de conexión no soportado: {self.connection_type}")
            
        except Exception as e:
            print(f"Error al imprimir: {str(e)}")
            return False

    def print_test(self):
        """
        Imprime una etiqueta de prueba
        :return: True si la impresión fue exitosa, False en caso contrario
        """
        test_zpl = """
^XA
^FO50,50^ADN,36,20^FDTEST PRINT^FS
^FO50,100^BY3^BC^FD12345678^FS
^XZ
"""
        try:
            # En modo de prueba, siempre generar PDF
            if self.test_mode:
                pdf_path = self.generate_pdf(test_zpl)
                return pdf_path

            # En modo normal, usar el método de conexión configurado
            if self.connection_type == 'network':
                return self.print_network(test_zpl)
            elif self.connection_type == 'usb':
                return self.print_usb(test_zpl)
            elif self.connection_type == 'cups':
                return self.print_cups(test_zpl)
            elif self.connection_type == 'pdf':
                pdf_path = self.generate_pdf(test_zpl)
                return pdf_path
            else:
                raise ValueError(f"Tipo de conexión no soportado: {self.connection_type}")
            
        except Exception as e:
            print(f"Error al imprimir prueba: {str(e)}")
            return False 