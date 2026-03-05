from flask import Flask, g, redirect, render_template, request, url_for, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from app.config.config import Config
from werkzeug.middleware.proxy_fix import ProxyFix
from datetime import datetime
from jinja2 import TemplateNotFound


SUPPORTED_LANGUAGES = ('en', 'es')
LANG_COOKIE_NAME = 'lang'

db = SQLAlchemy()
migrate = Migrate()


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
	
	@app.errorhandler(404)
	def page_not_found(e):
		return render_localized_template('error/404.html'), 404

	from app.routes.home import home_bp
	app.register_blueprint(home_bp)

	return app