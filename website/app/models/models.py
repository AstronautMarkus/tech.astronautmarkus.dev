from .. import db
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash


class User(UserMixin, db.Model):
	__tablename__ = 'users'

	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(80), unique=True, nullable=False, index=True)
	email = db.Column(db.String(255), unique=True, nullable=False, index=True)
	password_hash = db.Column(db.String(255), nullable=False)
	is_active = db.Column(db.Boolean, nullable=False, default=True)
	is_admin = db.Column(db.Boolean, nullable=False, default=False)
	created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
	updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

	def set_password(self, password):
		self.password_hash = generate_password_hash(password)

	def check_password(self, password):
		return check_password_hash(self.password_hash, password)


class YoutubeChannelCache(db.Model):
	__tablename__ = 'youtube_channel_cache'

	id = db.Column(db.Integer, primary_key=True)
	channel_url = db.Column(db.String(255), unique=True, nullable=False, index=True)
	last_synced_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class YoutubeVideo(db.Model):
	__tablename__ = 'youtube_videos'

	id = db.Column(db.Integer, primary_key=True)
	channel_url = db.Column(db.String(255), nullable=False, index=True)
	video_id = db.Column(db.String(64), nullable=False)
	title = db.Column(db.String(255), nullable=False)
	published = db.Column(db.String(32), nullable=True)
	video_url = db.Column(db.String(255), nullable=False)
	thumbnail_url = db.Column(db.String(512), nullable=True)

	__table_args__ = (
		db.UniqueConstraint('channel_url', 'video_id', name='uq_channel_video_id'),
	)

class MiniBlog(db.Model):
	__tablename__ = 'mini_blog'

	id = db.Column(db.Integer, primary_key=True)
	title = db.Column(db.String(255), nullable=False)
	markdown_file = db.Column(db.String(255), nullable=False)
	author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
	created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
	updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
	