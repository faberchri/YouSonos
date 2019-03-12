from enum import Enum, unique


def create_logger_name(*name_parts):
	return '.'.join(name_parts)


class General:
	APP_NAME = 'you_sonos'
	REDIS_URL = 'redis://'
	QUEUE_CHANNEL_NAME_PLAYER_COMMANDS = APP_NAME + '_player_commands'
	QUEUE_CHANNEL_NAME_SEARCH = APP_NAME + '_search'

	EVENT_NAME = 'event_name'
	EVENT_PAYLOAD = 'payload'
	SID = 'sid'
	RECEIVED_EVENT = 'received_event'

	SERVER_LOGGER_NAME_PREFIX = create_logger_name(APP_NAME, 'server')
	PLAYER_LOGGER_NAME_PREFIX = create_logger_name(APP_NAME, 'player')
	MAIN_LOGGER_NAME_POSTFIX = 'main'
	SOCKETIO_LOGGER_NAME_POSTFIX = 'socketio'
	ENGINEIO_LOGGER_NAME_POSTFIX = 'engineio'
	EVENTLET_LOGGER_NAME_POSTFIX = 'eventlet'


@unique
class Source(Enum):
	YOUTUBE = 'youtube'

@unique
class SendEvent(Enum):
	PLAYER_STATE_CHANGE_STARTED = 'player_state_change_started'
	SONOS_SETUP = 'sonos_setup'
	VOLUME_CHANGED = 'volume_changed'
	PLAYLIST_CHANGED = 'playlist_changed'
	SEARCH_RESULTS = 'search_results'
	CURRENT_TRACK = 'current_track'
	NEW_TRACK_PLAYING = 'new_track_playing'
	PLAYER_STATE = 'player_state'
	PLAYER_TIME = 'player_time'
	PLAYER_TIME_UPDATE_ACTIVATION = 'player_time_update_activation'


@unique
class ReceiveEvent(Enum):
	CONNECT = 'connect'
	TOGGLE_PLAY_PAUSE = 'toggle_play_pause'
	SET_VOLUME = 'set_volume'
	SEARCH_TRACKS = 'search_tracks'
	CANCEL_SEARCH = 'cancel_search'
	ADD_TRACK_TO_PLAYLIST = 'add_track_to_playlist'
	DELETE_TRACK_FROM_PLAYLIST = 'delete_track_from_playlist'
	CHANGE_PLAYLIST_TRACK_POSITION = 'change_playlist_track_position'
	PLAY_TRACK_OF_PLAYLIST = 'play_track_of_playlist'
	PLAY_TRACK = 'play_track'
	PREVIOUS_TRACK = 'previous_track'
	NEXT_TRACK = 'next_track'
	SEEK_TO = 'seek_to'


@unique
class DbKey(Enum):
	SONOS_SETUP = 'sonos_setup'
	CURRENT_TRACK = 'current_track'
	PLAYER_STATE = 'player_state'
	PLAYLIST = 'playlist'


@unique
class ServerLoggerName(Enum):
	MAIN = create_logger_name(General.SERVER_LOGGER_NAME_PREFIX, General.MAIN_LOGGER_NAME_POSTFIX)
	SOCKETIO = create_logger_name(General.SERVER_LOGGER_NAME_PREFIX, General.SOCKETIO_LOGGER_NAME_POSTFIX)
	ENGINEIO = create_logger_name(General.SERVER_LOGGER_NAME_PREFIX, General.ENGINEIO_LOGGER_NAME_POSTFIX)
	EVENTLET = create_logger_name(General.SERVER_LOGGER_NAME_PREFIX, General.EVENTLET_LOGGER_NAME_POSTFIX)
	EVENTS = create_logger_name(General.SERVER_LOGGER_NAME_PREFIX, 'events')


@unique
class PlayerLoggerName(Enum):
	MAIN = create_logger_name(General.PLAYER_LOGGER_NAME_PREFIX, General.MAIN_LOGGER_NAME_POSTFIX)
	SOCKETIO = create_logger_name(General.PLAYER_LOGGER_NAME_PREFIX, General.SOCKETIO_LOGGER_NAME_POSTFIX)
	ENGINEIO = create_logger_name(General.PLAYER_LOGGER_NAME_PREFIX, General.ENGINEIO_LOGGER_NAME_POSTFIX)
	EVENTLET = create_logger_name(General.PLAYER_LOGGER_NAME_PREFIX, General.EVENTLET_LOGGER_NAME_POSTFIX)
	UTIL = create_logger_name(General.PLAYER_LOGGER_NAME_PREFIX, 'util')
	PLAYER = create_logger_name(General.PLAYER_LOGGER_NAME_PREFIX, 'player')
	EVENT_CONSUMER = create_logger_name(General.PLAYER_LOGGER_NAME_PREFIX, 'event_consumer')
	PLAYLIST_ENTRY = create_logger_name(General.PLAYER_LOGGER_NAME_PREFIX, 'playlist_entry')
	SONOS_ENVIRONMENT = create_logger_name(General.PLAYER_LOGGER_NAME_PREFIX, 'sonos_environment')
	TRACK = create_logger_name(General.PLAYER_LOGGER_NAME_PREFIX, 'track')
	SEARCH_SERVICE = create_logger_name(General.PLAYER_LOGGER_NAME_PREFIX, 'search_service')
