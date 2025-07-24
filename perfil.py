from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app, send_file
# Importa db y User desde 'models' para evitar la importación circular.
from models import db, User 
import os
from datetime import datetime, date # Importar date para manejar fechas
from werkzeug.utils import secure_filename # Importar para manejo de archivos
import shutil # Importar para copiar archivos (para backup)
from functools import wraps # Importar wraps desde functools - ¡CORRECCIÓN AQUÍ!

# Asumo que role_required está definido globalmente o se importa desde app.py o un archivo de utilidades.
# Si no es así, necesitarías importarlo:
# from app import role_required # O desde donde lo tengas definido
# DECORADOR PARA ROLES (Si no lo importas de app.py, puedes tenerlo aquí o en un archivo de utilidades)
def role_required(roles):
    """
    Decorador para restringir el acceso a rutas basadas en roles.
    `roles` puede ser una cadena (un solo rol) o una lista de cadenas (múltiples roles).
    """
    if not isinstance(roles, list):
        roles = [roles]

    def decorator(f):
        @wraps(f) # Importar wraps desde functools
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


perfil_bp = Blueprint('perfil', __name__)

@perfil_bp.route('/') # Esta ruta mostrará la información del perfil del usuario logueado
def ver_perfil():
    if 'user_id' not in session:
        flash('Necesitas iniciar sesión para ver tu perfil.', 'danger')
        return redirect(url_for('login'))

    user_id = session['user_id']
    user = db.session.get(User, user_id) 

    if not user:
        flash('Usuario no encontrado.', 'danger')
        return redirect(url_for('home')) # O a una página de error

    avatar_url = url_for('static', filename=user.avatar_url) if user.avatar_url else url_for('static', filename='images/defaults/default_avatar.png')

    # Para renderizar detalle_contactos.html con la información del usuario logueado
    # Importante: aquí se usa 'perfil.html' como se ha solicitado para mostrar la información del usuario
    return render_template(
        'perfil.html', # Ahora renderiza perfil.html directamente
        user=user,
        avatar_url=avatar_url
    )

