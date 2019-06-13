#!/usr/bin/env python3

import argparse
import multiprocessing as mp
import time
import urllib.request
from argparse import Namespace
from typing import NoReturn

import redis
from redis.exceptions import ConnectionError

from Constants import General, ServerLoggerName, PlayerLoggerName


def init_logging(parsed_args: Namespace):
	import logging
	log_level = logging.WARN
	if parsed_args.verbose > 0:
		log_level = logging.INFO
	if parsed_args.verbose > 1:
		log_level = logging.DEBUG
	logging.basicConfig(level=log_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

	# prevent spamming of log on info level from engineio and socketio
	if log_level == logging.INFO:
		[logger.setLevel(logging.WARN) for logger in [logging.getLogger(ServerLoggerName.ENGINEIO.value),
													  logging.getLogger(ServerLoggerName.SOCKETIO.value),
													  logging.getLogger(PlayerLoggerName.SOCKETIO.value),
													  logging.getLogger('soco')]]
	return logging


def parse_args() -> Namespace:
	out_stream_url = '--out-stream-url'
	vlc_command = '--vlc-command'
	parser = argparse.ArgumentParser(prog='YouSonos', description='Play YouTube tracks on Sonos loud speakers.',
									 formatter_class=argparse.RawTextHelpFormatter)
	parser.add_argument('--verbose', '-v', action='count',  default=0, help='Change the level of verbosity.\n'
																			'Info: -v, Debug: -vv, Warn: default')
	parser.add_argument('--host', '-i', action='store', default=General.HOST_DEFAULT_URL, help='The hostname or IP address '
														'for the server to listen on.\n'
														'Defaults to:\n\t' + General.HOST_DEFAULT_URL
														+ ' (flask-SocketIO default value)')
	parser.add_argument('--port', '-p', action='store', default=General.HOST_DEFAULT_PORT, help='The port number for the '
														'server to listen on.\n'
														'Defaults to:\n\t' + str(General.HOST_DEFAULT_PORT) +
														' (flask-SocketIO default value)')
	parser.add_argument('--youtube-api-key', '-k', action='store', help='The YouTube API key. If not specified or invalid '
																	  'the keyword search is disabled and only YouTube '
																	  'URLs and YouTube video IDs are valid search input.')
	parser.add_argument(out_stream_url, action='store', help='URL of stream sent from YouSonos host to Sonos speakers.\n'
															'Defaults to:\n\t'
																 'http://<IP-of-this-host>:' + str(General.VLC_OUT_STREAM_DEFAULT_PORT)
																 + '/' + General.OUT_STREAM_NAME +
															'\nSee also option \'' + vlc_command + '\'.')
	parser.add_argument(vlc_command, action='store', default=General.VLC_TRANSCODE_CMD, help='VLC player command to '
														'transcode the incoming (YouTube) stream to the outgoing stream,'
														' which can be picked up by the Sonos speakers.\nDefaults to:\n\t'
														+ General.VLC_TRANSCODE_CMD +
														'\nSee also option \'' + out_stream_url + '\'.')
	parser.add_argument('--redis_url', action='store', default=General.REDIS_URL, help='URL of the redis instance.\n'
															'Defaults to:\n\t' + General.REDIS_URL)
	return parser.parse_args()


def wait_for_redis(logger) -> None:
	MAX_REDIS_WAIT_TIME = 30
	i = 0
	db = redis.Redis()
	while True:
		try:
			if db.ping():
				logger.info('Connection to redis server established.')
				break
		except ConnectionError:
			if i > MAX_REDIS_WAIT_TIME:
				logger.error('Connecting to redis server failed ({}/{}).'.format(i, MAX_REDIS_WAIT_TIME))
				raise
		logger.warning('Waiting for redis server ... ({}/{})'.format(i, MAX_REDIS_WAIT_TIME))
		time.sleep(1)
		i = i + 1


def player_main(parsed_args: Namespace) -> None:
	logging= init_logging(parsed_args)
	main_logger = logging.getLogger(PlayerLoggerName.MAIN.value)
	main_logger.info('Starting youSonos player ...')
	wait_for_redis(main_logger)
	from player import initialize
	initialize(parsed_args)
	main_logger.info('youSonos player successfully started.')


def server_main(parsed_args: Namespace) -> NoReturn:
	logging = init_logging(parsed_args)
	main_logger = logging.getLogger(ServerLoggerName.MAIN.value)
	main_logger.info('Starting youSonos server ...')
	import eventlet
	eventlet.monkey_patch()
	wait_for_redis(main_logger)
	from server import create_app
	from server import socketio
	app = create_app(parsed_args)
	socketio.run(app, host=parsed_args.host, port=parsed_args.port, log_output=True, log=logging.getLogger(ServerLoggerName.EVENTLET.value))


def wait_for_server(parsed_args) -> None:
	url_with_port = "http://{}:{}".format(parsed_args.host, parsed_args.port)
	while True:
		time.sleep(1)
		try:
			urllib.request.urlopen(url_with_port)
			print("YouSonos started at: " + url_with_port)
			break
		except urllib.error.URLError:
			pass


if __name__ == '__main__':
	mp.set_start_method('spawn')
	parsed_args = parse_args()
	player_main(parsed_args)
	mp.Process(target=server_main, args=(parsed_args,)).start()
	wait_for_server(parsed_args)

