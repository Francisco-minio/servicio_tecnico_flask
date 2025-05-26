# Sistema de Gestión de Servicio Técnico

## Descripción
Sistema web para la gestión de órdenes de servicio técnico, desarrollado con Flask.

## Características
- Gestión de órdenes de servicio
- Seguimiento de estado de reparaciones
- Sistema de notificaciones por correo
- Gestión de clientes y técnicos
- Generación de reportes PDF
- Panel de administración
- Sistema de logs

## Requisitos
- Python 3.8+
- MySQL/MariaDB
- Servidor SMTP (SMTP2GO recomendado)

## Instalación

1. Clonar el repositorio:
```bash
git clone <repositorio>
cd servicio_tecnico_flask
```

2. Crear y activar entorno virtual:
```bash
python -m venv env
source env/bin/activate  # Linux/Mac
env\Scripts\activate     # Windows
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

4. Configurar variables de entorno:
Crear archivo `.env` con:
```
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=tu_clave_secreta

# Base de datos
DATABASE_URL=mysql+pymysql://usuario:contraseña@localhost/ordenes_db

# Configuración SMTP
MAIL_SERVER=smtp.smtp2go.com
MAIL_PORT=2525
MAIL_USE_TLS=True
MAIL_USERNAME=tu_usuario
MAIL_PASSWORD=tu_contraseña
MAIL_DEFAULT_SENDER=no-reply@tudominio.com
CORREO_ADMIN=admin@tudominio.com
```

5. Inicializar la base de datos:
```bash
flask db upgrade
python init_setup.py
```

## Ejecución
```bash
# Iniciar servidor de desarrollo
flask run
```

## Estructura de Directorios
```
servicio_tecnico_flask/
├── blueprints/           # Módulos de la aplicación
├── static/              # Archivos estáticos
├── templates/           # Plantillas HTML
├── utils/              # Utilidades
├── migrations/         # Migraciones de base de datos
├── logs/              # Archivos de registro
│   ├── app.log        # Logs de la aplicación
│   └── email.log      # Logs de correos
└── tests/             # Pruebas unitarias
```

## Seguridad
- Autenticación de usuarios
- Protección CSRF
- Sesiones seguras
- Sanitización de entradas
- Logs de actividad
- Backups automáticos

## Mantenimiento
- Los logs se rotan automáticamente
- Backups diarios de la base de datos
- Monitoreo de errores y actividad

## Contribuir
1. Fork el repositorio
2. Crear rama para feature (`git checkout -b feature/nombre`)
3. Commit cambios (`git commit -am 'Añadir característica'`)
4. Push a la rama (`git push origin feature/nombre`)
5. Crear Pull Request

## Licencia
Este proyecto está bajo la Licencia MIT. 