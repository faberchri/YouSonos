import logging
from abc import abstractmethod, ABC
from typing import List, Any, Dict, ValuesView

import soco

from Constants import SendEvent, DbKey, PlayerLoggerName
from . import save_and_emit

INITIAL_SONOS_VOLUME = 5

logger = logging.getLogger(PlayerLoggerName.SONOS_ENVIRONMENT.value)

class StreamConsumer(ABC):

	@abstractmethod
	def play_stream(self, stream_url: str, stream_name: str) -> None: raise NotImplementedError


class SonosEnvironment(StreamConsumer):

	def __init__(self):
		self.sonos_devices = self._find_sonos_devices()
		self.sonos_coordinators = self._find_sonos_coordinators(self.sonos_devices.values())
		self.set_sonos_volume_for_all_devices(INITIAL_SONOS_VOLUME)

	def _create_sonos_setup_dict(self):
		sorted_devices = list(self.sonos_devices.values())
		sorted_devices.sort(key=lambda device: device.player_name)
		return [{'device_name': device.player_name, 'current_volume': device.volume, 'max_volume': 100} for device in sorted_devices]

	def set_sonos_volume_for_all_devices(self, volume: int) -> None:
		for device in self.sonos_devices.values():
			device.volume = volume
			logger.info('Volume of Sonos device with name \'%s\' changed to %d.', device.player_name, device.volume)
		self._update_db_and_emit(SendEvent.VOLUME_CHANGED)

	def set_sonos_volume(self, device_name: str, volume: int, originator_sid: str) -> None:
		device = self.sonos_devices.get(device_name)
		if not device:
			raise ValueError('No Sonos device with name {0} found. Present Sonos devices: {1}'
							 .format(device_name, self.sonos_devices))
		device.volume = volume
		logger.info('Volume of Sonos device with name \'%s\' changed to %d.', device_name, device.volume)
		self._update_db_and_emit(SendEvent.VOLUME_CHANGED, originator_sid=originator_sid)

	def _update_db_and_emit(self, event: SendEvent, originator_sid=None):
		sonos_setup = self._create_sonos_setup_dict()
		save_and_emit(DbKey.SONOS_SETUP, event, sonos_setup, skip_sid=originator_sid)

	def play_stream(self, stream_url: str, stream_name: str) -> None:
		logger.debug('Tuning Sonos coordinator devices (%s) to VLC stream ...', self.sonos_coordinators)
		for sonos_coordinator in self.sonos_coordinators:
			sonos_coordinator.stop()
			sonos_coordinator.play_uri(stream_url, title='vlc-stream')
			logger.debug('Sonos coordinator (%s) started playing URL %s', sonos_coordinator, stream_url)

	def _find_sonos_devices(self) -> Dict[str, Any]:
		discovered = soco.discover()
		if not discovered:
			raise ValueError('No Sonos zones found.')
		sonos_devices = dict(map(lambda zone: (zone.player_name, zone), discovered))
		if not sonos_devices:
			raise ValueError('No Sonos devices found.')
		logger.info('Found Sonos devices: %s', sonos_devices)
		return sonos_devices

	def _find_sonos_coordinators(self, sonos_devices: ValuesView[Any]) -> List[Any]:
		coordinators = [device for device in sonos_devices if device.is_coordinator]
		if not coordinators:
			raise ValueError('No Sonos coordinator device found. Found devices: {0}'.format(sonos_devices))
		logger.debug('Found Sonos coordinator devices: %s', coordinators)
		return coordinators

