import logging
import os

import redis
from argparse import Namespace
from flask import Flask, send_from_directory, render_template
from flask_socketio import SocketIO

from Constants import General, ServerLoggerName

REACT_APP_LOCATION = 'client/build'
PARENT_REACT_APP_LOCATION = '../' + REACT_APP_LOCATION

socketio = SocketIO(logger=logging.getLogger(ServerLoggerName.SOCKETIO.value),
					engineio_logger=logging.getLogger(ServerLoggerName.ENGINEIO.value),
					cors_allowed_origins='*')

redis_db = None


def create_app(args: Namespace):
	global redis_db
	redis_db = redis.from_url(args.redis_url, decode_responses=True)

	app = Flask(__name__, static_folder=PARENT_REACT_APP_LOCATION, template_folder=PARENT_REACT_APP_LOCATION)

	# Serve React App
	@app.route('/', defaults={'path': ''})
	@app.route('/<path:path>')
	def serve(path):
		if path != '' and os.path.exists(os.path.join(REACT_APP_LOCATION, path)):
			return send_from_directory(PARENT_REACT_APP_LOCATION, path)
		else:
			return render_template('index.html')

	from . import events
	socketio.init_app(app, message_queue=args.redis_url)
	return app
