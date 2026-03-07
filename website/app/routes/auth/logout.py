from flask import flash, redirect, url_for
from flask_login import login_required, logout_user

from . import auth_bp
from app import get_current_language

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    lang = get_current_language()
    logout_user()

    if lang == 'es':
        flash('Sesión cerrada correctamente.', 'success')
    else:
        flash('Signed out successfully.', 'success')

    return redirect(url_for('auth.login'))
