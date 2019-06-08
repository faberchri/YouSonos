from __future__ import annotations

import time
from uuid import UUID

from . import *


class Playlist(PlayerObserver):

	def __init__(self, playlist_entry_factory: PlaylistEntryFactory):
		super().__init__()
		self._playlist_entry_factory = playlist_entry_factory
		self.playlist_entries: List[PlaylistEntry] = []

	def player_status_changed(self, previous_status: PlayerStatus, new_status: PlayerStatus, current_track: Track) -> None:
		self._save_and_emit_playlist()

	def read_playlist_from_db(self) -> None:
		self.playlist_entries = self._playlist_entry_factory.playlist_entries_from_props_list(read_list_from_db(DbKey.PLAYLIST))
		def init_player(entry: PlaylistEntry) -> None:
			# after startup we want the current playlist entry to be loaded but paused
			# play() ensures the track is loaded and playing
			entry.play()
			# without sleep the pause command is ignored from vlc player
			time.sleep(1)
			# set to paused
			entry.toggle_play_pause()
		self.on_current(init_player)
		self._save_and_emit_playlist()

	def on_current(self, callback: [Callable[[PlaylistEntry], None]]) -> None:
		if self.playlist_entries:
			current = next((entry for entry in self.playlist_entries if entry.is_current()), self.playlist_entries[0])
			callback(current)

	def play_previous(self) -> None:
		def play_previous(entry: PlaylistEntry) -> None:
			entry.play_previous()
		self.on_current(play_previous)

	def play_next(self) -> None:
		def play_next(entry: PlaylistEntry):
			entry.play_next()
		self.on_current(play_next)

	def play_track_of_playlist(self, playlist_entry_id: str) -> None:
		def callback(position: int, entry: PlaylistEntry) -> None:
			entry.toggle_play_pause()
		self._run_if_present(playlist_entry_id, callback)

	def clear(self) -> None:
		def stop_current(entry: PlaylistEntry) -> None:
			entry.stop()
		self.on_current(stop_current)
		self.playlist_entries.clear()
		self._save_and_emit_playlist()

	def add_track_at_end(self, url: str) -> None:
		self.add_track(url, len(self.playlist_entries))

	def add_track(self, url: str, position: int) -> None:
		new_playlist_entry = self._playlist_entry_factory.create_playlist_entry_from_youtube_url(url)
		self.playlist_entries.insert(min(position, len(self.playlist_entries)), new_playlist_entry)
		self._save_and_emit_playlist()

	def delete_track(self, playlist_entry_id: str) -> None:
		# TODO think about behaviour if track to delete is same as current in player.
		# TODO 1) how should behaviour be if paused? how if playing? 2) how if started from playlist? how if started from search results?
		def callback (position: int, entry: PlaylistEntry) -> None:
			def next_if_current(current: PlaylistEntry) -> None:
				if entry == current:
					current.stop()
					current.play_next()
			self.on_current(next_if_current)
			self.playlist_entries.pop(position)
			self._save_and_emit_playlist()
		self._run_if_present(playlist_entry_id, callback)

	def change_track_position(self, playlist_entry_id: str, target_position: int) -> None:
		def callback (position: int, entry: PlaylistEntry) -> None:
			if position != target_position:
				self.playlist_entries.pop(position)
				self.playlist_entries.insert(min(target_position, len(self.playlist_entries)), entry)
				self._save_and_emit_playlist()
		self._run_if_present(playlist_entry_id, callback)

	def _run_if_present(self, play_list_entry_id: str, callback: Callable[[int, PlaylistEntry], None]) -> None:
		play_list_entry_uuid = UUID(play_list_entry_id)
		position, entry = next(((position, entry) for position, entry in enumerate(self.playlist_entries)
								if entry.playlist_entry_id == play_list_entry_uuid), (None, None))
		if entry: # test *only* for entry, since if position == 0 bool(position) evaluates to False
			callback(position, entry)

	def _update_entry_links(self) -> None:
		previous_entry: PlaylistEntry = None
		for index, entry in enumerate(self.playlist_entries):
			next_entry: PlaylistEntry = None
			index_of_next = index + 1
			if index_of_next < len(self.playlist_entries):
				next_entry = self.playlist_entries[index_of_next]
			entry.set_links(previous_entry, next_entry)
			previous_entry = entry

	def _update_stati(self) -> None:
		def update_stati(entry: PlaylistEntry) -> None:
			entry.update_playlist_entry_stati()
		self.on_current(update_stati)

	def _save_and_emit_playlist(self) -> None:
		self._update_entry_links()
		self._update_stati()
		property_dicts = [playlist_entry.get_property_dict() for playlist_entry in self.playlist_entries]
		save_and_emit(DbKey.PLAYLIST, SendEvent.PLAYLIST_CHANGED, property_dicts)