@perfil_bp.route('/editar', methods=['GET', 'POST']) # Ruta cambiada a '/editar' para url_prefix
def editar_perfil():
    if 'user_id' not in session:
        flash('Necesitas iniciar sesión para editar tu perfil.', 'danger')
        return redirect(url_for('login'))

    user_id = session['user_id']
    user = db.session.get(User, user_id) 

    # Opciones para los campos select (igual que en editar_contacto.html)
    provincia_opciones = ["San José", "Alajuela", "Cartago", "Heredia", "Guanacaste", "Puntarenas", "Limón"]
    tipo_sangre_opciones = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-", "Desconocido"]
    actividad_opciones = ["No Aplica", "La Tribu", "Senderista", "Enfermería", "Cocina", "Confección y Diseño", "Restaurante", "Transporte Terrestre", "Transporte Acuatico", "Transporte Aereo", "Migración", "Parque Nacional", "Refugio Silvestre", "Centro de Atracción", "Lugar para Caminata", "Acarreo", "Oficina de trámite", "Primeros Auxilios", "Farmacia", "Taller", "Abogado", "Mensajero", "Tienda", "Polizas", "Aerolínea", "Guía", "Banco", "Otros"]
    capacidad_opciones = ["Seleccionar Capacidad", "Rápido", "Intermedio", "Básico", "Iniciante"]
    participacion_opciones = ["No Aplica", "Solo de La Tribu", "Constante", "Inconstante", "El Camino de Costa Rica", "Parques Nacionales", "Paseo | Recreativo", "Revisar/Eliminar"]

    if request.method == 'POST':
        # Actualiza los campos del usuario con los datos del formulario
        user.nombre = request.form['nombre']
        user.primer_apellido = request.form['primer_apellido']
        user.segundo_apellido = request.form.get('segundo_apellido')
        user.username = request.form['username']
        user.email = request.form['email']
        user.telefono = request.form['telefono']
        user.telefono_emergencia = request.form.get('telefono_emergencia')
        user.nombre_emergencia = request.form.get('nombre_emergencia')
        user.empresa = request.form.get('empresa')
        user.cedula = request.form.get('cedula')
        user.direccion = request.form.get('direccion') # Ahora es la provincia
        
        # Manejo de fecha de cumpleaños
        fecha_cumpleanos_str = request.form.get('fecha_cumpleanos')
        if fecha_cumpleanos_str:
            try:
                user.fecha_cumpleanos = datetime.strptime(fecha_cumpleanos_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Formato de fecha de cumpleaños inválido.', 'danger')
        else:
            user.fecha_cumpleanos = None # Si el campo está vacío, establece a None

        user.tipo_sangre = request.form.get('tipo_sangre') if request.form.get('tipo_sangre') != "Seleccionar Tipo" else None
        user.poliza = request.form.get('poliza')
        user.aseguradora = request.form.get('aseguradora')
        user.alergias = request.form.get('alergias')
        user.enfermedades_cronicas = request.form.get('enfermedades_cronicas')
        user.actividad = request.form.get('actividad') if request.form.get('actividad') != "No Aplica" else None
        user.capacidad = request.form.get('capacidad') if request.form.get('capacidad') != "Seleccionar Capacidad" else None
        user.participacion = request.form.get('participacion') if request.form.get('participacion') != "No Aplica" else None


        # Manejo de la imagen de avatar
        if 'avatar' in request.files and request.files['avatar'].filename != '':
            avatar_file = request.files['avatar']
            # Accede a allowed_file y UPLOAD_FOLDER a través de current_app
            if avatar_file and current_app.allowed_file(avatar_file.filename):
                filename = secure_filename(avatar_file.filename)
                avatar_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                avatar_file.save(avatar_path)
                user.avatar_url = 'uploads/avatars/' + filename
            elif avatar_file.filename != '':
                flash('Tipo de archivo de avatar no permitido. Solo se aceptan PNG, JPG, JPEG, GIF.', 'warning')
        
        try:
            db.session.commit()
            flash('Tu perfil ha sido actualizado exitosamente.', 'success')
            return redirect(url_for('perfil.ver_perfil')) # Redirige de vuelta al perfil después de editar
        except Exception as e:
            db.session.rollback()
            flash(f'Hubo un error al actualizar tu perfil: {e}', 'danger')

    # Para mostrar el avatar actual si existe
    avatar_url = url_for('static', filename=user.avatar_url) if user.avatar_url else url_for('static', filename='images/defaults/default_avatar.png')

    return render_template(
        'editar_contacto.html',
        user=user,
        avatar_url=avatar_url,
        provincia_opciones=provincia_opciones,
        tipo_sangre_opciones=tipo_sangre_opciones,
        actividad_opciones=actividad_opciones,
        capacidad_opciones=capacidad_opciones,
        participacion_opciones=participacion_opciones
    )

# NUEVA RUTA PARA BACKUP DE LA BASE DE DATOS DENTRO DEL BLUEPRINT 'perfil'
@perfil_bp.route('/backup_database', methods=['POST'])
@role_required('Superuser') # Solo Superusers pueden hacer backup
def backup_database():
    try:
        # Ruta de la base de datos actual (asumiendo SQLite en la carpeta 'instance')
        # Asegúrate de que 'instance' esté en la misma carpeta que app.py o ajusta la ruta
        db_path = os.path.join(current_app.instance_path, 'db.db')
        
        # Crear la carpeta de backups si no existe
        backup_folder = os.path.join(current_app.root_path, 'backups')
        os.makedirs(backup_folder, exist_ok=True)

        # Nombre del archivo de backup con marca de tiempo
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'db_backup_{timestamp}.db'
        backup_filepath = os.path.join(backup_folder, backup_filename)

        # Copiar el archivo de la base de datos
        shutil.copyfile(db_path, backup_filepath)

        flash(f'Backup de la base de datos "{backup_filename}" creado exitosamente.', 'success')
        
        # Permitir la descarga directa del backup
        return send_file(backup_filepath, as_attachment=True, download_name=backup_filename)

    except Exception as e:
        flash(f'Error al crear el backup de la base de datos: {e}', 'danger')
        current_app.logger.error(f"Error al crear backup de la base de datos: {e}")
        # Redirige a donde el usuario estaba o a una página de administración
        return redirect(request.referrer or url_for('perfil.ver_perfil')) # Redirige al perfil después del backup

