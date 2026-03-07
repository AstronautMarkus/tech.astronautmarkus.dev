from flask import Blueprint
from app.middleware.check_user_is_admin import check_user_is_admin

admin_bp = Blueprint('admin', __name__, url_prefix='/admin', template_folder='templates')
admin_bp.before_request(check_user_is_admin)

from . import (
    index
)