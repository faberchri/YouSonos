import json
import logging

import flask
from flask_socketio import emit

from Constants import ReceiveEvent, SendEvent, General, DbKey, ServerLoggerName
from server import socketio, redis_db

logger = logging.getLogger(ServerLoggerName.EVENTS.value)

@socketio.on(ReceiveEvent.CONNECT.value)
def on_connect():
	_read_from_redis_and_emit(DbKey.SONOS_SETUP, SendEvent.SONOS_SETUP)
	_read_from_redis_and_emit(DbKey.CURRENT_TRACK, SendEvent.CURRENT_TRACK)
	_read_from_redis_and_emit(DbKey.PLAYER_STATE, SendEvent.PLAYER_STATE)
	_read_from_redis_and_emit(DbKey.PLAYLIST, SendEvent.PLAYLIST_CHANGED)


def _read_from_redis_and_emit(db_key: DbKey, event: SendEvent):
	redis_value = redis_db.get(db_key.value)
	redis_value = json.loads(redis_value)
	logger.debug("For key %s value read from redis is %s", db_key.value, redis_value)
	emit(event.value, redis_value)


@socketio.on(ReceiveEvent.SET_VOLUME.value)
def set_volume(data) -> None:
	publish_on_player_command_channel(ReceiveEvent.SET_VOLUME, data)
	emit_player_state_change(ReceiveEvent.SET_VOLUME)


@socketio.on(ReceiveEvent.TOGGLE_PLAY_PAUSE.value)
def toggle_play_pause(data) -> None:
	publish_on_player_command_channel(ReceiveEvent.TOGGLE_PLAY_PAUSE, '{}')
	emit_player_state_change(ReceiveEvent.TOGGLE_PLAY_PAUSE)


@socketio.on(ReceiveEvent.NEXT_TRACK.value)
def play_next_track(data) -> None:
	publish_on_player_command_channel(ReceiveEvent.NEXT_TRACK, '{}')


@socketio.on(ReceiveEvent.PREVIOUS_TRACK.value)
def play_previous_track(data) -> None:
	publish_on_player_command_channel(ReceiveEvent.PREVIOUS_TRACK, '{}')


@socketio.on(ReceiveEvent.SEARCH_TRACKS.value)
def search_tracks(youtube_url) -> None:
	publish_on_search_channel(ReceiveEvent.SEARCH_TRACKS, youtube_url)


@socketio.on(ReceiveEvent.CANCEL_SEARCH.value)
def cancel_search(data) -> None:
	publish_on_search_channel(ReceiveEvent.CANCEL_SEARCH, '{}')


@socketio.on(ReceiveEvent.PLAY_TRACK.value)
def play_track(youtube_url) -> None:
	publish_on_player_command_channel(ReceiveEvent.PLAY_TRACK, youtube_url)


@socketio.on(ReceiveEvent.ADD_TRACK_TO_PLAYLIST.value)
def add_track_to_playlist(data) -> None:
	publish_on_player_command_channel(ReceiveEvent.ADD_TRACK_TO_PLAYLIST, data)


@socketio.on(ReceiveEvent.DELETE_TRACK_FROM_PLAYLIST.value)
def delete_track_from_playlist(data) -> None:
	publish_on_player_command_channel(ReceiveEvent.DELETE_TRACK_FROM_PLAYLIST, data)


@socketio.on(ReceiveEvent.CHANGE_PLAYLIST_TRACK_POSITION.value)
def change_playlist_track_position(data) -> None:
	publish_on_player_command_channel(ReceiveEvent.CHANGE_PLAYLIST_TRACK_POSITION, data)


@socketio.on(ReceiveEvent.PLAY_TRACK_OF_PLAYLIST.value)
def play_track_of_playlist(data) -> None:
	publish_on_player_command_channel(ReceiveEvent.PLAY_TRACK_OF_PLAYLIST, data)


@socketio.on(ReceiveEvent.SEEK_TO.value)
def seek_to(data) -> None:
	publish_on_player_command_channel(ReceiveEvent.SEEK_TO, data)


def publish_on_player_command_channel(event: ReceiveEvent, data):
	publish_on_redis(General.QUEUE_CHANNEL_NAME_PLAYER_COMMANDS, event, data)


def publish_on_search_channel(event: ReceiveEvent, data):
	publish_on_redis(General.QUEUE_CHANNEL_NAME_SEARCH, event, data)


def publish_on_redis(channel_name: str, event: ReceiveEvent, data):
	sid = flask.request.sid
	logger.debug("Publishing event '%s' on redis channel '%s'. payload %s (sid: %s)", event.value, channel_name, data, sid)
	redis_db.publish(channel_name,
					 json.dumps({General.EVENT_NAME: event.value,
								General.EVENT_PAYLOAD: json.loads(data),
								General.SID: sid}))


def emit_player_state_change(event_received: ReceiveEvent):
	socketio.emit(SendEvent.PLAYER_STATE_CHANGE_STARTED.value, {General.RECEIVED_EVENT: event_received.value})
