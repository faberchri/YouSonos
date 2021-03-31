from abc import abstractmethod
from threading import Thread, Event


class StoppableThread(Thread):

	@abstractmethod
	def stop(self) -> None: raise NotImplementedError


class StoppableThreadWithEvent(StoppableThread):

	def __init__(self, target):
		super().__init__(target=target)
		self._exit_event = Event()

	def stop(self):
		self._exit_event.set()

	def get_exit_event(self):
		return self._exit_event
