from __future__ import annotations

import re

from random import randint
from datetime import timedelta, datetime

import pafy
from pafy.backend_shared import BasePafy

from . import *

URL = 'url'
TYPE = 'track_type'
STATUS = 'track_status'
COVER_URL= 'cover_url'
DURATION= 'duration'

AVERAGE_TRACK_VALIDITY_IN_HOURS = 3

logger = logging.getLogger(PlayerLoggerName.TRACK.value)

@unique
class TrackType(Enum):
	YOU_TUBE = Source.YOUTUBE.value
	NULL = 'null'


@unique
class TrackStatus(Enum):
	PLAYING = 'PLAYING'
	PAUSED = 'PAUSED'
	STOPPED = 'STOPPED'


class Track(PlayerObserver):

	def __init__(self, args: Namespace, player: Player, track_status: TrackStatus):
		super().__init__()
		self._args = args
		self._player = player
		self._track_status = track_status

	@property
	def track_status(self) -> TrackStatus:
		return self._track_status

	@abstractmethod
	def get_title(self) -> str: raise NotImplementedError

	@abstractmethod
	def get_artist(self) -> str: raise NotImplementedError

	@abstractmethod
	def get_author(self) -> str: raise NotImplementedError

	@abstractmethod
	def get_url(self) -> str: raise NotImplementedError

	@abstractmethod
	def get_cover_url(self) -> str: raise NotImplementedError

	@abstractmethod
	def get_track_type(self) -> TrackType: raise NotImplementedError

	@abstractmethod
	def create_vlc_media(self, vlc_instance) -> Any: raise NotImplementedError

	def get_out_stream_url(self, reference_ip: str, reference_port=General.VLC_OUT_STREAM_DEFAULT_PORT) -> str:
		if self._args.out_stream_url:
			return self._args.out_stream_url
		own_ip = get_own_ip(reference_ip, reference_port)
		return 'http://{}:{}/{}'.format(own_ip, reference_port, General.OUT_STREAM_NAME)

	@abstractmethod
	def get_duration(self) -> int: raise NotImplementedError

	def player_status_changed(self, previous_status: PlayerStatus, new_status: PlayerStatus, current_track: Track) -> None:
		if current_track == self:
			self._track_status = TrackStatus(new_status.value)
			self._save_and_emit_current_track()
		else:
			self._player.remove_observer(self)
			self._track_status = TrackStatus.STOPPED

	def play(self) -> None:
		self._player.play(self)

	def toggle_play_pause(self) -> None:
		if self.track_status == TrackStatus.STOPPED:
			self.play()
		else:
			self._player.toggle_play_pause()

	def stop(self) -> None:
		if self.track_status != TrackStatus.STOPPED:
			self._player.stop()

	def __str__(self) -> str:
		return '\'{}\' of \'{}\' ({}) is {} (at {})'.format(self.get_title(), self.get_artist(), self.get_author(),
													   self.track_status.value, self.get_url())

	def get_property_dict(self) -> {}:
		return {'title': self.get_title(),
				'artist': self.get_artist(),
				'author': self.get_author(),
				URL: self.get_url(),
				COVER_URL: self.get_cover_url(),
				TYPE: self.get_track_type().value,
				STATUS: self._track_status.value,
				DURATION: self.get_duration()}

	def _save_and_emit_current_track(self) -> None:
		properties = self.get_property_dict()
		save_and_emit(DbKey.CURRENT_TRACK, SendEvent.CURRENT_TRACK, properties)


