# Usar una imagen base de Python oficial
FROM python:3.9-slim

# Establecer variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app.py
ENV FLASK_ENV=development

# Crear usuario no root
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Establecer el directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libcairo2 \
    libpq-dev \
    build-essential \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

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
