import logging
import os

import redis
from flask import Flask, send_from_directory, render_template
from flask_socketio import SocketIO

from Constants import General, ServerLoggerName

REACT_APP_LOCATION = 'client/build'
PARENT_REACT_APP_LOCATION = '../' + REACT_APP_LOCATION

socketio = SocketIO(logger=logging.getLogger(ServerLoggerName.SOCKETIO.value),
					engineio_logger=logging.getLogger(ServerLoggerName.ENGINEIO.value))

redis_db = redis.Redis(decode_responses=True)


def create_app():
	app = Flask(__name__, static_folder=PARENT_REACT_APP_LOCATION, template_folder=PARENT_REACT_APP_LOCATION)

	# Serve React App
	@app.route('/', defaults={'path': ''})
	@app.route('/<path:path>')
	def serve(path):
		#FIXME: what happens when accessing .../index.html directly?
		if path != '' and os.path.exists(os.path.join(REACT_APP_LOCATION, path)):
			return send_from_directory(PARENT_REACT_APP_LOCATION, path)
		else:
			return render_template('index.html')

	from . import events
	socketio.init_app(app, message_queue=General.REDIS_URL)
	return app
