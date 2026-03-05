from . import home_bp
from app import render_localized_template

@home_bp.route('/')
def index():
    return render_localized_template('home.html')