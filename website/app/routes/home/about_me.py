from . import home_bp
from app import render_localized_template

@home_bp.route('/about-me')
def about_me():
    return render_localized_template('about_me.html')