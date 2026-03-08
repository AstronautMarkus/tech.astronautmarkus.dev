from flask import Blueprint
    
home_bp = Blueprint('home', __name__, template_folder='templates')

from . import (
    index,
    youtube_channel,
    about_me
)