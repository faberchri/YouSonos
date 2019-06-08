from __future__ import annotations

from concurrent.futures import Executor, as_completed, Future, CancelledError, TimeoutError
from concurrent.futures.thread import ThreadPoolExecutor
from threading import Lock

from googleapiclient.errors import Error
from googleapiclient.discovery import build, Resource

from . import *

YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'

SEARCH_RESULT_INITIAL_EMIT_BATCH_SIZE = 3
MINIMAL_WAIT_TIME_IN_SECONDS = 7
MAXIMAL_WAIT_TIME_IN_SECONDS = 100
WAIT_TIME_PER_TRACK_IN_SECONDS = 3
NUMBER_OF_WORKERS = 5

logger = logging.getLogger(PlayerLoggerName.SEARCH_SERVICE.value)
logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)


class SearchResult(Iterable[Track]):

	@abstractmethod
	def is_empty(self) -> bool: raise NotImplementedError


class SearchStrategy(ABC):

	@abstractmethod
	def search(self, search_term: str) -> SearchResult: raise NotImplementedError


class UrlBasedSearchResult(SearchResult):

	def __init__(self, tracks: [Track]) -> None:
		self._tracks = tracks

	def is_empty(self) -> bool:
		return len(self._tracks) == 0

	def __iter__(self) -> Iterator[Track]:
		return iter(self._tracks)


class UrlBasedSearchStrategy(SearchStrategy):

	def _preprocess_youtube_url(self, url: str) -> str:
		return url.replace('/m.youtube.com', '/youtube.com')

	def search(self, search_term: str) -> SearchResult:
		url = self._preprocess_youtube_url(search_term)
		try:
			return UrlBasedSearchResult(self.resolve_url(url))
		except Exception:
			return UrlBasedSearchResult([])

	@abstractmethod
	def resolve_url(self, url: str) -> [Track]: raise NotImplementedError


class TrackSearchStrategy(UrlBasedSearchStrategy):

	def __init__(self, track_factory: TrackFactory) -> None:
		self._track_factory = track_factory

	def resolve_url(self, url: str) -> Iterator[Track]:
		return [self._track_factory.create_youtube_track(url)]


class PlaylistSearchStrategy(UrlBasedSearchStrategy):

	def __init__(self, track_factory: TrackFactory) -> None:
		self._track_factory = track_factory

	def resolve_url(self, url: str) -> [Track]:
		return self._track_factory.create_youtube_tracks_from_playlist(url)


class KeywordSearchResultIterator(SearchResult, Iterator[Track]):

	def __init__(self, track_factory: TrackFactory, youtube_api: Resource, search_term: str) -> None:
		self._track_factory = track_factory
		self._youtube_api = youtube_api
		self._next_page_token = None
		self._has_next_page = True
		self._search_term = search_term
		self._video_ids = self._query_youtube_api()
		self._result_count = len(self._video_ids)
		self._index = 0

	def __iter__(self) -> Iterator[Track]:
		return self

	def __next__(self) -> Track:
		video_id = self._get_next_video_id()
		return self._track_factory.create_youtube_track(video_id, lazy_load=True)

	def is_empty(self) -> bool:
		return self._result_count == 0

	def _get_next_video_id(self) -> str:
		if self._index >= len(self._video_ids):
			if self._has_next_page:
				self._video_ids = self._query_youtube_api()
				self._result_count = self._result_count + len(self._video_ids)
				self._index = 0

		if self._index >= len(self._video_ids):
			raise StopIteration

		next_video_id = self._video_ids[self._index]
		self._index = self._index + 1
		return next_video_id

	def _query_youtube_api(self) -> List[str]:
		search_response = self._youtube_api.search().list(
			q=self._search_term,
			part='id',
			maxResults=10,
			type='video',
			pageToken=self._next_page_token
		).execute()
		self._next_page_token = search_response.get('nextPageToken', None)
		if not self._next_page_token:
			self._has_next_page = False
		return [search_result['id']['videoId'] for search_result in search_response.get('items', [])]


class KeywordSearchStrategy(SearchStrategy):

	def __init__(self, track_factory: TrackFactory, youtube_api: Resource) -> None:
		self._track_factory = track_factory
		self._youtube_api = youtube_api

	def search(self, search_term: str) -> Iterator[Track]:
		return KeywordSearchResultIterator(self._track_factory, self._youtube_api, search_term)


