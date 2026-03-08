from flask import request, jsonify, current_app
from flask_login import current_user
from werkzeug.utils import secure_filename
from . import admin_bp
from app import db, get_current_language, render_localized_template
from app.models.models import MiniBlog
import os
import uuid


ALLOWED_EXTENSIONS = {'md'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@admin_bp.route('/mini-blog-admin')
def mini_blog_admin():
    return render_localized_template('admin/mini_blog.html')


@admin_bp.route('/mini-blog', methods=['GET'])
def list_blogs():
    blogs = MiniBlog.query.order_by(MiniBlog.created_at.desc()).all()
    
    return jsonify({
        'success': True,
        'blogs': [{
            'id': blog.id,
            'title': blog.title,
            'markdown_file': blog.markdown_file,
            'author_id': blog.author_id,
            'created_at': blog.created_at.isoformat(),
            'updated_at': blog.updated_at.isoformat()
        } for blog in blogs]
    }), 200


@admin_bp.route('/mini-blog', methods=['POST'])
def create_blog():

    lang = get_current_language()

    # Check if the post request has the file part
    if 'file' not in request.files:
        return jsonify({
            'success': False,
            'message': 'No file part in the request' if lang == 'en' else 'No se encontró el archivo en la solicitud'
        }), 400
    
    file = request.files['file']
    title = request.form.get('title', '').strip()
    
    # Validate title
    if not title:
        return jsonify({
            'success': False,
            'message': 'Title is required' if lang == 'en' else 'El título es obligatorio'
        }), 400
    
    # Validate that a file was selected
    if file.filename == '':
        return jsonify({
            'success': False,
            'message': 'No file was selected' if lang == 'en' else 'No se seleccionó ningún archivo'
        }), 400
    
    # Validate file extension
    if not allowed_file(file.filename):
        return jsonify({
            'success': False,
            'message': 'Only .md files are allowed' if lang == 'en' else 'Solo se permiten archivos .md'
        }), 400
    
    try:
        # Generate a unique filename
        original_filename = secure_filename(file.filename)
        base_filename = original_filename.rsplit('.', 1)[0]
        unique_id = str(uuid.uuid4())[:8]
        filename = f"{base_filename}_{unique_id}.md"
        
        # Save file
        upload_folder = os.path.join(current_app.root_path, 'static', 'blog_posts')
        os.makedirs(upload_folder, exist_ok=True)
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)
        
        # Create database record
        blog = MiniBlog(
            title=title,
            markdown_file=filename,
            author_id=current_user.id
        )
        
        db.session.add(blog)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Blog created successfully' if lang == 'en' else 'Blog creado exitosamente',
            'blog': {
                'id': blog.id,
                'title': blog.title,
                'markdown_file': blog.markdown_file,
                'author_id': blog.author_id,
                'created_at': blog.created_at.isoformat(),
                'updated_at': blog.updated_at.isoformat()
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error creating blog: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error creating blog' if lang == 'en' else 'Error al crear el blog'
        }), 500


@admin_bp.route('/mini-blog/<int:blog_id>', methods=['DELETE'])
def delete_blog(blog_id):

    lang = get_current_language()

    blog = MiniBlog.query.get(blog_id)
    
    if not blog:
        return jsonify({
            'success': False,
            'message': 'Blog not found' if lang == 'en' else 'Blog no encontrado'
        }), 404
    
    try:
        # Delete file from filesystem
        filepath = os.path.join(
            current_app.root_path, 
            'static', 
            'blog_posts', 
            blog.markdown_file
        )
        
        if os.path.exists(filepath):
            os.remove(filepath)
        
        # Delete database record
        db.session.delete(blog)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Blog deleted successfully' if lang == 'en' else 'Blog eliminado exitosamente'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error deleting blog: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error deleting blog' if lang == 'en' else 'Error al eliminar el blog'
        }), 500
