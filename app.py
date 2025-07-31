from flask import Flask, render_template, request, redirect, url_for, flash, session, current_app
from config import Config
import os
from werkzeug.utils import secure_filename # Para nombres de archivo seguros
from datetime import datetime, date # Importar date para manejar fechas
import re # Para validación de email
import json # NUEVA: Importa json para los filtros de Jinja2
from functools import wraps # Importar wraps para decoradores

# MODIFICADO: Importa db, bcrypt, migrate y User desde models.py
# ES CRUCIAL QUE EL MODELO USER Y LAS INSTANCIAS DE DB, BCRYPT Y MIGRATE
# SE IMPORTEN ÚNICAMENTE DESDE models.py PARA EVITAR IMPORTACIONES CIRCULARES.
from models import db, bcrypt, migrate, User, Project, Note, InternationalTravel, Caminata, AbonoCaminata, caminata_participantes, Pagos, CalendarEvent, Instruction, Song, Playlist, Itinerario, AboutUs
from contactos import contactos_bp
from perfil import perfil_bp # Importa el Blueprint de perfil
from proyecto import proyecto_bp # Importa el Blueprint de proyectos
from notas import notas_bp # NUEVA: Importa el Blueprint de notas
from intern import intern_bp # NUEVA: Importa el Blueprint de intern
from caminatas import caminatas_bp # NUEVA: Importa el Blueprint de caminatas
from pagos import pagos_bp # NUEVA: Importa el Blueprint de pagos
from calendario import calendario_bp # NUEVA: Importa el Blueprint de Calendario
from instrucciones import instrucciones_bp # NUEVA: Importa el Blueprint de Instrucciones
from player import player_bp # Importa el Blueprint del reproductor
from itinerario import itinerario_bp # NUEVA: Importa el Blueprint del itinerario
from aboutus import aboutus_bp # NUEVA: Importa el Blueprint de AboutUs
from rutas import rutas_bp # NUEVA: Importa el Blueprint de Rutas
from version import version_bp, Version # NUEVA: Importa el Blueprint de Version
from files import files_bp # NUEVA: Importa el Blueprint de Files
from btns import btns_bp # Importa el Blueprint desde btns.py


from sqlalchemy.exc import IntegrityError # NUEVO: Importar IntegrityError

app = Flask(__name__)
app.config.from_object(Config)

# REGISTRA EL BLUEPRINT DE BTNS.PY AQUÍ, ANTES DE DEFINIR CUALQUIER RUTA
# QUE PUEDA USAR SUS ENDPOINTS EN LAS PLANTILLAS.
app.register_blueprint(btns_bp)

# Configuración para subida de archivos
# NOTA IMPORTANTE: Estas rutas se definen aquí y luego se adjuntan a app.config
# para que sean accesibles desde los Blueprints a través de current_app.config
# Asegúrate de que los nombres de las carpetas coincidan con lo que esperas.
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads', 'avatars')
PROJECT_IMAGE_UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads', 'project_images')
NOTE_IMAGE_UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads', 'note_images') # Nueva carpeta para imágenes de notas

# MODIFICADO: Esta línea ahora apunta a la carpeta 'caminatas'
CAMINATA_IMAGE_UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads', 'caminatas')

PAGOS_IMAGE_UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads', 'pagos_images') # NUEVA: Carpeta para imágenes de pagos
CALENDAR_IMAGE_UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads', 'calendar_images') # NUEVA: Carpeta para imágenes de calendario
SONGS_UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads', 'songs') # NUEVA: Carpeta para archivos de música
COVERS_UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads', 'covers') # NUEVA: Carpeta para carátulas de álbumes
ABOUTUS_IMAGE_UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads', 'aboutus_images') # NUEVA: Carpeta para imágenes de AboutUs
UPLOAD_FILES_FOLDER = os.path.join(app.root_path, 'static', 'uploads', 'files') # NUEVA: Carpeta para archivos generales


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
ALLOWED_MUSIC_EXTENSIONS = {'mp3', 'wav', 'ogg'} # NUEVA: Extensiones de música permitidas

