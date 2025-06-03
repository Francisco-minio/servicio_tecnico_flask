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

## Despliegue en Portainer desde Git

### Prerrequisitos

1. Portainer instalado y configurado
2. Acceso a GitHub Container Registry (ghcr.io)
3. Docker Swarm inicializado en el servidor

### Pasos para el Despliegue

1. **Preparación del Entorno**
   - Crear los siguientes volúmenes en el nodo manager:
     ```bash
     docker volume create mysql_data
     docker volume create mysql_init
     docker volume create app_instance
     docker volume create app_logs
     docker volume create app_session
     docker volume create app_static
     ```

2. **Configuración en Portainer**
   - Ir a "Stacks" > "Add stack"
   - Seleccionar "Git Repository"
   - Configurar el repositorio:
     - Repository URL: https://github.com/Francisco-minio/servicio_tecnico_flask.git
     - Reference: main (o master)
     - Compose path: docker-compose.portainer.yml

3. **Variables de Entorno**
   Configurar las siguientes variables en Portainer:
   ```env
   REGISTRY=ghcr.io
   REPOSITORY=usuario/servicio_tecnico_flask
   TAG=latest
   PORT=5001
   MYSQL_PORT=3306
   FLASK_ENV=production
   WEB_REPLICAS=1
   MYSQL_DATABASE=ordenes_db
   MYSQL_USER=servicio_tecnico
   MYSQL_PASSWORD=servicio_tecnico_password
   MYSQL_ROOT_PASSWORD=root_password
   ```

4. **Inicialización de la Base de Datos**
   - Copiar el archivo init.sql al volumen mysql_init:
     ```bash
     docker cp mysql/init.sql NOMBRE_CONTENEDOR:/docker-entrypoint-initdb.d/
     ```

5. **Verificación**
   - La aplicación web estará disponible en http://tu-servidor:5001
   - La base de datos MySQL estará disponible en el puerto 3306

### Mantenimiento

- Los logs de la aplicación se almacenan en el volumen app_logs
- La base de datos se persiste en el volumen mysql_data
- Las sesiones se almacenan en app_session
- Los archivos estáticos se almacenan en app_static

### Actualización

Para actualizar la aplicación:
1. Hacer push de los cambios al repositorio
2. En Portainer, ir al stack y hacer clic en "Pull and redeploy"

### Solución de Problemas

1. Si la base de datos no se inicializa:
   ```bash
   docker exec -it NOMBRE_CONTENEDOR_DB mysql -u root -p
   ```

2. Para ver los logs de la aplicación:
   ```bash
   docker service logs NOMBRE_SERVICIO_WEB
   ```

3. Para escalar la aplicación web:
   - Modificar WEB_REPLICAS en las variables de entorno
   - Redeployar el stack 