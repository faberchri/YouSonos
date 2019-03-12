from __future__ import annotations

import logging
import re
from abc import abstractmethod
from enum import Enum, unique
from typing import Any

import pafy
from pafy.backend_shared import BasePafy

from Constants import Source, DbKey, SendEvent, PlayerLoggerName
from player.Player import PlayerObserver, PlayerStatus, Player

from . import save_and_emit

URL = 'url'
TYPE = 'track_type'
STATUS = 'track_status'
COVER_URL= 'cover_url'
DURATION= 'duration'

VLC_STREAM_QUALITY = '192'

VLC_STREAM_NAME_AAC = 'vlc.mp4'
VLC_STREAM_NAME_MP3 = 'vlc.mp3'

VLC_TRANSCODE_CMD_AAC = ':sout=#transcode{aenc=ffmpeg{strict=-2},acodec=mp4a,ab=' + VLC_STREAM_QUALITY + '}:standard{mux=raw,dst=/' + VLC_STREAM_NAME_AAC + ',access=http,sap}'
VLC_TRANSCODE_CMD_MP3 = ':sout=#transcode{acodec=mp3,ab=' + VLC_STREAM_QUALITY + '}:standard{mux=raw,dst=/' + VLC_STREAM_NAME_MP3 + ',access=http,sap}'

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

	def __init__(self, player: Player, track_status: TrackStatus):
		super().__init__()
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

	@abstractmethod
	def get_vlc_stream_name(self) -> str: raise NotImplementedError

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

	def __init__(self, player: Player, track_status: TrackStatus, pafy_data: BasePafy):
		super().__init__(player, track_status)
		self._pafy_data = pafy_data
		logger.debug('Resolved youtube video:\n%s', self._pafy_data)
		self.artist, self.title = self.determine_artist_and_title()

	def get_title(self) -> str:
		return self.title

	def get_artist(self) -> str:
		return self.artist

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
		cmd = VLC_TRANSCODE_CMD_MP3
		logger.debug('Create new VLC media from %s with command: %s', input_stream.url, cmd)
		return vlc_instance.media_new(input_stream.url, cmd)

	def get_vlc_stream_name(self) -> str:
		return VLC_STREAM_NAME_MP3

	def get_duration(self) -> int:
		return self._pafy_data.length * 1000

	def _get_best_stream(self) -> Any:
		return self._pafy_data.getbestaudio()

	def determine_artist_and_title(self) -> (str, str):
		title: str = self._pafy_data.title
		if not title:
			return self.strip_splits(['', self.get_author()])

		# e.g. "Michael Kiwanuka - Cold Little Heart"
		split = title.split(' - ', 1)
		if len(split) == 2:
			return self.strip_splits(split)

		# "Solomun @ Théâtre Antique d'Orange for Cercle"
		split = title.split(' @ ', 1)
		if len(split) == 2:
			return self.strip_splits(split)

		# "I Got A Name (Jim Croce)"
		find_paranthesis = r'\((.*?)\)'
		all_in_paranthesis = re.findall(find_paranthesis, title)
		if all_in_paranthesis:
			artist = all_in_paranthesis[-1]
			return self.strip(artist, title.replace('(' + artist + ')', ''))

		# split on first special character
		non_alphanumeric_or_whitespace = r'[^a-zA-Z0-9_ ]'
		re_search_result = re.search(non_alphanumeric_or_whitespace, title)
		if re_search_result:
			return self.strip(title[:re_search_result.start()], title[re_search_result.end():])

		return self.strip('', title)

	def strip_splits(self, split: [str]) -> (str, str):
		return self.strip(split[0], split[1])

	def strip(self, artist: str, title: str) -> (str, str):
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

	def get_vlc_stream_name(self) -> str:
		return ''

	def get_duration(self) -> int:
		return 0


class TrackFactory:
	def __init__(self, player: Player):
		self._player = player

	def create_youtube_tracks(self, url: str) -> [YouTubeTrack]:
		preprocessed_url = self._preprocess_youtube_url(url)
		try:
			playlist = pafy.get_playlist(preprocessed_url)
			if not playlist:
				raise ValueError('Playlist at URL \'{}\' but does not contain any items. Resolved playlist: {}'.format(preprocessed_url, playlist))
			return self._create_youtube_tracks_from_playlist(playlist)
		except Exception:
			pass
		try:
			pafy_data = pafy.new(preprocessed_url)
			return [YouTubeTrack(self._player, TrackStatus.STOPPED, pafy_data)]
		except Exception:
			pass
		logger.warning('Neither a YouTube playlist nor a single YouTube video was found at \'%s\'', preprocessed_url)
		return []

	def _preprocess_youtube_url(self, url: str) -> str:
		return url.replace('/m.youtube.com', '/youtube.com')

	def _create_youtube_tracks_from_playlist(self, raw_playlist) -> [YouTubeTrack]:
		return [YouTubeTrack(self._player, TrackStatus.STOPPED, item['pafy']) for item in raw_playlist['items']]

	def create_youtube_track(self, url: str, track_status=TrackStatus.STOPPED) -> YouTubeTrack:
		return YouTubeTrack(self._player, track_status, pafy.new(url))

	def _create_youtube_track_from_dict(self, track_dict) -> YouTubeTrack:
		return self.create_youtube_track(track_dict[URL], track_status=TrackStatus(track_dict[STATUS]))

	def track_from_dict(self, track_dict) -> Track:
		type = TrackType(track_dict[TYPE])
		if type == TrackType.NULL:
			return self._player.get_null_track()
		if type == TrackType.YOU_TUBE:
			return self._create_youtube_track_from_dict(track_dict)