# Adjuntar las rutas de las carpetas a la configuración de la aplicación
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROJECT_IMAGE_UPLOAD_FOLDER'] = PROJECT_IMAGE_UPLOAD_FOLDER
app.config['NOTE_IMAGE_UPLOAD_FOLDER'] = NOTE_IMAGE_UPLOAD_FOLDER # Guarda la ruta en config
app.config['CAMINATA_IMAGE_UPLOAD_FOLDER'] = CAMINATA_IMAGE_UPLOAD_FOLDER # NUEVA: Adjuntar la ruta de imágenes de caminatas
app.config['PAGOS_IMAGE_UPLOAD_FOLDER'] = PAGOS_IMAGE_UPLOAD_FOLDER # NUEVA: Adjuntar la ruta de imágenes de pagos
app.config['CALENDAR_IMAGE_UPLOAD_FOLDER'] = CALENDAR_IMAGE_UPLOAD_FOLDER # NUEVA: Adjuntar la ruta de imágenes de calendario
app.config['SONGS_UPLOAD_FOLDER'] = SONGS_UPLOAD_FOLDER # NUEVA: Adjuntar la ruta de canciones
app.config['COVERS_UPLOAD_FOLDER'] = COVERS_UPLOAD_FOLDER # NUEVA: Adjuntar la ruta de carátulas
app.config['ABOUTUS_IMAGE_UPLOAD_FOLDER'] = ABOUTUS_IMAGE_UPLOAD_FOLDER # NUEVA: Adjuntar la ruta de imágenes de AboutUs
app.config['UPLOAD_FILES_FOLDER'] = UPLOAD_FILES_FOLDER # NUEVA: Adjuntar la ruta de archivos generales


# Asegúrate de que las carpetas de subidas existan
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROJECT_IMAGE_UPLOAD_FOLDER, exist_ok=True)
os.makedirs(NOTE_IMAGE_UPLOAD_FOLDER, exist_ok=True) # Asegura que la carpeta para imágenes de notas exista

# MODIFICADO: Asegura que la carpeta 'caminatas' exista
os.makedirs(CAMINATA_IMAGE_UPLOAD_FOLDER, exist_ok=True)

os.makedirs(PAGOS_IMAGE_UPLOAD_FOLDER, exist_ok=True) # NUEVA: Asegura que la carpeta para imágenes de pagos exista
os.makedirs(CALENDAR_IMAGE_UPLOAD_FOLDER, exist_ok=True) # NUEVA: Asegura que la carpeta para imágenes de calendario exista
os.makedirs(SONGS_UPLOAD_FOLDER, exist_ok=True) # NUEVA: Asegura que la carpeta para canciones exista
os.makedirs(COVERS_UPLOAD_FOLDER, exist_ok=True) # NUEVA: Asegura que la carpeta para carátulas exista
os.makedirs(ABOUTUS_IMAGE_UPLOAD_FOLDER, exist_ok=True) # NUEVA: Asegura que la carpeta para imágenes de AboutUs exista
os.makedirs(UPLOAD_FILES_FOLDER, exist_ok=True) # NUEVA: Asegura que la carpeta para archivos generales exista


# Inicializa db, bcrypt y migrate con la instancia de la aplicación
# Ahora db, bcrypt, migrate son objetos importados de models.py
db.init_app(app)
bcrypt.init_app(app)
migrate.init_app(app, db)

# Función para verificar extensiones de archivo permitidas
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# NUEVA: Función para verificar extensiones de música permitidas
def allowed_music_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_MUSIC_EXTENSIONS


# Adjuntando allowed_file y UPLOAD_FOLDER al objeto 'app'
# Esto permite que los Blueprints accedan a ellos a través de current_app
app.allowed_file = allowed_file
app.allowed_music_file = allowed_music_file # NUEVA: Adjuntar la función para archivos de música
app.UPLOAD_FOLDER = UPLOAD_FOLDER

