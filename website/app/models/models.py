from .. import db
from datetime import datetime


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