class SearchResultTrack:

	def __init__(self, index: int, track: Track) -> None:
		self._index = index
		self._track = track

	def get_property_dict(self):
		return {'index': self._index,
				'track': self._track.get_property_dict()}

	def __str__(self) -> str:
		return '{} {}'.format(self._index, str(self._track))


class SearchTask:

	def __init__(self, search_term: str, sid: str, track_factory: TrackFactory, executor: Executor, youtube_api: Resource):
		self._search_term = search_term
		self._sid = sid
		self._executor = executor
		self._search_strategies = [PlaylistSearchStrategy(track_factory), TrackSearchStrategy(track_factory)]
		if youtube_api:
			self._search_strategies.append(KeywordSearchStrategy(track_factory, youtube_api))
		# appending and extending a list is thread-safe according to
		# https://stackoverflow.com/questions/6319207/are-lists-thread-safe and
		# http://effbot.org/pyfaq/what-kinds-of-global-value-mutation-are-thread-safe.htm
		self._futures: List[Future] = []
		self._has_errors = False
		self._search_completed = False
		self._batch_completed = False
		self._result_index = 0
		self._tracks_iterator = iter(())
		self._lock = Lock()
		self._search_results: Dict[int, SearchResultTrack] = {}

	@property
	def sid(self) -> str:
		return self._sid

	@property
	def search_term(self) -> str:
		return self._search_term

	def start(self, batch_index: int, requested_search_indices: List[int]) -> None:
		future = self._executor.submit(self._start, batch_index, requested_search_indices)
		self._futures.append(future)

	def get_results(self, batch_index: int, requested_search_indices: List[int]) -> None:
		future = self._executor.submit(self._get_results,  batch_index, requested_search_indices)
		self._futures.append(future)

	def cancel(self) -> None:
		for future in self._futures:
			future.cancel()

	def completed(self) -> bool:
		return self._search_completed and self._batch_completed

	def _start(self, batch_index: int, requested_search_indices: List[int]):
		with self._lock:
			self._tracks_iterator = self._find_search_result()
			result_batch = self._fetch_result_batch(requested_search_indices)
			# signal error if we didn't find anything
			if self._result_index == 0:
				self._has_errors = True
			self._send_result_batch(batch_index, result_batch)

	def _get_results(self, batch_index: int, requested_search_indices: List[int]):
		if self._lock.acquire(blocking=False):
			try:
				self._batch_completed = False
				result_batch = self._fetch_result_batch(requested_search_indices)
				self._send_result_batch(batch_index, result_batch)
			finally:
				self._lock.release()

	def _find_search_result(self) -> Iterator[Track]:
		futures: List[Future] = [self._executor.submit(search_strategy.search, self._search_term) for search_strategy in self._search_strategies]
		self._futures.extend(futures)
		track_iterable: Iterable[Track] = ()
		for future in futures:
			track_iterable: SearchResult = self._fetch_search_result(future, futures)
			if not track_iterable.is_empty():
				break
		[future.cancel() for future in futures]
		return iter(track_iterable)

	def _fetch_search_result(self, future: Future, futures: List[Future]) -> SearchResult:
		def description():
			strategy = self._search_strategies[futures.index(future)]
			return 'search strategy \'%s\''.format(strategy)
		return self._fetch_result(future, UrlBasedSearchResult([]), description)

	def _fetch_result_batch(self, requested_search_indices: List[int]) -> [SearchResultTrack]:
		batch_index_end = self._result_index
		if requested_search_indices:
			batch_index_end = max(max(requested_search_indices), batch_index_end)
		try:
			while self._result_index <= batch_index_end:
				self._search_results[self._result_index] = SearchResultTrack(self._result_index, next(self._tracks_iterator))
				self._result_index = self._result_index + 1
		except StopIteration:
				self._search_completed = True
		return [self._search_results[result_index] for result_index in requested_search_indices if self._search_results.get(result_index)]

	def _send_result_batch(self, batch_index: int, result_batch: [SearchResultTrack]) -> None:
		result_batch_futures: List[Future] = [self._executor.submit(entry.get_property_dict) for entry in result_batch]
		self._futures.extend(result_batch_futures)
		property_dicts = []
		next_emit = SEARCH_RESULT_INITIAL_EMIT_BATCH_SIZE
		timeout = min(MINIMAL_WAIT_TIME_IN_SECONDS + (len(result_batch) * WAIT_TIME_PER_TRACK_IN_SECONDS) / NUMBER_OF_WORKERS, MAXIMAL_WAIT_TIME_IN_SECONDS)
		for track_future in as_completed(result_batch_futures, timeout=timeout):
			property_dict = self._fetch_property_dict(track_future, result_batch_futures, result_batch)
			if property_dict:
				property_dicts.append(property_dict)
			if len(property_dicts) == next_emit:
				self._emit_search_result(batch_index, property_dicts)
				next_emit = len(property_dicts) * 2
				property_dicts = []
		self._batch_completed = True
		self._emit_search_result(batch_index, property_dicts)

	def _fetch_property_dict(self, track_future: Future, result_batch_futures: List[Future], result_batch: [SearchResultTrack]):
		def description():
			result_track = result_batch[result_batch_futures.index(track_future)]
			return 'track dict of \'%s\''.format(str(result_track))
		return self._fetch_result(track_future, None, description)

	def _emit_search_result(self, batch_index: int, property_dicts):
		search_result = {
			'search_string': self._search_term,
			'batch_index': batch_index,
			'search_completed': self._search_completed,
			'batch_completed': self._batch_completed,
			'has_error': self._has_errors,
			'results': property_dicts
		}
		logger.info('emitting search result for \'%s\' of size %d (%s)', self._search_term, len(property_dicts), search_result)
		emit(SendEvent.SEARCH_RESULTS, search_result, sid=self._sid)

	def _fetch_result(self, future: Future, default_result, description_callback):
		try:
			return future.result(timeout=MINIMAL_WAIT_TIME_IN_SECONDS)
		except CancelledError:
			logger.debug('Loading of %s (Future: %s) was cancelled.', description_callback(), future, exc_info=False)
		except TimeoutError:
			self._has_errors = True
			logger.debug('Loading of %s (Future: %s) resulted in timeout.', description_callback(), future, exc_info=False)
		except Exception as exc:
			self._has_errors = True
			logger.warning('Exception when loading %s (Future: %s).', description_callback(), future, exc_info=True)
		return default_result


