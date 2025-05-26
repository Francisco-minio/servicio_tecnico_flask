import os
from werkzeug.utils import secure_filename
from datetime import datetime
import uuid

class FileHandler:
    _instance = None

    def __init__(self):
        self.app = None
        self.allowed_extensions = None
        self.upload_folder = None

    @classmethod
    def init_app(cls, app):
        if cls._instance is None:
            cls._instance = cls()
        
        cls._instance.app = app
        cls._instance.allowed_extensions = app.config.get('ALLOWED_EXTENSIONS', {'png', 'jpg', 'jpeg', 'gif', 'pdf'})
        cls._instance.upload_folder = app.config.get('UPLOAD_FOLDER', 'static/uploads')
        cls._instance._ensure_upload_folders()
        return cls._instance

    def _ensure_upload_folders(self):
        """Asegura que existan los directorios necesarios para uploads."""
        folders = ['images', 'documents', 'temp', 'pdfs']
        for folder in folders:
            path = os.path.join(self.upload_folder, folder)
            if not os.path.exists(path):
                os.makedirs(path)

    def allowed_file(self, filename):
        """Verifica si la extensión del archivo está permitida."""
        return '.' in filename and \
            filename.rsplit('.', 1)[1].lower() in self.allowed_extensions

    def get_unique_filename(self, filename):
        """Genera un nombre único para el archivo."""
        ext = filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:8]}.{ext}"
        return unique_filename

    def save_file(self, file, category='temp'):
        """Guarda un archivo en la categoría especificada."""
        if not file or not self.allowed_file(file.filename):
            return None

        filename = secure_filename(file.filename)
        unique_filename = self.get_unique_filename(filename)
        save_path = os.path.join(self.upload_folder, category, unique_filename)
        
        try:
            file.save(save_path)
            return os.path.join(category, unique_filename)
        except Exception as e:
            self.app.logger.error(f"Error al guardar archivo: {str(e)}")
            return None

    def delete_file(self, filepath):
        """Elimina un archivo del sistema."""
        try:
            full_path = os.path.join(self.upload_folder, filepath)
            if os.path.exists(full_path):
                os.remove(full_path)
                return True
        except Exception as e:
            self.app.logger.error(f"Error al eliminar archivo: {str(e)}")
        return False

    def clean_temp_files(self, max_age_hours=24):
        """Limpia archivos temporales más antiguos que max_age_hours."""
        temp_dir = os.path.join(self.upload_folder, 'temp')
        now = datetime.now()
        
        try:
            for filename in os.listdir(temp_dir):
                filepath = os.path.join(temp_dir, filename)
                file_modified = datetime.fromtimestamp(os.path.getmtime(filepath))
                if (now - file_modified).total_seconds() > max_age_hours * 3600:
                    os.remove(filepath)
        except Exception as e:
            self.app.logger.error(f"Error al limpiar archivos temporales: {str(e)}")

    def get_file_url(self, filepath):
        """Obtiene la URL para acceder al archivo."""
        if not filepath:
            return None
        return os.path.join('/', self.upload_folder, filepath) 