# Documentación Técnica - Sistema de Gestión de Servicio Técnico

## Arquitectura del Sistema

### Estructura MVC
El sistema sigue el patrón Modelo-Vista-Controlador:
- **Modelos**: Definidos en `models.py`
- **Vistas**: Templates en `templates/`
- **Controladores**: Blueprints en `blueprints/`

### Componentes Principales

#### 1. Factory Pattern (`factory.py`)
- Inicialización de la aplicación Flask
- Registro de blueprints
- Configuración de extensiones
- Manejo de errores
- Configuración de logging

#### 2. Blueprints
- **orden/**: Gestión de órdenes de servicio
- **cliente/**: Gestión de clientes
- **admin/**: Panel de administración
- **auth/**: Autenticación y autorización

#### 3. Base de Datos
- ORM: SQLAlchemy
- Migraciones: Flask-Migrate
- Modelos principales:
  - Usuario
  - Orden
  - Cliente
  - Técnico
  - HistorialOrden

#### 4. Sistema de Autenticación
- Flask-Login para gestión de sesiones
- Roles de usuario:
  - Administrador
  - Técnico
  - Recepcionista

#### 5. Sistema de Impresión (`utils/zebra_printer.py`)
- Clase ZebraPrinter
- Soporte múltiples conexiones
- Generación de PDFs
- Códigos de barras

## Seguridad

### Protección CSRF
- Implementada con Flask-WTF
- Tokens en todos los formularios
- Validación en métodos POST/PUT/DELETE

### Validación de Datos
- WTForms para validación de formularios
- Sanitización de entradas
- Escape de HTML en templates

### Sesiones
- Sesiones seguras con Flask-Session
- Almacenamiento en filesystem
- Rotación de tokens

## Sistema de Logs

### Configuración
- Rotación diaria de logs
- Niveles de logging configurables
- Separación por componentes:
  - app.log: Logs generales
  - email.log: Logs de correos
  - error.log: Errores críticos

### Eventos Registrados
- Accesos al sistema
- Cambios en órdenes
- Errores de aplicación
- Intentos de acceso fallidos
- Operaciones administrativas

## APIs y Endpoints

### API REST
- Autenticación por token
- Endpoints principales:
  - `/api/ordenes/`
  - `/api/clientes/`
  - `/api/tecnicos/`
  - `/api/estadisticas/`

### Webhooks
- Notificaciones de estado
- Integraciones externas
- Callbacks de pagos

## Gestión de Correos

### Sistema de Notificaciones
- Flask-Mail para envío de correos
- Templates HTML personalizados
- Cola de envío asíncrona
- Retry automático

### Tipos de Notificaciones
- Creación de orden
- Actualización de estado
- Finalización de servicio
- Recordatorios
- Alertas administrativas

## Manejo de Archivos

### Almacenamiento
- Archivos estáticos en `static/`
- Uploads en `static/uploads/`
- PDFs generados en `static/labels/`
- Backups en `backups/`

### Procesamiento
- Redimensionamiento de imágenes
- Generación de PDFs
- Compresión de archivos
- Validación de tipos MIME

## Desarrollo y Testing

### Entorno de Desarrollo
- Flask Debug Toolbar
- Modo debug configurable
- Recarga automática
- Perfilado de SQL

### Testing
- Tests unitarios con pytest
- Tests de integración
- Fixtures de prueba
- Cobertura de código

## Despliegue

### Configuración de Producción
- Gunicorn como servidor WSGI
- Nginx como proxy reverso
- Supervisord para gestión de procesos
- Certificados SSL/TLS

### Monitoreo
- Healthchecks
- Métricas de rendimiento
- Alertas automáticas
- Dashboard de estado

## Mantenimiento

### Tareas Programadas
- Backups diarios
- Limpieza de archivos temporales
- Actualización de estadísticas
- Envío de reportes

### Recuperación
- Procedimientos de backup
- Restauración de datos
- Planes de contingencia
- Logs de auditoría 