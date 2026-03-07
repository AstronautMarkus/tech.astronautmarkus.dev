from flask import abort
from flask_login import current_user


def check_user_is_admin():
	if not current_user.is_authenticated:
		return None

	if not bool(current_user.is_admin):
		abort(403)

	return None