# MODIFICADO: Adjuntar la ruta de imágenes de caminatas
app.CAMINATA_IMAGE_UPLOAD_FOLDER = CAMINATA_IMAGE_UPLOAD_FOLDER

app.PAGOS_IMAGE_UPLOAD_FOLDER = PAGOS_IMAGE_UPLOAD_FOLDER # NUEVA: Adjuntar la ruta de imágenes de pagos
app.CALENDAR_IMAGE_UPLOAD_FOLDER = CALENDAR_IMAGE_UPLOAD_FOLDER # NUEVA: Adjuntar la ruta de imágenes de calendario
app.SONGS_UPLOAD_FOLDER = SONGS_UPLOAD_FOLDER # NUEVA: Adjuntar la ruta de canciones
app.COVERS_UPLOAD_FOLDER = COVERS_UPLOAD_FOLDER # NUEVA: Adjuntar la ruta de carátulas
app.ABOUTUS_IMAGE_UPLOAD_FOLDER = ABOUTUS_IMAGE_UPLOAD_FOLDER # NUEVA: Adjuntar la ruta de imágenes de AboutUs
app.UPLOAD_FILES_FOLDER = UPLOAD_FILES_FOLDER # NUEVA: Adjuntar la ruta de archivos generales


# NUEVOS FILTROS DE JINJA2: Para formatear moneda y parsear JSON en las plantillas
def format_currency(value):
    if value is None:
        return "N/A"
    try:
        return f"${value:,.2f}"
    except (ValueError, TypeError):
        return str(value)

app.jinja_env.filters['format_currency'] = format_currency

def from_json(value):
    if value:
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return [] # Retorna lista vacía si el JSON es inválido
    return []

app.jinja_env.filters['from_json'] = from_json

# Filtro personalizado para Jinja2 para convertir a datetime
@app.template_filter('to_datetime')
def to_datetime_filter(value):
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            # Intenta parsear diferentes formatos si es necesario
            return datetime.strptime(value, '%Y-%m-%d %H:%M:%S.%f') # Formato común de SQLAlchemy
        except ValueError:
            try:
                return datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                try:
                    return datetime.strptime(value, '%Y-%m-%d')
                except ValueError:
                    # Si no se puede parsear, devuelve None o el valor original
                    return None
    return value


# DECORADORES PARA ROLES
def role_required(roles):
    """
    Decorador para restringir el acceso a rutas basadas en roles.
    `roles` puede ser una cadena (un solo rol) o una lista de cadenas (múltiples roles).
    """
    if not isinstance(roles, list):
        roles = [roles]

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'logged_in' not in session or not session['logged_in']:
                flash('Por favor, inicia sesión para acceder a esta página.', 'info')
                return redirect(url_for('login'))
            
            user_role = session.get('role')
            if user_role not in roles:
                flash('No tienes permiso para acceder a esta página.', 'danger')
                return redirect(url_for('home')) # O a una página de "Acceso Denegado"
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# NUEVO: Procesador de contexto para inyectar la última versión en todas las plantillas
@app.context_processor
def inject_latest_version():
    try:
        latest_version = Version.query.order_by(Version.fecha_creacion.desc()).first()
        if latest_version:
            return {'latest_version_number': latest_version.numero_version}
    except Exception as e:
        # Esto es importante para manejar el caso donde la tabla Version aún no existe
        # durante el primer inicio o antes de las migraciones.
        print(f"DEBUG: Error al obtener la última versión: {e}")
    return {'latest_version_number': 'N/A'} # Valor por defecto si no hay versiones o hay un error



# LÓGICA PARA EL PRIMER SUPERUSUARIO: Se ejecuta antes de cada solicitud
@app.before_request
def check_for_first_user():
    """
    Verifica si no hay usuarios en la base de datos.
    Si no hay, la siguiente ruta de registro permitirá crear un Superuser.
    Esta bandera solo se establece una vez por instancia de la aplicación en memoria.
    """
    # Solo ejecutar si la bandera aún no se ha establecido.
    # Esto evita consultas a la DB en cada request después de la inicialización.
    if 'first_user_registration_allowed' not in current_app.config:
        with app.app_context():
            total_users = db.session.query(User).count()
            if total_users == 0:
                current_app.config['first_user_registration_allowed'] = True
                print("DEBUG: No se encontraron usuarios. El próximo registro será un Superuser.")
            else:
                current_app.config['first_user_registration_allowed'] = False
                print("DEBUG: Ya existen usuarios. Los registros serán Usuarios Regulares.")


