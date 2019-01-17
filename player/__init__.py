import json
import logging
import socket
from typing import Any

import redis
from flask_socketio import SocketIO

from Constants import General, DbKey, SendEvent, ReceiveEvent, PlayerLoggerName

_db = redis.Redis()
_socket = SocketIO(message_queue=General.REDIS_URL,
				   logger=logging.getLogger(PlayerLoggerName.SOCKETIO.value),
				   engineio_logger=logging.getLogger(PlayerLoggerName.ENGINEIO.value),
				   # FIXME probably meaningless arg
				   log=logging.getLogger(PlayerLoggerName.EVENTLET.value))

logger = logging.getLogger(PlayerLoggerName.UTIL.value)

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


def get_own_ip() -> str:

	hostname = socket.gethostname()

	# workaround to fix 'wrong IP if iPhone is connected in dev mode to computer (via USB)'
	# socket.gethostbyname(hostname) returns the IP of the network interface 'iPhone USB (en3)' (e.g.: 169.254.51.36)
	# instead of the IP of the Wi-Fi or ethernet network interface (e.g.: 192.168.0.45)
	host_by_name_ex = socket.gethostbyname_ex(hostname)
	logger.debug('socket.gethostbyname_ex(%s): %s', hostname, host_by_name_ex)
	all_addresses = host_by_name_ex[2]
	if not all_addresses:
		raise ValueError('No network interface detected. Is computer connected to network?')

	# get the first IP starting with '192' or else just the first in the list
	own_ip = next((address for address in all_addresses if address.startswith('192')), all_addresses[0])
	logger.debug('Own IP resolved: %s (hostname: %s)', own_ip, hostname)

	return own_ip
