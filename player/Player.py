from __future__ import annotations

import time

from . import *
from vlc import MediaPlayer, Instance, EventType

logger = logging.getLogger(PlayerLoggerName.PLAYER.value)

@unique
class PlayerStatus(Enum):
	PLAYING = 'PLAYING'
	PAUSED = 'PAUSED'
	STOPPED = 'STOPPED'


class PlayerObserver(ABC):

	@abstractmethod
	def player_status_changed(self, previous_status: PlayerStatus, new_status: PlayerStatus, current_track: Track) -> None:
		pass

NETWORK_CACHING_DURATION_IN_SECONDS = 2

class Player:

	def __init__(self, args: Namespace, stream_consumer: StreamConsumer):
		self._observers: Set[PlayerObserver] = set()
		self._terminal_observers: Set[PlayerObserver] = set()
		self._stream_consumer = stream_consumer
		vlc_args = ["--network-caching=" + str(NETWORK_CACHING_DURATION_IN_SECONDS * 1000)]
		if args.verbose > 0:
			vlc_args.append('-' + 'v' * args.verbose)
		logger.debug('Init new VLC player with args %s ...', str(vlc_args))
		self._vlc_instance: Instance = Instance(vlc_args)
		self._vlc_player: MediaPlayer = self._vlc_instance.media_player_new()
		logger.info('VLC player created. Player: %s', self._vlc_player)
		from .Track import NullTrack, TrackStatus
		self._null_track = NullTrack(args, self, TrackStatus.STOPPED)
		self._set_track(self._null_track)
		self._player_state = PlayerStatus.STOPPED
		self._update_player_state(PlayerStatus.STOPPED)
		self._init_track_end_callback()
		self._init_player_time_callback()

	def get_null_track(self) -> Track:
		return self._null_track

	def add_observer(self, observer: PlayerObserver) -> None:
		self._observers.add(observer)

	def add_terminal_observer(self, terminal_observer: PlayerObserver):
		self._terminal_observers.add(terminal_observer)

	def remove_observer(self, observer: PlayerObserver) -> None:
		if observer in self._observers:
			self._observers.remove(observer)
		if observer in self._terminal_observers:
			self._terminal_observers.remove(observer)

	def play(self, track: Track) -> None:
		logger.debug('Next playing: %s', self._track)
		self._set_track(track)
		self._init_stream()
		self._play()
		logger.info('Started playing: %s', self._track)

	def toggle_play_pause(self) -> None:
		if self._player_state is PlayerStatus.STOPPED:
			raise ValueError('Toggling of play / pause is not allowed if player is stopped.')
		if self._player_state is PlayerStatus.PLAYING:
			self._pause()
			logger.info('Paused playing: %s', self._track)
			return
		if self._player_state is PlayerStatus.PAUSED:
			self._play()
			logger.info('Continue playing: %s', self._track)
			return

	def stop(self) -> None:
		self._set_track(self._null_track)
		self._vlc_player.stop()
		self._update_player_state(PlayerStatus.STOPPED)

	def seek_to(self, player_time: int) -> int:
		limited_player_time = player_time
		if player_time < 0:
			limited_player_time = 0
		if self._track.get_duration() < player_time:
			limited_player_time = self._track.get_duration()
		logger.info('Set player time to: %d / %d', player_time, self._track.get_duration())
		self._vlc_player.set_time(limited_player_time)
		self._init_stream_consumer()
		return self._vlc_player.get_time()

	def _set_track(self, track: Track) -> None:
		self._track = track
		self._observers.add(track)

	def _play(self) -> None:
		r = self._vlc_player.play()
		logger.debug('VLC playing started. vlc_player.play() result code: %s', r)
		self._init_stream_consumer()
		self._update_player_state(PlayerStatus.PLAYING)

	def _init_stream_consumer(self):
		self._stream_consumer.play_stream(self._track)

	def _pause(self) -> None:
		r = self._vlc_player.pause()
		logger.debug('vlc_player.pause() result code: %s', r)
		self._update_player_state(PlayerStatus.PAUSED)

	def _init_stream(self) -> None:
		vlc_media = self._track.create_vlc_media(self._vlc_instance)
		mrl = vlc_media.get_mrl()
		logger.debug('VLC media %s, VLC mrl: %s', vlc_media, mrl)
		r = self._vlc_player.stop()
		logger.debug('VLC player stopped. vlc_player.stop() result code: %s', r)
		r = self._vlc_player.set_media(vlc_media)
		logger.debug('VLC player media set. vlc_player.set_media(...) result code: %s', r)

	def _init_track_end_callback(self) -> None:
		event_manager = self._vlc_player.event_manager()
		event_manager.event_attach(EventType.MediaPlayerEndReached, self._get_track_end_callback())

	def _init_player_time_callback(self) -> None:
		event_manager = self._vlc_player.event_manager()
		def callback(event):
			emit(SendEvent.PLAYER_TIME, event.u.new_time)
		event_manager.event_attach(EventType.MediaPlayerTimeChanged, callback)

	def _get_track_end_callback(self) -> Callable[[Any], None]:
		def callback(event):
			time.sleep(NETWORK_CACHING_DURATION_IN_SECONDS)
			self._set_track(self._null_track)
			self._update_player_state(PlayerStatus.STOPPED)
			publish_on_player_command_channel(ReceiveEvent.NEXT_TRACK, {})
		return callback

	def _update_player_state(self, player_state: PlayerStatus) -> None:
		self._update_observers(player_state)
		self._player_state = player_state
		player_state_dict = {'player_state': player_state.value}
		save_and_emit(DbKey.PLAYER_STATE, SendEvent.PLAYER_STATE, player_state_dict)

	def _update_observers(self, player_state: PlayerStatus) -> None:
		# first copy set of observers so that observers can register / unregister when called
		current_observers = list(self._observers)
		current_observers.extend(self._terminal_observers)
		for observer in current_observers:
			observer.player_status_changed(self._player_state, player_state, self._track)