# Rutas de la aplicación (mantenidas igual)
@app.route('/')
def index():
    # Obtener todas las caminatas (similar a como lo hace ver_caminatas en caminatas.py)
    all_caminatas = Caminata.query.order_by(Caminata.fecha.desc()).all()
    search_actividad = request.args.get('actividad')

    if search_actividad:
        caminatas = Caminata.query.filter_by(actividad=search_actividad).all()
    else:
        caminatas = Caminata.query.all()
        
    return render_template('ver_caminatas.html', caminatas=caminatas, search_actividad=search_actividad)


@app.route('/register', methods=['GET', 'POST'])
def register():
    actividad_opciones = ["No Aplica", "La Tribu", "Senderista", "Enfermería", "Cocina", "Confección y Diseño", "Restaurante", "Transporte Terrestre", "Transporte Acuatico", "Transporte Aereo", "Migración", "Parque Nacional", "Refugio Silvestre", "Centro de Atracción", "Lugar para Caminata", "Acarreo", "Oficina de trámite", "Primeros Auxilios", "Farmacia", "Taller", "Abogado", "Mensajero", "Tienda", "Polizas", "Aerolínea", "Guía", "Banco", "Otros"]
    capacidad_opciones = ["Seleccionar Capacidad", "Rápido", "Intermedio", "Básico", "Iniciante"]
    participacion_opciones = ["No Aplica", "Solo de La Tribu", "Constante", "Inconstante", "El Camino de Costa Rica", "Parques Nacionales", "Paseo | Recreativo", "Revisar/Eliminar"]

    # Opciones para Tipo de Sangre
    tipo_sangre_opciones = ["Seleccionar Tipo", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
    # NUEVA: Opciones para Provincia
    provincia_opciones = ["San José", "Alajuela", "Cartago", "Heredia", "Guanacaste", "Puntarenas", "Limón"]

    if request.method == 'POST':
        username = request.form['username_registro']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        nombre = request.form['nombre']
        primer_apellido = request.form['primer_apellido']
        telefono = request.form['telefono']

        segundo_apellido = request.form.get('segundo_apellido')
        telefono_emergencia = request.form.get('telefono_emergencia')
        nombre_emergencia = request.form.get('nombre_emergencia')
        empresa = request.form.get('empresa')
        cedula = request.form.get('cedula')
        direccion = request.form.get('direccion')
        email = request.form.get('email') # Obtener el email del formulario
        actividad = request.form.get('actividad')
        capacidad = request.form.get('capacidad')
        participacion = request.form.get('participacion')

        # NUEVOS CAMPOS: Obtener datos del formulario
        fecha_cumpleanos_str = request.form.get('fecha_cumpleanos')
        fecha_cumpleanos = None
        if fecha_cumpleanos_str:
            try:
                fecha_cumpleanos = datetime.strptime(fecha_cumpleanos_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Formato de fecha de cumpleaños inválido.', 'danger')
                return render_template('register.html', actividad_opciones=actividad_opciones, capacidad_opciones=capacidad_opciones, participacion_opciones=participacion_opciones, tipo_sangre_opciones=tipo_sangre_opciones, provincia_opciones=provincia_opciones)

        tipo_sangre = request.form.get('tipo_sangre')
        poliza = request.form.get('poliza')
        aseguradora = request.form.get('aseguradora')
        alergias = request.form.get('alergias')
        enfermedades_cronicas = request.form.get('enfermedades_cronicas')

        if not all([username, password, confirm_password, nombre, primer_apellido, telefono]):
            flash('Por favor, completa todos los campos obligatorios (*).', 'danger')
            return render_template('register.html', actividad_opciones=actividad_opciones, capacidad_opciones=capacidad_opciones, participacion_opciones=participacion_opciones, tipo_sangre_opciones=tipo_sangre_opciones, provincia_opciones=provincia_opciones)

        if password != confirm_password:
            flash('Las contraseñas no coinciden.', 'danger')
            return render_template('register.html', actividad_opciones=actividad_opciones, capacidad_opciones=capacidad_opciones, participacion_opciones=participacion_opciones, tipo_sangre_opciones=tipo_sangre_opciones, provincia_opciones=provincia_opciones)

        existing_username = User.query.filter_by(username=username).first()
        if existing_username:
            flash('Ese nombre de usuario ya está en uso. Por favor, elige otro.', 'danger')
            return render_template('register.html', actividad_opciones=actividad_opciones, capacidad_opciones=capacidad_opciones, participacion_opciones=participacion_opciones, tipo_sangre_opciones=tipo_sangre_opciones, provincia_opciones=provincia_opciones)

        # Hacemos el email opcional, pero si se proporciona, lo validamos y verificamos unicidad
        if email:
            email = email.lower() # Convertir el email a minúsculas para consistencia y evitar duplicados por mayúsculas/minúsculas
            # Validación de email básico
            if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                flash('Formato de correo electrónico inválido.', 'danger')
                return render_template('register.html', actividad_opciones=actividad_opciones, capacidad_opciones=capacidad_opciones, participacion_opciones=participacion_opciones, tipo_sangre_opciones=tipo_sangre_opciones, provincia_opciones=provincia_opciones)

            existing_email = User.query.filter_by(email=email).first()
            if existing_email:
                flash('Ese correo electrónico ya está registrado. Por favor, usa otro.', 'danger')
                return render_template('register.html', actividad_opciones=actividad_opciones, capacidad_opciones=capacidad_opciones, participacion_opciones=participacion_opciones, tipo_sangre_opciones=tipo_sangre_opciones, provincia_opciones=provincia_opciones)
        else:
            email = None # Asegurarse de que el email sea None si no se proporciona

        # Eliminado el argumento 'rounds' de la llamada a generate_password_hash
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        avatar_filename = None

        if 'avatar' in request.files:
            avatar_file = request.files['avatar']
            if avatar_file and allowed_file(avatar_file.filename):
                filename = secure_filename(avatar_file.filename)
                avatar_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                avatar_file.save(avatar_path)
                avatar_filename = 'uploads/avatars/' + filename
            elif avatar_file.filename != '':
                flash('Tipo de archivo de avatar no permitido. Solo se aceptan PNG, JPG, JPEG, GIF.', 'warning')
                return render_template('register.html', actividad_opciones=actividad_opciones, capacidad_opciones=capacidad_opciones, participacion_opciones=participacion_opciones, tipo_sangre_opciones=tipo_sangre_opciones, provincia_opciones=provincia_opciones)

        if not avatar_filename:
            avatar_filename = 'images/defaults/default_avatar.png'
        
        # LÓGICA CLAVE PARA ASIGNAR EL ROL DE SUPERUSUARIO
        new_user_role = 'Usuario Regular' # Rol por defecto
        
        # current_app.config.get() es importante por si la bandera no existe (ej. en desarrollo local sin before_request)
        if current_app.config.get('first_user_registration_allowed', False):
            # Doble verificación para evitar problemas de concurrencia
            with app.app_context():
                total_users_after_check = db.session.query(User).count()
                if total_users_after_check == 0:
                    new_user_role = 'Superuser'
                    # Desactivar la bandera inmediatamente después de que se registre el primer superuser
                    current_app.config['first_user_registration_allowed'] = False 
                    print(f"DEBUG: Registrando a {username} como Superuser (primer usuario).")
                else:
                    print(f"DEBUG: Ya existen usuarios (verificación secundaria), {username} se registrará como Usuario Regular.")
        else:
            print(f"DEBUG: 'first_user_registration_allowed' es False, {username} se registrará como Usuario Regular.")
        # FIN LÓGICA CLAVE

        new_user = User(
            username=username,
            password=hashed_password,
            nombre=nombre,
            primer_apellido=primer_apellido,
            telefono=telefono,
            avatar_url=avatar_filename,
            segundo_apellido=segundo_apellido,
            telefono_emergencia=telefono_emergencia,
            nombre_emergencia=nombre_emergencia,
            empresa=empresa,
            cedula=cedula,
            direccion=direccion,
            email=email, # Asignar el email normalizado (puede ser None)
            actividad=actividad if actividad != "No Aplica" else None,
            capacidad=capacidad if capacidad != "Seleccionar Capacidad" else None,
            participacion=participacion if participacion != "No Aplica" else None,
            # NUEVOS CAMPOS: Asignar valores al modelo
            fecha_cumpleanos=fecha_cumpleanos,
            tipo_sangre=tipo_sangre if tipo_sangre != "Seleccionar Tipo" else None,
            poliza=poliza,
            aseguradora=aseguradora,
            alergias=alergias,
            enfermedades_cronicas=enfermedades_cronicas,
            role=new_user_role # Asignar el rol determinado aquí
        )

        try:
            db.session.add(new_user)
            db.session.commit()
            flash('¡Registro exitoso! Ahora puedes iniciar sesión.', 'success')

            if 'logged_in' in session and session['logged_in']:
                return redirect(url_for('contactos.ver_contactos'))
            else:
                return redirect(url_for('login'))

        except IntegrityError as e: # Captura errores específicos de unicidad de la base de datos
            db.session.rollback()
            # Verifica si el error se relaciona con el campo 'email' o 'username'
            error_message = str(e)
            if "UNIQUE constraint failed: user.email" in error_message:
                flash('Ese correo electrónico ya está registrado. Por favor, usa otro.', 'danger')
            elif "UNIQUE constraint failed: user.username" in error_message:
                flash('Ese nombre de usuario ya está en uso. Por favor, elige otro.', 'danger')
            else:
                # Para otros errores de integridad inesperados
                flash('Ocurrió un error de integridad de datos. Por favor, inténtalo de nuevo.', 'danger')
                current_app.logger.error(f"IntegrityError durante el registro: {e}") # Log para depuración

            return render_template('register.html', actividad_opciones=actividad_opciones, capacidad_opciones=capacidad_opciones, participacion_opciones=participacion_opciones, tipo_sangre_opciones=tipo_sangre_opciones, provincia_opciones=provincia_opciones)

        except Exception as e: # Captura cualquier otra excepción general
            db.session.rollback()
            flash(f'Ocurrió un error inesperado al registrar el usuario: {e}', 'danger')
            current_app.logger.error(f"Error general durante el registro: {e}") # Log para depuración
            return render_template('register.html', actividad_opciones=actividad_opciones, capacidad_opciones=capacidad_opciones, participacion_opciones=participacion_opciones, tipo_sangre_opciones=tipo_sangre_opciones, provincia_opciones=provincia_opciones)

    # Si es GET, renderiza el formulario
    return render_template('register.html', actividad_opciones=actividad_opciones, capacidad_opciones=capacidad_opciones, participacion_opciones=participacion_opciones, tipo_sangre_opciones=tipo_sangre_opciones, provincia_opciones=provincia_opciones)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username_or_email = request.form['username_or_email']
        password = request.form['password']

        user = User.query.filter_by(username=username_or_email).first()

        if not user and '@' in username_or_email: # Intentar buscar por email si contiene '@'
            user = User.query.filter_by(email=username_or_email.lower()).first() # Normalizar para login también

        if user and bcrypt.check_password_hash(user.password, password):
            session['logged_in'] = True
            session['username'] = user.username
            session['email'] = user.email
            session['user_id'] = user.id # NUEVA: Almacenar user_id en la sesión
            session['role'] = user.role # NUEVA: Almacenar el rol del usuario en la sesión
            # Actualizar last_login_at
            user.last_login_at = datetime.utcnow()
            db.session.commit()
            flash('¡Sesión iniciada correctamente!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Nombre de usuario/correo electrónico o contraseña incorrectos.', 'danger')
            return render_template('login.html')
    return render_template('login.html')

@app.route('/home')
def home():
    # Obtener todas las caminatas (similar a como lo hace ver_caminatas en caminatas.py)
    all_caminatas = Caminata.query.order_by(Caminata.fecha.desc()).all()
    search_actividad = request.args.get('actividad')

    if search_actividad:
        caminatas = Caminata.query.filter_by(actividad=search_actividad).all()
    else:
        caminatas = Caminata.query.all()
        
    return render_template('ver_caminatas.html', caminatas=caminatas, search_actividad=search_actividad)

@app.route('/logout')
def logout():
    session.clear()
    flash('Has cerrado sesión.', 'success')
    return redirect(url_for('login'))

# Registra los Blueprints después de que la app haya sido inicializada
app.register_blueprint(contactos_bp)
app.register_blueprint(perfil_bp, url_prefix='/perfil')
app.register_blueprint(proyecto_bp)
app.register_blueprint(notas_bp) # NUEVA: Registro del Blueprint de Notas
app.register_blueprint(intern_bp, url_prefix='/intern') # ¡Añade esta línea!
app.register_blueprint(caminatas_bp, url_prefix='/caminatas') # NUEVA: Registro del Blueprint de Caminatas
app.register_blueprint(pagos_bp, url_prefix='/pagos') # NUEVA: Registro del Blueprint de Pagos
app.register_blueprint(calendario_bp, url_prefix='/calendario') # NUEVA: Registro del Blueprint de Calendario
app.register_blueprint(instrucciones_bp, url_prefix='/instrucciones') # NUEVA: Registro del Blueprint de Instrucciones
app.register_blueprint(player_bp)
app.register_blueprint(itinerario_bp, url_prefix='/itinerario') # NUEVA: Registro del Blueprint de Itinerario
app.register_blueprint(aboutus_bp, url_prefix='/aboutus') # NUEVA: Registro del Blueprint de AboutUs
app.register_blueprint(rutas_bp, url_prefix='/rutas') # NUEVA: Registro del Blueprint de Rutas
app.register_blueprint(version_bp, url_prefix='/version') # NUEVA: Registro del Blueprint de Version
app.register_blueprint(files_bp, url_prefix='/files') # NUEVA: Registro del Blueprint de Files


if __name__ == '__main__':
    with app.app_context(): # Usar app_context para db.create_all()
        db.create_all()
    app.run(host='0.0.0.0', debug=True, port=3030)
    

# Migraciones Cmder
        # set FLASK_APP=app.py     <--Crea un directorio de migraciones
        # flask db init             <--
        # $ flask db stamp head
        # $ flask db migrate
        # $ flask db migrate -m "mensaje x"
        # $ flask db upgrade
        # ERROR [flask_migrate] Error: Target database is not up to date.
        # $ flask db stamp head
        # $ flask db migrate
        # $ flask db upgrade
        # git clone https://github.com/kerm1977/MI_APP_FLASK.git
        # mysql> DROP DATABASE kenth1977$db; PYTHONANYWHATE
# -----------------------

# del db.db
# rmdir /s /q migrations
# flask db init
# flask db migrate -m "Reinitial migration with all correct models"
# flask db upgrade


# -----------------------
# Consola de pythonanywhere ante los errores de versiones
# Error: Can't locate revision identified by '143967eb40c0'

# flask db stamp head
# lask db migrate
# flask db upgrade

# Database pythonanywhere
# kenth1977$db
# DROP TABLE alembic_version;
# rm -rf migrations
# flask db init
# flask db migrate -m "Initial migration after reset"
# flask db upgrade

# Cuando se cambia de repositorio
# git remote -v
# git remote add origin <URL_DEL_REPOSITORIO>
# git remote set-url origin <NUEVA_URL_DEL_REPOSITORIO>
# git branchgit remote -v
# git push -u origin flet
