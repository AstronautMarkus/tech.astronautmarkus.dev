from . import admin_bp
from flask import render_template

@admin_bp.route('/')
def admin_index():
    return render_template('admin/index.html')