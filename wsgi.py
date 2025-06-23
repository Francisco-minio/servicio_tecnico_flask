import os
from factory import create_app

# Configurar el entorno como producción
os.environ['FLASK_ENV'] = 'production'

# Crear la aplicación usando la factory
app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, ssl_context=None)

# Si tu archivo principal se llama distinto, cambia 'app' por el nombre correcto:
# from main import app as application