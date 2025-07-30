from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app, send_file
# Importa db y User desde 'models' para evitar la importación circular.
from models import db, User 
import os
from datetime import datetime, date # Importar date para manejar fechas
from werkzeug.utils import secure_filename # Importar para manejo de archivos
import shutil # Importar para copiar archivos (para backup y restore)
from functools import wraps # Importar wraps desde functools

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

@perfil_bp.route('/perfil')
@role_required(['Superuser', 'Usuario Regular'])
def perfil():
    user_id = session.get('user_id')
    if not user_id:
        flash('No se encontró el ID de usuario en la sesión.', 'danger')
        return redirect(url_for('login'))

    user = User.query.get(user_id)
    if not user:
        flash('Usuario no encontrado.', 'danger')
        return redirect(url_for('login'))

    avatar_url = None
    if user.avatar_url:
        # Asume que avatar_url es la ruta relativa desde static/
        avatar_url = url_for('static', filename=user.avatar_url)
    
    return render_template('perfil.html', user=user, avatar_url=avatar_url)

@perfil_bp.route('/editar_perfil', methods=['GET', 'POST'])
@role_required(['Superuser', 'Usuario Regular'])
def editar_perfil():
    user_id = session.get('user_id')
    if not user_id:
        flash('No se encontró el ID de usuario en la sesión.', 'danger')
        return redirect(url_for('login'))

    user = db.session.get(User, user_id)
    if not user:
        flash('Usuario no encontrado para editar.', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        user.nombre = request.form['nombre']
        user.primer_apellido = request.form['primer_apellido']
        user.segundo_apellido = request.form.get('segundo_apellido')
        user.telefono = request.form['telefono']
        user.email = request.form['email']
        user.telefono_emergencia = request.form.get('telefono_emergencia')
        user.nombre_emergencia = request.form.get('nombre_emergencia')
        user.direccion = request.form.get('direccion')
        user.cedula = request.form.get('cedula')
        user.empresa = request.form.get('empresa')
        user.tipo_sangre = request.form.get('tipo_sangre')
        user.poliza = request.form.get('poliza')
        user.aseguradora = request.form.get('aseguradora')
        user.alergias = request.form.get('alergias')
        user.enfermedades_cronicas = request.form.get('enfermedades_cronicas')

        # Campos solo editables por Superuser
        if session.get('role') == 'Superuser':
            user.actividad = request.form.get('actividad')
            user.capacidad = request.form.get('capacidad')
            user.participacion = request.form.get('participacion')
            user.role = request.form.get('role') # Permitir cambiar el rol

        fecha_cumpleanos_str = request.form.get('fecha_cumpleanos')
        if fecha_cumpleanos_str:
            try:
                user.fecha_cumpleanos = datetime.strptime(fecha_cumpleanos_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Formato de fecha de cumpleaños inválido. Usa YYYY-MM-DD.', 'danger')
                return redirect(url_for('perfil.editar_perfil'))

        # Manejo de la subida de avatar
        if 'avatar' in request.files:
            avatar_file = request.files['avatar']
            if avatar_file and avatar_file.filename != '':
                # Generar un nombre de archivo único
                filename = secure_filename(avatar_file.filename)
                unique_filename = str(uuid.uuid4()) + os.path.splitext(filename)[1]
                
                # Definir la ruta de guardado
                upload_folder = current_app.config.get('UPLOAD_FOLDER')
                if not upload_folder:
                    flash('Error de configuración: Carpeta de subida de avatares no definida.', 'danger')
                    return redirect(url_for('perfil.editar_perfil'))

                # Asegurarse de que el directorio exista
                os.makedirs(upload_folder, exist_ok=True)
                
                file_path = os.path.join(upload_folder, unique_filename)
                avatar_file.save(file_path)
                
                # Actualizar la URL del avatar en el usuario
                user.avatar_url = os.path.join('uploads', 'avatars', unique_filename).replace('\\', '/') # Ruta relativa para URL

        user.fecha_actualizacion = datetime.utcnow() # Actualizar fecha de actualización

        try:
            db.session.commit()
            flash('Perfil actualizado exitosamente.', 'success')
            return redirect(url_for('perfil.perfil'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar el perfil: {e}', 'danger')
            current_app.logger.error(f"Error al actualizar perfil del usuario {user_id}: {e}")

    return render_template('editar_perfil.html', user=user)

@perfil_bp.route('/backup_database', methods=['POST'])
@role_required(['Superuser']) # Solo Superusers pueden hacer backup
def backup_database():
    try:
        # Ruta de la base de datos actual (ahora app.db en la carpeta instance)
        # MODIFICADO: Apunta a 'app.db' en la carpeta 'instance'
        db_path = os.path.join(current_app.instance_path, 'app.db')
        
        # Crear la carpeta de backups si no existe
        backup_folder = os.path.join(current_app.root_path, 'backups')
        os.makedirs(backup_folder, exist_ok=True)

        # Nombre del archivo de backup con marca de tiempo
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'app_backup_{timestamp}.db' # Nombre de backup refleja 'app.db'
        backup_filepath = os.path.join(backup_folder, backup_filename)

        # Copiar el archivo de la base de datos
        shutil.copyfile(db_path, backup_filepath)

        flash(f'Backup de la base de datos "{backup_filename}" creado exitosamente.', 'success')
        
        # Permitir la descarga directa del backup
        return send_file(backup_filepath, as_attachment=True, download_name=backup_filename)

    except Exception as e:
        flash(f'Error al crear el backup de la base de datos: {e}', 'danger')
        current_app.logger.error(f"Error al crear backup de la base de datos: {e}")
        return redirect(url_for('perfil.perfil'))

@perfil_bp.route('/restore_database', methods=['POST'])
@role_required(['Superuser']) # Solo Superusers pueden restaurar la base de datos
def restore_database():
    # Es altamente recomendable que esta operación se realice con la aplicación detenida
    # o en un entorno de mantenimiento para evitar corrupción de datos.
    # En un entorno de producción, esto requeriría un reinicio del servidor.

    # Obtener la ruta del archivo de backup desde el formulario o parámetro
    backup_filename = request.form.get('backup_filename')
    if not backup_filename:
        flash('No se especificó ningún archivo de backup para restaurar.', 'danger')
        return redirect(url_for('perfil.perfil'))

    backup_folder = os.path.join(current_app.root_path, 'backups')
    backup_filepath = os.path.join(backup_folder, backup_filename)

    # Ruta de la base de datos actual (ahora app.db en la carpeta instance)
    # MODIFICADO: Apunta a 'app.db' en la carpeta 'instance'
    db_path = os.path.join(current_app.instance_path, 'app.db') 

    if not os.path.exists(backup_filepath):
        flash(f'El archivo de backup "{backup_filename}" no fue encontrado.', 'danger')
        return redirect(url_for('perfil.perfil'))

    try:
        # Primero, hacer una copia de seguridad de la base de datos actual ANTES de restaurar
        # Esto es una medida de seguridad adicional
        temp_backup_filename = f'pre_restore_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
        temp_backup_filepath = os.path.join(backup_folder, temp_backup_filename)
        if os.path.exists(db_path):
            shutil.copyfile(db_path, temp_backup_filepath)
            flash(f'Se creó una copia de seguridad temporal de la base de datos actual: "{temp_backup_filename}".', 'info')

        # Reemplazar la base de datos actual con el archivo de backup
        shutil.copyfile(backup_filepath, db_path)

        flash(f'Base de datos restaurada exitosamente desde "{backup_filename}".', 'success')
        flash('¡IMPORTANTE! Reinicia tu aplicación Flask para que los cambios surtan efecto.', 'warning')
        
    except Exception as e:
        flash(f'Error al restaurar la base de datos: {e}', 'danger')
        current_app.logger.error(f"Error al restaurar base de datos desde {backup_filename}: {e}")

    return redirect(url_for('perfil.perfil'))

