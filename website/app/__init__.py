from flask import Flask, g, redirect, render_template, request, url_for, current_app
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from app.config.config import Config
from werkzeug.middleware.proxy_fix import ProxyFix
from datetime import datetime
from jinja2 import TemplateNotFound


SUPPORTED_LANGUAGES = ('en', 'es')
LANG_COOKIE_NAME = 'lang'
ERROR_STATUS_CODES = (400, 401, 403, 404, 405, 429, 500, 502, 503, 504)

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'warning'


@login_manager.user_loader
def load_user(user_id):
	from app.models.models import User

	try:
		user_id = int(user_id)
	except (TypeError, ValueError):
		return None

	return User.query.get(user_id)


def get_current_language():
	lang = getattr(g, 'current_lang', None)
	if lang in SUPPORTED_LANGUAGES:
		return lang
	return 'en'


def localized_template_name(template_name):
	lang = get_current_language()
	if lang == 'en':
		return template_name

	dot_index = template_name.rfind('.')
	if dot_index == -1:
		candidate = f'{template_name}_{lang}'
	else:
		candidate = f'{template_name[:dot_index]}_{lang}{template_name[dot_index:]}'

	try:
		current_app.jinja_loader.get_source(current_app.jinja_env, candidate)
		return candidate
	except TemplateNotFound:
		return template_name


def render_localized_template(template_name, **context):
	return render_template(localized_template_name(template_name), **context)

def create_app():
	app = Flask(__name__)
	app.config.from_object(Config)

	db.init_app(app)
	migrate.init_app(app, db)
	login_manager.init_app(app)

	app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

	@app.before_request
	def detect_language():
		lang = request.cookies.get(LANG_COOKIE_NAME)
		if lang not in SUPPORTED_LANGUAGES:
			lang = request.accept_languages.best_match(SUPPORTED_LANGUAGES) or 'en'
		g.current_lang = lang

	@app.context_processor
	def current_year():
		return {
			'current_year': datetime.utcnow().year,
			'current_lang': get_current_language()
		}

	@app.get('/lang/<lang_code>')
	def set_language(lang_code):
		lang = lang_code.lower()
		if lang not in SUPPORTED_LANGUAGES:
			lang = 'en'

		next_url = request.args.get('next', '')
		if not next_url.startswith('/'):
			next_url = url_for('home.home')

		response = redirect(next_url)
		response.set_cookie(
			LANG_COOKIE_NAME,
			lang,
			max_age=60 * 60 * 24 * 365,
			samesite='Lax'
		)
		return response

	def handle_http_error(error):
		status_code = getattr(error, 'code', 500)
		if status_code not in ERROR_STATUS_CODES:
			status_code = 500
		return render_localized_template(f'error/{status_code}.html'), status_code

	for status_code in ERROR_STATUS_CODES:
		app.register_error_handler(status_code, handle_http_error)

	from app.routes.home import home_bp
	from app.routes.auth import auth_bp
	app.register_blueprint(home_bp)
	app.register_blueprint(auth_bp)

	return app