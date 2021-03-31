from __future__ import annotations

import json
import logging
import socket
import redis

from abc import ABC, abstractmethod
from argparse import Namespace
from flask_socketio import SocketIO
from threading import Thread, Event
from typing import Any, Dict, Callable, Iterable, Iterator, List, Set, ValuesView, TypeVar, Union

from Constants import *
from Util import StoppableThread

_db = None
_socket = None

logger = logging.getLogger(PlayerLoggerName.UTIL.value)


IntOrStr = Union[int, str]
PropDict = Dict[str, IntOrStr]


def save_in_db(key: DbKey, payload):
	logger.debug("Save to db. key: '%s' | value: %s", key.value, payload)
	_db.set(key.value, json.dumps(payload))


def read_list_from_db(key: DbKey) -> Any:
	value = _db.get(key.value)
	if value:
		return json.loads(value)
	return []


def emit(event: SendEvent, dict, sid=None, skip_sid=None):
	logger.debug("Emit event: '%s' | sid: '%s' | skip_sid: '%s' | payload: %s", event.value, sid, skip_sid, dict)
	_socket.emit(event.value, dict, room=sid, skip_sid=skip_sid)


def save_and_emit(key: DbKey, event: SendEvent, payload, sid=None, skip_sid=None):
	save_in_db(key, payload)
	emit(event, payload, sid=sid, skip_sid=skip_sid)


def publish_on_player_command_channel(event: ReceiveEvent, data):
	logger.debug("Publishing internal event '%s' on redis. payload %s", event.value, data)
	_db.publish(General.QUEUE_CHANNEL_NAME_PLAYER_COMMANDS,
				json.dumps({General.EVENT_NAME: event.value,
								General.EVENT_PAYLOAD: data,
								General.SID: None}))


def get_own_ip(reference_ip="8.8.8.8", reference_port=80) -> str:

	# from https://stackoverflow.com/a/166589
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	try:
		s.connect((reference_ip, reference_port))
		own_ip = s.getsockname()[0]
		logger.debug('Own IP resolved: %s (open socket: %s)', own_ip, s)
		return own_ip
	except socket.error:
		logger.error('Detection of own IP failed. Exception on attempt to open socket to %s:%d.', reference_ip, reference_port)
		raise
	finally:
		s.close()


from .SonosEnvironment import SonosEnvironment, StreamConsumer
from .Player import Player, PlayerObserver, PlayerStatus
from .Track import Track, TrackStatus, NullTrack, TrackFactory, URL
from .Playlist import Playlist
from .PlaylistEntry import PlaylistEntry, PlaylistEntryFactory, PlaylistEntryStatus, ID, STATUS
from .EventConsumer import EventConsumer, PlayerEventsConsumer, SearchEventConsumer
from .SearchService import SearchService


def initialize(args: Namespace) -> List[StoppableThread]:
	global _db
	_db = redis.from_url(args.redis_url)
	global _socket
	_socket = SocketIO(message_queue=args.redis_url,
					   logger=logging.getLogger(PlayerLoggerName.SOCKETIO.value),
					   engineio_logger=logging.getLogger(PlayerLoggerName.ENGINEIO.value),
					   # FIXME probably meaningless arg
					   log=logging.getLogger(PlayerLoggerName.EVENTLET.value))
	sonos_environment = SonosEnvironment()
	sonos_env_monitoring_thread = sonos_environment.start_sonos_environment_monitoring()
	player = Player(args, sonos_environment)
	track_factory = TrackFactory(args, player)
	playlist_entry_factory = PlaylistEntryFactory(track_factory)
	playlist = Playlist(playlist_entry_factory)
	player.add_terminal_observer(playlist)
	player_events_consumer = PlayerEventsConsumer(args, sonos_environment, player, track_factory, playlist)
	player_events_consumer.start()
	search_service = SearchService(track_factory, args.youtube_api_key, args.max_keyword_search_results)
	search_event_consumer = SearchEventConsumer(args, search_service)
	search_event_consumer.start()
	playlist.read_playlist_from_db()
	return [sonos_env_monitoring_thread, player_events_consumer, search_event_consumer]

