# config.py
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'una_clave_secreta_muy_dificil_de_adivinar'

    # Configuración de la base de datos SQLAlchemy para usar db.db en la carpeta instance
    # Esto asegura que la base de datos se cree y se busque consistentemente en la carpeta 'instance'.
    # La variable de entorno DATABASE_URL se usará en PythonAnywhere, si no, usará la ruta local.
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'db.db') # MODIFICADO: Cambiado de app.db a db.db

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- Configuración para las carpetas de subidas ---
    # Asegúrate de que estas rutas sean absolutas y que el usuario que ejecuta la app tenga permisos de escritura.
    UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'uploads', 'avatars')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # Límite de 16 MB para el tamaño de los archivos

    # Rutas de subida adicionales
    PROJECT_IMAGE_UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'uploads', 'project_images')
    NOTE_IMAGE_UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'uploads', 'note_images')
    
    # MODIFICADO: Cambiado de 'caminata_images' a 'caminatas' para coincidir con tu ubicación manual
    CAMINATA_IMAGE_UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'uploads', 'caminatas')
    
    PAGOS_IMAGE_UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'uploads', 'pagos_images')
    CALENDAR_IMAGE_UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'uploads', 'calendar_images')
    SONGS_UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'uploads', 'songs')
    COVERS_UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'uploads', 'covers')
    ABOUTUS_IMAGE_UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'uploads', 'aboutus_images')
    UPLOAD_FILES_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'uploads', 'files')
