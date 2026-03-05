from . import home_bp
from flask import render_template

@home_bp.route('/')
def home():
    return render_template('home.html')