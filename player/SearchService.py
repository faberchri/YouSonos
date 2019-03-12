import logging
from typing import List, Dict

from concurrent.futures import Executor, as_completed, Future, CancelledError
from concurrent.futures.thread import ThreadPoolExecutor

from Constants import SendEvent, PlayerLoggerName
from player.Track import TrackFactory, Track

from . import emit

SEARCH_RESULT_INITIAL_EMIT_BATCH_SIZE = 3
MINIMAL_WAIT_TIME_IN_SECONDS = 7
MAXIMAL_WAIT_TIME_IN_SECONDS = 100
WAIT_TIME_PER_TRACK_IN_SECONDS = 3
NUMBER_OF_WORKERS = 5

logger = logging.getLogger(PlayerLoggerName.SEARCH_SERVICE.value)


class SearchTask:

	def __init__(self, url: str, sid: str, track_factory: TrackFactory, executor: Executor):
		self._url = url
		self._sid = sid
		self._track_factory = track_factory
		self._executor = executor
		# appending and extending a list is thread-safe according to
		# https://stackoverflow.com/questions/6319207/are-lists-thread-safe and
		# http://effbot.org/pyfaq/what-kinds-of-global-value-mutation-are-thread-safe.htm
		self._futures: List[Future] = []
		self._has_errors = False
		self._completed = False
		self._search_results = []

	@property
	def sid(self) -> str:
		return self._sid

	def start(self) -> None:
		future = self._executor.submit(self._run)
		self._futures.append(future)

	def cancel(self) -> None:
		for future in self._futures:
			future.cancel()

	def completed(self) -> bool:
		return self._completed

	def _run(self) -> None:
		tracks = self._create_youtube_track()
		if self._completed:
			return
		track_futures = [self._executor.submit(track.get_property_dict) for track in tracks]
		self._futures.extend(track_futures)
		property_dicts = [None] * len(track_futures)
		next_emit = SEARCH_RESULT_INITIAL_EMIT_BATCH_SIZE
		timeout = min(MINIMAL_WAIT_TIME_IN_SECONDS + (len(track_futures) * WAIT_TIME_PER_TRACK_IN_SECONDS) / NUMBER_OF_WORKERS, MAXIMAL_WAIT_TIME_IN_SECONDS)
		for track_future in as_completed(track_futures, timeout=timeout):
			playlist_index = track_futures.index(track_future)
			property_dict = self._fetch_search_result(track_future, tracks[playlist_index])
			property_dicts[playlist_index] = property_dict
			self._search_results = [property_dict for property_dict in property_dicts if property_dict is not None]
			if len(self._search_results) == next_emit:
				self._emit_search_result()
				next_emit = len(self._search_results) * 2
		self._completed = True
		# signal error if we are done and didn't find anything
		if not self._search_results:
			self._has_errors = True
		self._emit_search_result()

	def _create_youtube_track(self) -> [Track]:
		try:
			return self._track_factory.create_youtube_tracks(self._url)
		except Exception as exc:
			self._has_errors = True
			self._completed = True
			logger.warning('Exception when creating tracks list from \'%s\'.', self._url, exc_info=True)
			self._emit_search_result()
			return []

	def _fetch_search_result(self, track_future: Future, track: Track):
		try:
			return track_future.result()
		except CancelledError:
			logger.debug('Loading of track dict of \'%s\' (Future: %s) was cancelled.', track, track_future, exc_info=False)
		except Exception as exc:
			self._has_errors = True
			logger.warning('Exception when loading track dict of \'%s\' (Future: %s).', track, track_future, exc_info=True)
		return None

	def _emit_search_result(self):
		search_result = {'search_string': self._url,
			'search_completed': self._completed,
			'has_error': self._has_errors,
			'results': self._search_results
		}
		logger.info('emitting search result for \'%s\' of size %d', self._url, len(self._search_results))
		emit(SendEvent.SEARCH_RESULTS, search_result, sid=self._sid)


class SearchService:

	def __init__(self, track_factory: TrackFactory):
		self._track_factory = track_factory
		self._executor = ThreadPoolExecutor(max_workers=NUMBER_OF_WORKERS, thread_name_prefix='SearchServiceThread')
		self._search_tasks: Dict[str, SearchTask] = {}

	def run_search(self, url: str, sid: str) -> None:
		logger.info('run search for \'%s\' of %s', url, sid)
		search_task = SearchTask(url, sid, self._track_factory, self._executor)
		search_task.start()
		self._cancel_search(sid)
		self._search_tasks[sid] = search_task
		self._cleanup_search_tasks()

	def cancel_search(self, sid: str) -> None:
		logger.info('cancel search for %s', sid)
		self._cancel_search(sid)
		self._cleanup_search_tasks()

	def _cancel_search(self, sid: str):
		search_task = self._search_tasks.get(sid)
		if search_task:
			search_task.cancel()

	def _cleanup_search_tasks(self):
		self._search_tasks = {search_task.sid: search_task for search_task in self._search_tasks.values() if not search_task.completed()}
