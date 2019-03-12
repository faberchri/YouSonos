from __future__ import annotations

from concurrent.futures.thread import ThreadPoolExecutor

import logging
import uuid
from enum import Enum, unique
from typing import Callable
from uuid import UUID

from Constants import PlayerLoggerName
from player.Track import Track, TrackFactory

ID = 'playlist_entry_id'
TRACK = 'track'
STATUS = 'status'

logger = logging.getLogger(PlayerLoggerName.PLAYLIST_ENTRY.value)

@unique
class PlaylistEntryStatus(Enum):
	COMPLETED = 'COMPLETED'
	CURRENT = 'CURRENT'
	WAITING = 'WAITING'


class PlaylistEntry:

	def __init__(self, track: Track, initial_status: PlaylistEntryStatus, id: UUID):
		self._playlist_entry_status = initial_status
		self._track = track
		self._playlist_entry_id = id
		self._previous_entry: PlaylistEntry = None
		self._next_entry: PlaylistEntry = None

	@property
	def playlist_entry_id(self) -> UUID:
		return self._playlist_entry_id

	@property
	def track(self) -> Track:
		return self._track

	@property
	def previous_entry(self) -> PlaylistEntry:
		return self._previous_entry

	@property
	def next_entry(self) -> PlaylistEntry:
		return self._next_entry

	@property
	def playlist_entry_status(self) -> PlaylistEntryStatus:
		return self._playlist_entry_status

	@playlist_entry_status.setter
	def playlist_entry_status(self, new_status: PlaylistEntryStatus) -> None:
		self._playlist_entry_status = new_status

	def play(self) -> None:
		self.set_to_current()
		self.track.play()

	def toggle_play_pause(self) -> None:
		self.set_to_current()
		self.track.toggle_play_pause()

	def play_previous(self) -> None:
		if self._previous_entry:
			self.previous_entry.play()
		else:
			self.play()

	def play_next(self) -> None:
		if self.next_entry:
			self.next_entry.play()
		else:
			logger.info('Playlist ended')

	def stop(self) -> None:
		self.track.stop()

	def set_to_current(self) -> None:
		self.playlist_entry_status = PlaylistEntryStatus.CURRENT
		self.update_playlist_entry_stati()

	def update_playlist_entry_stati(self) -> None:
		def on_previous(entry: PlaylistEntry) -> None:
			entry._playlist_entry_status = PlaylistEntryStatus.COMPLETED
		self._apply_on_all_preceding_entries(on_previous)
		def on_succeeding(entry: PlaylistEntry) -> None:
			entry._playlist_entry_status = PlaylistEntryStatus.WAITING
		self._apply_on_all_succeeding_entries(on_succeeding)

	def _apply_on_all_preceding_entries(self, callback: Callable[[PlaylistEntry], None]) -> None:
		previous_entry = self.previous_entry
		while previous_entry is not None:
			callback(previous_entry)
			previous_entry = previous_entry.previous_entry

	def _apply_on_all_succeeding_entries(self, callback: Callable[[PlaylistEntry], None]) -> None:
		next_entry = self.next_entry
		while next_entry is not None:
			callback(next_entry)
			next_entry = next_entry.next_entry

	def set_links(self, previous: PlaylistEntry, next: PlaylistEntry) -> None:
		self._previous_entry = previous
		self._next_entry = next

	def __str__(self) -> str:
		return 'PLaylist entry for track: {} (status: {}, id: {})'\
			.format(self.track, self.playlist_entry_status, self.playlist_entry_id)

	def get_property_dict(self) -> {}:
		return {ID: str(self.playlist_entry_id),
				TRACK: self.track.get_property_dict(),
				STATUS: self.playlist_entry_status.value}


class PlaylistEntryFactory:
	def __init__(self, track_factory: TrackFactory):
		self._track_factory = track_factory

	def create_playlist_entry_from_youtube_url(self, url: str) -> PlaylistEntry:
		return PlaylistEntry(self._track_factory.create_youtube_track(url), PlaylistEntryStatus.WAITING, uuid.uuid4())

	def playlist_entries_from_props_list(self, playlist_entry_dicts: []) -> [PlaylistEntry]:
		executor = ThreadPoolExecutor(max_workers=100, thread_name_prefix='PlayListLoaderThread')
		futures = [executor.submit(self._load_playlist_entry_from_property_dict, playlist_entry_dict) for playlist_entry_dict in playlist_entry_dicts]
		executor.shutdown()
		return [future.result() for future in futures]

	def _load_playlist_entry_from_property_dict(self, playlist_entry_dict: {}) -> PlaylistEntry:
		track_dict = playlist_entry_dict[TRACK]
		track = self._track_factory.track_from_dict(track_dict)
		return PlaylistEntry(track, PlaylistEntryStatus(playlist_entry_dict[STATUS]), UUID(playlist_entry_dict[ID]))
