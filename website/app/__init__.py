from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from app.config.config import Config
from werkzeug.middleware.proxy_fix import ProxyFix
from datetime import datetime


db = SQLAlchemy()
migrate = Migrate()

def create_app():
	app = Flask(__name__)
	app.config.from_object(Config)

	db.init_app(app)
	migrate.init_app(app, db)

	app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

	@app.context_processor
	def current_year():
		return {'current_year': datetime.utcnow().year}

	from app.routes.home import home_bp
	app.register_blueprint(home_bp)

	return app