from . import home_bp
from app import db, get_current_language, render_localized_template
from app.models.models import YoutubeChannelCache, YoutubeVideo
import requests
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError


CHANNEL_URL = 'https://www.youtube.com/@astronautmarkusdev'
YOUTUBE_TIMEOUT_SECONDS = 10
MAX_VIDEOS = 8
CACHE_TTL_MINUTES = 15

NAMESPACES = {
    'atom': 'http://www.w3.org/2005/Atom',
    'media': 'http://search.yahoo.com/mrss/',
    'yt': 'http://www.youtube.com/xml/schemas/2015',
}


def _extract_channel_id(channel_url):
    response = requests.get(
        channel_url,
        timeout=YOUTUBE_TIMEOUT_SECONDS,
        headers={'User-Agent': 'Mozilla/5.0'},
    )
    response.raise_for_status()

    page_content = response.text
    rss_match = re.search(
        r'https://www\.youtube\.com/feeds/videos\.xml\?channel_id=([A-Za-z0-9_-]+)',
        page_content,
    )
    if rss_match:
        return rss_match.group(1)

    channel_match = re.search(r'"channelId":"(UC[\w-]{20,})"', page_content)
    if channel_match:
        return channel_match.group(1)

    raise ValueError('Unable to resolve channel ID from the provided YouTube URL.')


def _format_published_date(raw_published):
    if not raw_published:
        return ''

    try:
        published_at = datetime.fromisoformat(raw_published.replace('Z', '+00:00'))
        return published_at.strftime('%Y-%m-%d')
    except ValueError:
        return raw_published


def _fetch_latest_videos(channel_url, limit=MAX_VIDEOS):
    channel_id = _extract_channel_id(channel_url)
    feed_url = f'https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}'

    response = requests.get(
        feed_url,
        timeout=YOUTUBE_TIMEOUT_SECONDS,
        headers={'User-Agent': 'Mozilla/5.0'},
    )
    response.raise_for_status()

    root = ET.fromstring(response.content)
    entries = root.findall('atom:entry', NAMESPACES)

    videos = []
    for entry in entries[:limit]:
        video_id = entry.findtext('yt:videoId', default='', namespaces=NAMESPACES)
        title = entry.findtext('atom:title', default='Untitled video', namespaces=NAMESPACES)
        published_raw = entry.findtext('atom:published', default='', namespaces=NAMESPACES)

        thumbnail_node = entry.find('media:group/media:thumbnail', NAMESPACES)
        thumbnail_url = thumbnail_node.get('url') if thumbnail_node is not None else ''

        videos.append(
            {
                'video_id': video_id,
                'title': title,
                'published': _format_published_date(published_raw),
                'url': f'https://www.youtube.com/watch?v={video_id}' if video_id else '',
                'thumbnail': thumbnail_url,
            }
        )

    return videos


def _get_cached_channel_state(channel_url):
    return YoutubeChannelCache.query.filter_by(channel_url=channel_url).first()


def _get_cached_videos(channel_url):
    rows = (
        YoutubeVideo.query.filter_by(channel_url=channel_url)
        .order_by(YoutubeVideo.published.desc(), YoutubeVideo.id.desc())
        .all()
    )

    return [
        {
            'video_id': row.video_id,
            'title': row.title,
            'published': row.published or '',
            'url': row.video_url,
            'thumbnail': row.thumbnail_url or '',
        }
        for row in rows
    ]


def _load_cache_snapshot(channel_url):
    try:
        return _get_cached_channel_state(channel_url), _get_cached_videos(channel_url)
    except SQLAlchemyError:
        db.session.rollback()
        return None, []


def _save_videos_in_cache(channel_url, videos):
    synced_at = datetime.utcnow()

    YoutubeVideo.query.filter_by(channel_url=channel_url).delete(synchronize_session=False)

    for video in videos:
        db.session.add(
            YoutubeVideo(
                channel_url=channel_url,
                video_id=video.get('video_id', ''),
                title=video.get('title', 'Untitled video'),
                published=video.get('published', ''),
                video_url=video.get('url', ''),
                thumbnail_url=video.get('thumbnail', ''),
            )
        )

    state = _get_cached_channel_state(channel_url)
    if state is None:
        state = YoutubeChannelCache(channel_url=channel_url, last_synced_at=synced_at)
        db.session.add(state)
    else:
        state.last_synced_at = synced_at

    db.session.commit()


def _is_cache_fresh(last_synced_at):
    if not last_synced_at:
        return False

    return datetime.utcnow() - last_synced_at < timedelta(minutes=CACHE_TTL_MINUTES)



@home_bp.route('/youtube-channel')
def youtube_channel():
    cached_state, cached_videos = _load_cache_snapshot(CHANNEL_URL)

    videos = cached_videos
    fetch_error = None
    lang = get_current_language()

    if not _is_cache_fresh(cached_state.last_synced_at if cached_state else None):
        try:
            fresh_videos = _fetch_latest_videos(CHANNEL_URL)
            videos = fresh_videos
            try:
                _save_videos_in_cache(CHANNEL_URL, fresh_videos)
            except SQLAlchemyError:
                db.session.rollback()
        except (requests.RequestException, ET.ParseError, ValueError):
            db.session.rollback()

    if not videos:
        if lang == 'es':
            fetch_error = 'No pude cargar los últimos videos en este momento. Intenta de nuevo en unos minutos.'
        else:
            fetch_error = 'Unable to load latest videos right now. Please try again in a few minutes.'

    return render_localized_template(
        'youtube_channel.html',
        channel_url=CHANNEL_URL,
        videos=videos,
        fetch_error=fetch_error,
    )