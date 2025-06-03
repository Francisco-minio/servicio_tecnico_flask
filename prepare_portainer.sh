#!/bin/bash

# Asegúrate de reemplazar esto con tu registro de Docker
DOCKER_REGISTRY="tu.registro.docker.com"

# Construir la imagen
docker build -t servicio_tecnico_flask:latest .

# Etiquetar la imagen para el registro
docker tag servicio_tecnico_flask:latest $DOCKER_REGISTRY/servicio_tecnico_flask:latest

# Subir la imagen al registro
docker push $DOCKER_REGISTRY/servicio_tecnico_flask:latest

# Crear directorio para archivos de inicialización
mkdir -p portainer_deploy
cp docker-compose.portainer.yml portainer_deploy/docker-compose.yml
cp mysql/init.sql portainer_deploy/

# Crear archivo .env para Portainer
echo "DOCKER_REGISTRY=$DOCKER_REGISTRY" > portainer_deploy/.env

# Crear archivo README con instrucciones
cat > portainer_deploy/README.md << EOL
# Instrucciones de Despliegue en Portainer

1. Asegúrate de que Portainer esté configurado con acceso a tu registro de Docker ($DOCKER_REGISTRY)
2. Crea los siguientes volúmenes en el nodo manager:
   - mysql_data
   - mysql_init
   - app_instance
   - app_logs
   - app_session
   - app_static

3. Copia el archivo init.sql al volumen mysql_init:
   \`\`\`bash
   docker cp init.sql NOMBRE_CONTENEDOR:/docker-entrypoint-initdb.d/
   \`\`\`

4. En Portainer:
   - Ve a Stacks > Add Stack
   - Sube el archivo docker-compose.yml
   - Configura las variables de entorno según sea necesario
   - Deploy el stack

5. Verifica que los servicios estén funcionando:
   - La aplicación web estará disponible en el puerto 5001
   - La base de datos MySQL estará disponible en el puerto 3306

Notas:
- Asegúrate de que los puertos 5001 y 3306 no estén en uso
- Los logs estarán disponibles en el volumen app_logs
- La base de datos se persistirá en el volumen mysql_data
EOL

# Crear archivo zip para fácil distribución
cd portainer_deploy
zip -r ../portainer_deploy.zip ./*
cd ..

echo "Preparación completada. Los archivos están en el directorio 'portainer_deploy' y comprimidos en 'portainer_deploy.zip'" 