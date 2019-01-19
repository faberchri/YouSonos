#!/usr/bin/env python3

import argparse
import multiprocessing as mp
from argparse import Namespace
from typing import NoReturn

from Constants import ServerLoggerName, PlayerLoggerName


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
	parser = argparse.ArgumentParser(description='Play YouTube tracks on Sonos loud speakers.')
	parser.add_argument('--verbose', '-v', action='count',  default=0, help='Change the level of verbosity. '
																			'Info: -v, Debug: -vv, Warn: default')
	parser.add_argument('--host', '-i', action='store', help='The hostname or IP address for the server to listen on. '
													   'Is set to flask-SocketIO default value if not specified.')
	parser.add_argument('--port', '-p', action='store', help='The port number for the server to listen on. '
													   'Is set to flask-SocketIO default value if not specified.')
	return parser.parse_args()


def player_main(parsed_args: Namespace) -> None:
	logging= init_logging(parsed_args)
	main_logger = logging.getLogger(PlayerLoggerName.MAIN.value)
	main_logger.info('Starting youSonos player ...')
	from player import SonosEnvironment, Player, Track, Playlist, EventConsumer
	sonos_environment = SonosEnvironment.SonosEnvironment()
	player = Player.Player(sonos_environment, parsed_args.verbose)
	track_factory = Track.TrackFactory(player)
	playlist = Playlist.Playlist(track_factory)
	player.add_terminal_observer(playlist)
	EventConsumer.PlayerEventsConsumer(sonos_environment, player, track_factory, playlist).start()
	EventConsumer.SearchEventConsumer(track_factory).start()
	playlist.read_playlist_from_db()
	main_logger.info('youSonos player successfully started.')


def server_main(parsed_args: Namespace) -> NoReturn:
	logging = init_logging(parsed_args)
	main_logger = logging.getLogger(ServerLoggerName.MAIN.value)
	main_logger.info('Starting youSonos server ...')
	import eventlet
	eventlet.monkey_patch()
	from server import create_app
	from server import socketio
	app = create_app()
	socketio.run(app, host=parsed_args.host, port=parsed_args.port, log_output=True, log=logging.getLogger(ServerLoggerName.EVENTLET.value))


if __name__ == '__main__':
	mp.set_start_method('spawn')
	parsed_args = parse_args()
	player_main(parsed_args)
	mp.Process(target=server_main, args=(parsed_args,)).start()

