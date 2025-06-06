# Sistema de Impresión de Etiquetas

Este documento describe el sistema de impresión de etiquetas implementado en la aplicación de gestión de órdenes de servicio técnico.

## Características Principales

- Soporte para múltiples métodos de impresión:
  - Impresión directa a impresora Zebra por red
  - Impresión por USB
  - Impresión a través de CUPS (Common Unix Printing System)
  - Generación de PDFs
- Modo de prueba para desarrollo y testing
- Compatible con Windows, macOS y Linux
- Generación de códigos de barras Code128
- Registro de historial de impresiones

## Configuración

El sistema se configura a través de variables de entorno:

### Modo de Prueba

```bash
# Activar/desactivar modo de prueba (por defecto: True)
export ZEBRA_TEST_MODE=true    # Para generar solo PDFs
export ZEBRA_TEST_MODE=false   # Para impresión real
```

### Tipo de Conexión

```bash
# Configurar el tipo de conexión
export ZEBRA_CONNECTION_TYPE=network  # Conexión por red
export ZEBRA_CONNECTION_TYPE=usb      # Conexión USB directa
export ZEBRA_CONNECTION_TYPE=cups     # Usar sistema CUPS
export ZEBRA_CONNECTION_TYPE=pdf      # Siempre generar PDFs
```

### Configuración por Tipo de Conexión

#### Conexión de Red

```bash
export ZEBRA_PRINTER_IP=192.168.1.100   # IP de la impresora
export ZEBRA_PRINTER_PORT=9100          # Puerto (por defecto: 9100)
```

#### Conexión USB

```bash
# Linux
export ZEBRA_USB_DEVICE=/dev/usb/lp0

# Windows
export ZEBRA_USB_DEVICE=USB001

# macOS
export ZEBRA_USB_DEVICE=/dev/usb/lpX  # X es el número de dispositivo
```

#### Conexión CUPS

```bash
export ZEBRA_PRINTER_NAME=Zebra  # Nombre de la impresora en CUPS
```

## Estructura del Sistema

### Componentes Principales

1. **Clase ZebraPrinter** (`utils/zebra_printer.py`)
   - Maneja toda la lógica de impresión
   - Genera código ZPL para las etiquetas
   - Convierte ZPL a PDF cuando es necesario
   - Implementa diferentes métodos de impresión

2. **Configuración** (`config.py`)
   - Define todas las variables de configuración
   - Maneja valores por defecto
   - Carga configuración desde variables de entorno

3. **Rutas de Impresión** (`routes/ordenes.py`)
   - `/orden/<orden_id>/imprimir_etiqueta`: Imprime etiqueta para una orden
   - `/orden/<orden_id>/generar_etiqueta_pdf`: Genera PDF de la etiqueta
   - `/imprimir_test`: Imprime etiqueta de prueba (solo admin)

### Formato de Etiquetas

Las etiquetas incluyen:
- Nombre del cliente
- Detalles del equipo (tipo, marca, modelo)
- Fecha de creación
- Número de orden
- Código de barras Code128

## Uso del Sistema

### En Desarrollo

Por defecto, el sistema opera en modo de prueba, generando PDFs en lugar de imprimir:

1. Los PDFs se guardan en `static/labels/`
2. Se generan automáticamente al llamar a las funciones de impresión
3. Ideal para desarrollo y pruebas sin necesidad de hardware

### En Producción

Para usar el sistema con impresoras reales:

1. Configurar las variables de entorno según el tipo de conexión
2. Desactivar el modo de prueba (`ZEBRA_TEST_MODE=false`)
3. Verificar la conexión con la impresora usando la función de prueba

### Manejo de Errores

El sistema incluye:
- Registro detallado de errores
- Mensajes de error específicos por tipo de conexión
- Fallback a PDF en caso de errores de impresión

## Mantenimiento

### Archivos Temporales

- Los PDFs se guardan en `static/labels/`
- Se recomienda implementar una tarea periódica para limpiar archivos antiguos

### Registro de Impresiones

Cada impresión se registra en el historial de la orden con:
- Fecha y hora
- Usuario que realizó la impresión
- Tipo de impresión (directa o PDF)

## Solución de Problemas

### Problemas Comunes

1. **Error de Conexión de Red**
   - Verificar IP y puerto
   - Comprobar firewall
   - Verificar que la impresora esté encendida y en red

2. **Error de USB**
   - Verificar permisos del dispositivo
   - Comprobar que el dispositivo esté reconocido
   - Verificar la ruta del dispositivo

3. **Error de CUPS**
   - Verificar que CUPS esté funcionando
   - Comprobar nombre de impresora
   - Verificar permisos de CUPS

### Diagnóstico

Para diagnosticar problemas:
1. Revisar los logs de la aplicación
2. Usar la función de impresión de prueba
3. Verificar la configuración actual
4. Comprobar permisos y conectividad

## Mejores Prácticas

1. **Desarrollo**
   - Usar modo de prueba
   - Mantener PDFs de prueba organizados
   - Documentar cambios en el formato de etiquetas

2. **Producción**
   - Implementar monitoreo de impresión
   - Mantener registro de errores
   - Realizar copias de seguridad de configuración

3. **Mantenimiento**
   - Limpiar archivos temporales regularmente
   - Actualizar firmware de impresoras
   - Mantener documentación actualizada 