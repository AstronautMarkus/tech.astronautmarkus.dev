from flask import flash, redirect, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import or_

from . import auth_bp
from app import db, get_current_language, render_localized_template
from app.models.models import User


def _safe_next_url(next_url):
    return bool(next_url) and next_url.startswith('/')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home.index'))

    errors = {}
    form_data = {
        'username': '',
        'email': '',
    }

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        form_data['username'] = username
        form_data['email'] = email

        lang = get_current_language()

        if not username or not email or not password:
            if not username:
                errors['username'] = 'El usuario es obligatorio.' if lang == 'es' else 'Username is required.'
            if not email:
                errors['email'] = 'El correo es obligatorio.' if lang == 'es' else 'Email is required.'
            if not password:
                errors['password'] = 'La contraseña es obligatoria.' if lang == 'es' else 'Password is required.'

        if not confirm_password:
            errors['confirm_password'] = (
                'Debes confirmar la contraseña.' if lang == 'es' else 'Password confirmation is required.'
            )

        if password and confirm_password and password != confirm_password:
            errors['confirm_password'] = (
                'Las contraseñas no coinciden.' if lang == 'es' else 'Passwords do not match.'
            )

        if not errors:
            username_exists = User.query.filter_by(username=username).first()
            email_exists = User.query.filter_by(email=email).first()

            if username_exists:
                errors['username'] = 'Ese usuario ya está registrado.' if lang == 'es' else 'That username is already registered.'

            if email_exists:
                errors['email'] = 'Ese correo ya está registrado.' if lang == 'es' else 'That email is already registered.'

        if not errors:
            user = User(
                username=username,
                email=email,
                is_active=True,
                is_admin=False,
            )
            user.set_password(password)
            db.session.add(user)
            db.session.commit()

            login_user(user)
            return redirect(url_for('home.index'))

    return render_localized_template('auth/register.html', errors=errors, form_data=form_data)


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


@auth_bp.route('/logout')
@login_required
def logout():
    lang = get_current_language()
    logout_user()

    if lang == 'es':
        flash('Sesión cerrada correctamente.', 'success')
    else:
        flash('Signed out successfully.', 'success')

    return redirect(url_for('auth.login'))
