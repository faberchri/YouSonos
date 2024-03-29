from __future__ import annotations

from . import *

logger = logging.getLogger(PlayerLoggerName.EVENT_CONSUMER.value)


class EventConsumer(StoppableThread):

	def __init__(self, args: Namespace, queue_name: str):
		super(EventConsumer, self).__init__()
		self._queue_name = queue_name
		self.redis = redis.from_url(args.redis_url, decode_responses=True)
		self.redis_pubsub = self.redis.pubsub(ignore_subscribe_messages=True)
		self.redis_pubsub.subscribe(self._queue_name)

	def run(self):
		try:
			for message in self.redis_pubsub.listen():
				try:
					stopped = self.handle_message(message)
					if stopped:
						break
				except Exception as e:
					logger.exception('Exception in main loop of %s when handling message: %s', type(self).__name__, message)
		finally:
			self.redis_pubsub.unsubscribe()
			self.redis_pubsub.punsubscribe()
			self.redis_pubsub.close()

	def handle_message(self, message) -> bool:
		logger.debug('%s received message: %s', type(self).__name__, message)
		message_dict = json.loads(message['data'])
		event = ReceiveEvent(message_dict[General.EVENT_NAME])
		if event == ReceiveEvent.STOP:
			return True
		payload = message_dict[General.EVENT_PAYLOAD]
		sid = message_dict[General.SID]
		logger.info('%s received event \'%s\' from \'%s\' with payload: %s', type(self).__name__, event.value, sid, payload)
		self.run_event(event, sid, payload)
		return False

	def stop(self) -> None:
		self.redis.publish(self._queue_name, json.dumps({General.EVENT_NAME: ReceiveEvent.STOP.value,
													General.EVENT_PAYLOAD: {},
													General.SID: None}))

	@abstractmethod
	def run_event(self, event: ReceiveEvent, sid: str, payload: Any) -> None: raise NotImplementedError


class PlayerEventsConsumer(EventConsumer):

	def __init__(self, args: Namespace, sonos_environment: SonosEnvironment, player: Player, track_factory: TrackFactory, playlist: Playlist):
		super().__init__(args, General.QUEUE_CHANNEL_NAME_PLAYER_COMMANDS)
		self._sonos_environment = sonos_environment
		self._player = player
		self._track_factory = track_factory
		self._playlist = playlist

	def run_event(self, event: ReceiveEvent, sid: str, payload: Any):
		if event == ReceiveEvent.TOGGLE_PLAY_PAUSE:
			self._player.toggle_play_pause()
		if event == ReceiveEvent.SET_VOLUME:
			device_name = payload['device_name']
			volume = payload['volume']
			self._sonos_environment.set_sonos_volume(device_name, volume, sid)
		if event == ReceiveEvent.PLAY_TRACK:
			track = self._track_factory.create_youtube_track(payload[URL])
			self._player.play(track)
		if event == ReceiveEvent.ADD_TRACK_TO_PLAYLIST:
			url = payload[URL]
			self._playlist.add_track_at_end(url)
		if event == ReceiveEvent.DELETE_TRACK_FROM_PLAYLIST:
			playlist_entry_id = payload[ID]
			self._playlist.delete_track(playlist_entry_id)
		if event == ReceiveEvent.CHANGE_PLAYLIST_TRACK_POSITION:
			playlist_entry_id = payload[ID]
			target_position = payload['playlist_target_position']
			self._playlist.change_track_position(playlist_entry_id, target_position)
		if event == ReceiveEvent.PLAY_TRACK_OF_PLAYLIST:
			playlist_entry_id = payload[ID]
			self._playlist.play_track_of_playlist(playlist_entry_id)
		if event == ReceiveEvent.NEXT_TRACK:
			self._playlist.play_next()
		if event == ReceiveEvent.PREVIOUS_TRACK:
			self._playlist.play_previous()
		if event == ReceiveEvent.SEEK_TO:
			new_player_time = self._player.seek_to(payload['player_time'])
			emit(SendEvent.PLAYER_TIME_UPDATE_ACTIVATION, new_player_time, sid=sid)


class SearchEventConsumer(EventConsumer):

	def __init__(self, args: Namespace, search_service: SearchService):
		super().__init__(args, General.QUEUE_CHANNEL_NAME_SEARCH)
		self._search_service = search_service

	def run_event(self, event: ReceiveEvent, sid: str, payload: Any):
		if event == ReceiveEvent.SEARCH_TRACKS:
			self._search_service.run_search(payload['search_term'], payload['batch_index'],
											payload['search_result_indices'], sid)
		if event == ReceiveEvent.CANCEL_SEARCH:
			self._search_service.cancel_search(sid)
