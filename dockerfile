# Usar Alpine Linux como base
FROM python:3.9-alpine

# Establecer variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app.py
ENV FLASK_ENV=development

# Crear usuario no root
RUN addgroup -S appuser && adduser -S appuser -G appuser

# Establecer el directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema necesarias
RUN apk add --no-cache \
    gcc \
    musl-dev \
    python3-dev \
    libffi-dev \
    cairo-dev \
    pango-dev \
    mysql-client \
    mysql-dev \
    build-base

# Copiar requirements.txt
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Crear directorios necesarios
RUN mkdir -p instance logs flask_session static tmp

# Copiar el resto del código
COPY . .

# Establecer permisos
RUN chown -R appuser:appuser /app && \
    chmod -R 755 /app && \
    chmod -R 777 instance logs flask_session static tmp

# Cambiar al usuario no root
USER appuser

# Exponer el puerto
EXPOSE 5000

# Comando para ejecutar la aplicación
CMD ["python", "app.py"]