class SearchService:

	def __init__(self, track_factory: TrackFactory, youtube_api_key: str):
		self._track_factory = track_factory
		self._youtube_api_key = youtube_api_key
		self._executor = ThreadPoolExecutor(max_workers=NUMBER_OF_WORKERS, thread_name_prefix='SearchServiceThread')
		self._search_tasks: Dict[str, SearchTask] = {}
		self._youtube_api: Resource = None
		if self._youtube_api_key:
			try:
				self._youtube_api: Resource = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
						developerKey=self._youtube_api_key)
			except Error:
				logger.warning('Error on attempt to initialize YouTube API service. Did you specify an invalid API key? '
							   'Keyword search will be disabled.', exc_info=True)
		else:
			logger.info('No Google / YouTube API key was specified. Keyword search will be disabled.')

	def run_search(self, search_term: str, batch_index: int, requested_search_indices: List[int], sid: str) -> None:
		logger.info('run search for \'%s\' of %s (requested search result indices: %s)', search_term, sid, requested_search_indices)
		search_task = self._search_tasks.get(sid)
		if not search_task or search_task.search_term != search_term:
			if search_task:
				search_task.cancel()
			search_task = SearchTask(search_term, sid, self._track_factory, self._executor, self._youtube_api)
			search_task.start(batch_index, requested_search_indices)
			self._search_tasks[sid] = search_task
		else:
			search_task.get_results(batch_index, requested_search_indices)
		self._cleanup_search_tasks()

	def cancel_search(self, sid: str) -> None:
		logger.info('cancel search for %s', sid)
		search_task = self._search_tasks.get(sid)
		if search_task:
			search_task.cancel()
		self._cleanup_search_tasks()

	# FIXME: memory leak: user queries for big playlist (iterator does not complete) and terminates session. Max search task age?
	def _cleanup_search_tasks(self):
		self._search_tasks = {search_task.sid: search_task for search_task in self._search_tasks.values() if not search_task.completed()}
