# Sistema de Impresión de Etiquetas

Sistema flexible para impresión de etiquetas con soporte para impresoras Zebra y generación de PDFs.

## Características

✨ **Múltiples Modos de Impresión**
- Impresión directa por red
- Impresión por USB
- Impresión vía CUPS
- Generación de PDFs

🖨️ **Compatibilidad**
- Windows
- macOS
- Linux

🔧 **Configuración Flexible**
- Modo de prueba para desarrollo
- Configuración vía variables de entorno
- Fácil cambio entre modos

## Inicio Rápido

1. **Modo de Prueba (por defecto)**
   ```bash
   # No requiere configuración
   # Genera PDFs en static/labels/
   ```

2. **Impresión por Red**
   ```bash
   export ZEBRA_TEST_MODE=false
   export ZEBRA_CONNECTION_TYPE=network
   export ZEBRA_PRINTER_IP=192.168.1.100
   export ZEBRA_PRINTER_PORT=9100
   ```

3. **Impresión por USB**
   ```bash
   export ZEBRA_TEST_MODE=false
   export ZEBRA_CONNECTION_TYPE=usb
   export ZEBRA_USB_DEVICE=/dev/usb/lp0  # Linux
   # o
   export ZEBRA_USB_DEVICE=USB001  # Windows
   ```

4. **Impresión por CUPS**
   ```bash
   export ZEBRA_TEST_MODE=false
   export ZEBRA_CONNECTION_TYPE=cups
   export ZEBRA_PRINTER_NAME=Zebra
   ```

## Uso

1. **Imprimir Etiqueta de Orden**
   - Ir a la vista de detalle de orden
   - Clic en "Imprimir Etiqueta"

2. **Imprimir Etiqueta de Prueba**
   - Disponible solo para administradores
   - Ir a la página principal
   - Clic en "Imprimir Test"

3. **Generar PDF**
   - Disponible en cualquier modo
   - Se guarda en `static/labels/`

## Documentación

Para documentación detallada, ver:
- [Sistema de Impresión](docs/sistema_impresion.md)

## Solución de Problemas

Si encuentras problemas:
1. Verifica la configuración
2. Usa el modo de prueba
3. Revisa los logs
4. Consulta la documentación detallada 