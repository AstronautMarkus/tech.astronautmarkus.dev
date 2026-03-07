from flask import redirect, request, url_for
from flask_login import current_user, login_user
from sqlalchemy import or_

from . import auth_bp
from app import get_current_language, render_localized_template
from app.models.models import User


def _safe_next_url(next_url):
    return bool(next_url) and next_url.startswith('/')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home.index'))

    next_url = request.args.get('next', '')
    errors = {}
    form_data = {
        'identifier': '',
        'remember': False,
    }

    if request.method == 'POST':
        identifier = request.form.get('identifier', '').strip()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))

        form_data['identifier'] = identifier
        form_data['remember'] = remember

        lang = get_current_language()

        if not identifier:
            errors['identifier'] = 'Usuario o correo obligatorio.' if lang == 'es' else 'Username or email is required.'

        if not password:
            errors['password'] = 'Contraseña obligatoria.' if lang == 'es' else 'Password is required.'

        if not errors:
            user = User.query.filter(
                or_(User.username == identifier, User.email == identifier)
            ).first()

            if user and user.is_active and user.check_password(password):
                login_user(user, remember=remember)

                target_url = request.form.get('next', '')
                if not _safe_next_url(target_url):
                    target_url = url_for('home.index')

                return redirect(target_url)

            errors['password'] = 'Credenciales inválidas.' if lang == 'es' else 'Invalid credentials.'

    return render_localized_template(
        'auth/login.html',
        next_url=next_url,
        errors=errors,
        form_data=form_data,
    )