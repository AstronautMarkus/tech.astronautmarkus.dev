from flask import abort, current_app
from . import home_bp
from app import render_localized_template
from app.models.models import MiniBlog
import os
import markdown


@home_bp.route('/mini-blog')
def mini_blog_list():
    """List all available blogs"""
    blogs = MiniBlog.query.order_by(MiniBlog.created_at.desc()).all()
    
    return render_localized_template(
        'mini_blog_list.html',
        blogs=blogs
    )


@home_bp.route('/mini-blog/<int:blog_id>')
def mini_blog_detail(blog_id):
    """Show details for a specific blog"""
    blog = MiniBlog.query.get_or_404(blog_id)
    
    # Read markdown file
    filepath = os.path.join(
        current_app.root_path,
        'static',
        'blog_posts',
        blog.markdown_file
    )
    
    if not os.path.exists(filepath):
        current_app.logger.error(f'File not found: {filepath}')
        abort(404)
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
        
        # Convert markdown to HTML
        html_content = markdown.markdown(
            markdown_content,
            extensions=['fenced_code', 'tables', 'nl2br']
        )
        
        return render_localized_template(
            'mini_blog_detail.html',
            blog=blog,
            content=html_content
        )
        
    except Exception as e:
        current_app.logger.error(f'Error reading markdown file: {str(e)}')
        abort(500)