class YouTubeTrack(Track):

	def __init__(self, args: Namespace, player: Player, track_status: TrackStatus, url: str, pafy: BasePafy):
		super().__init__(args, player, track_status)
		self._url = url
		self._pafy: BasePafy = pafy
		self._expiration_timestamp = self._get_new_expiration_date()

	def _get_new_expiration_date(self) -> datetime:
		# YouTube stream URLs expire after a certain time, probably after one or two days.
		# Furthermore a track could be removed from YouTube or its content (e.g. metadata) can change.
		# Therefore we periodically try to reload the track.
		# We add some randomness to the expiration timestamp to prevent reloading multiple tracks at the same time.
		#
		# TODO: handling of tracks that can no longer be resolved (i.e. tracks that have been removed from YouTube).
		#  Playlist update? What else?
		return datetime.now() + timedelta(hours=AVERAGE_TRACK_VALIDITY_IN_HOURS, minutes=randint(-60, 60))

	def _is_expired(self) -> bool:
		return self._expiration_timestamp < datetime.now()

	@property
	def _pafy_data(self) -> BasePafy:
		if not self._pafy or self._is_expired():
			self._pafy: BasePafy = pafy.new(self._url)
			self._expiration_timestamp = self._get_new_expiration_date()
			logger.info('Resolved youtube video (expires at: %s): %s', self._expiration_timestamp.isoformat(), self._pafy)
		return self._pafy

	def __str__(self) -> str:
		if not self._pafy:
			return '<uninitialized track with URL or ID {}>'.format(self._url)
		return super().__str__()

	def get_title(self) -> str:
		return self._determine_artist_and_title()[1]

	def get_artist(self) -> str:
		return self._determine_artist_and_title()[0]

	def get_author(self) -> str:
		return self._pafy_data.author

	def get_url(self) -> str:
		return self._pafy_data.watchv_url

	def get_cover_url(self) -> str:
		return self._pafy_data.bigthumbhd or self._pafy_data.bigthumb or self._pafy_data.thumb

	def get_track_type(self) -> TrackType:
		return TrackType.YOU_TUBE

	def create_vlc_media(self, vlc_instance):
		input_stream = self._get_best_stream()
		logger.debug('Best audio stream of %s: %s (URL: %s)', self, input_stream, input_stream.url)
		logger.debug('Create new VLC media from %s with command: %s', input_stream.url, self._args.vlc_command)
		return vlc_instance.media_new(input_stream.url, self._args.vlc_command)

	def get_duration(self) -> int:
		return self._pafy_data.length * 1000

	def _get_best_stream(self) -> Any:
		return self._pafy_data.getbestaudio()

	def _determine_artist_and_title(self) -> (str, str):
		title: str = self._pafy_data.title
		if not title:
			return self._strip_splits(['', self.get_author()])

		# e.g. "Michael Kiwanuka - Cold Little Heart"
		split = title.split(' - ', 1)
		if len(split) == 2:
			return self._strip_splits(split)

		# "Solomun @ Théâtre Antique d'Orange for Cercle"
		split = title.split(' @ ', 1)
		if len(split) == 2:
			return self._strip_splits(split)

		# "I Got A Name (Jim Croce)"
		find_paranthesis = r'\((.*?)\)'
		all_in_paranthesis = re.findall(find_paranthesis, title)
		if all_in_paranthesis:
			artist = all_in_paranthesis[-1]
			return self._strip(artist, title.replace('(' + artist + ')', ''))

		# split on first special character
		non_alphanumeric_or_whitespace = r'[^a-zA-Z0-9_ ]'
		re_search_result = re.search(non_alphanumeric_or_whitespace, title)
		if re_search_result:
			return self._strip(title[:re_search_result.start()], title[re_search_result.end():])

		return self._strip('', title)

	def _strip_splits(self, split: [str]) -> (str, str):
		return self._strip(split[0], split[1])

	def _strip(self, artist: str, title: str) -> (str, str):
		return artist.strip(), title.strip()


class NullTrack(Track):
	def get_title(self) -> str:
		return ''

	def get_artist(self) -> str:
		return ''

	def get_author(self) -> str:
		return ''

	def get_url(self) -> str:
		return ''

	def get_cover_url(self) -> str:
		return ''

	def get_track_type(self) -> TrackType:
		return TrackType.NULL

	def create_vlc_media(self, vlc_instance): raise NotImplementedError

	def get_duration(self) -> int:
		return 0


class TrackFactory:
	def __init__(self, args: Namespace, player: Player):
		self._args = args
		self._player = player

	def create_youtube_track(self, url: str, track_status=TrackStatus.STOPPED, lazy_load=False) -> YouTubeTrack:
		pafy_data: BasePafy = None
		if not lazy_load:
			pafy_data = pafy.new(url)
		return YouTubeTrack(self._args, self._player, track_status, url, pafy_data)

	def create_youtube_tracks_from_playlist(self, preprocessed_url: str) -> List[YouTubeTrack]:
		playlist = pafy.get_playlist(preprocessed_url)
		playlist_items = playlist['items']
		if not playlist_items:
			logger.warning('Playlist at URL \'{}\' exists but does not contain any items. Resolved playlist: {}'
							 .format(preprocessed_url, playlist))
			return []
		return [YouTubeTrack(self._args, self._player, TrackStatus.STOPPED, item['pafy'].videoid, item['pafy']) for item in playlist_items]

	def _create_youtube_track_from_dict(self, track_dict) -> YouTubeTrack:
		return self.create_youtube_track(track_dict[URL], track_status=TrackStatus(track_dict[STATUS]))

	def track_from_dict(self, track_dict) -> Track:
		type = TrackType(track_dict[TYPE])
		if type == TrackType.NULL:
			return self._player.get_null_track()
		if type == TrackType.YOU_TUBE:
			return self._create_youtube_track_from_dict(track_dict)

