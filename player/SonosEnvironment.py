from __future__ import annotations

import soco
from soco.core import SoCo
import threading

from Util import StoppableThreadWithEvent, StoppableThread
from . import *

INITIAL_SONOS_VOLUME = 5
SONOS_DISCOVERY_INTERVAL_IN_SECONDS = 30

logger = logging.getLogger(PlayerLoggerName.SONOS_ENVIRONMENT.value)


class StreamConsumer(ABC):

	@abstractmethod
	def play_stream(self, track: Track) -> None: raise NotImplementedError


T = TypeVar('T')
SonosDevicesByName = Dict[str, SoCo]


class SonosEnvironment(StreamConsumer):

	def __init__(self):
		self._sonos_devices_lock = threading.Lock()
		self._sonos_devices = self._find_sonos_devices()
		if self._add_all_devices_to_one_zone(self._sonos_devices):
			logger.info(f"Initial Sonos device setup after zone unification: "
						f"{self._create_devices_description(self._sonos_devices)}")
		self._update_db_and_emit(self._sonos_devices, SendEvent.SONOS_SETUP)
		self.set_sonos_volume_for_all_devices(INITIAL_SONOS_VOLUME)
		self._monitoring_thread = StoppableThreadWithEvent(self._monitor_sonos_environment)

	def start_sonos_environment_monitoring(self) -> StoppableThread:
		self._monitoring_thread.start()
		return self._monitoring_thread

	def set_sonos_volume_for_all_devices(self, volume: int) -> None:
		def set_sonos_volume_for_all_devices(sonos_devices: SonosDevicesByName):
			for device in sonos_devices.values():
				self._set_device_volume(device, volume)
			self._update_db_and_emit(sonos_devices, SendEvent.VOLUME_CHANGED)
		return self._with_sonos_devices(set_sonos_volume_for_all_devices)

	def set_sonos_volume(self, device_name: str, volume: int, originator_sid: str) -> None:
		def set_sonos_volume(sonos_devices: SonosDevicesByName) -> None:
			device = sonos_devices.get(device_name)
			if not device:
				raise ValueError(f"No Sonos device with name {device_name} found. "
								 f"Present Sonos devices: {sonos_devices}")
			self._set_device_volume(device, volume)
			self._update_db_and_emit(sonos_devices, SendEvent.VOLUME_CHANGED, originator_sid=originator_sid)
		return self._with_sonos_devices(set_sonos_volume)

	def play_stream(self, track: Track) -> None:
		def play_stream(sonos_devices: SonosDevicesByName) -> None:
			sonos_coordinators = self._find_sonos_coordinators(sonos_devices)
			stream_url = track.get_out_stream_url(sonos_coordinators[0].ip_address)
			logger.debug('Tuning Sonos coordinator devices (%s) to stream on %s ...', sonos_coordinators, stream_url)
			for sonos_coordinator in sonos_coordinators:
				sonos_coordinator.stop()
				title = '{} - {}'.format(track.get_title(), track.get_artist())
				sonos_coordinator.play_uri(stream_url, title=title, force_radio=True)
				logger.debug('Sonos coordinator (%s) started playing URL %s', sonos_coordinator, stream_url)
		self._with_sonos_devices(play_stream)

	def _with_sonos_devices(self, callback: Callable[[SonosDevicesByName], T]) -> T:
		with self._sonos_devices_lock:
			return callback(self._sonos_devices)

	def _set_device_volume(self, device: SoCo, volume: int):
		device.volume = volume
		logger.info('Volume of Sonos device with name \'%s\' changed to %d.', device.player_name, device.volume)

	def _update_db_and_emit(self, sonos_devices: SonosDevicesByName, event: SendEvent, originator_sid=None):
		sonos_setup = self._create_sonos_setup_dict(sonos_devices)
		save_and_emit(DbKey.SONOS_SETUP, event, sonos_setup, skip_sid=originator_sid)

	def _create_sonos_setup_dict(self, sonos_devices: SonosDevicesByName) -> List[PropDict]:
		sorted_devices = list(sonos_devices.values())
		sorted_devices.sort(key=lambda device: device.player_name)
		return [{'device_name': device.player_name, 'current_volume': device.volume, 'max_volume': 100}
				for device in sorted_devices]

	def _monitor_sonos_environment(self) -> None:
		while True:
			if self._monitoring_thread.get_exit_event().wait(SONOS_DISCOVERY_INTERVAL_IN_SECONDS):
				break
			new_sonos_devices = {}
			try:
				new_sonos_devices = self._find_sonos_devices()
			except Exception:
				logger.warning('Exception in Sonos discovery routine.', exc_info=True)

			def set_sonos_devices(previous_sonos_devices: SonosDevicesByName) -> None:
				unified= self._add_all_devices_to_one_zone(new_sonos_devices)
				self._sonos_devices = new_sonos_devices
				logger.info(f"Sonos environment monitoring routine completed (Groups unification took place: {unified}). "
							f"New setup: {self._create_devices_description(new_sonos_devices)}.")
				self._update_db_and_emit(new_sonos_devices, SendEvent.SONOS_SETUP)
			try:
				self._with_sonos_devices(set_sonos_devices)
			except Exception:
				logger.warning('Exception in unifying or reassigning Sonos devices.', exc_info=True)

	def _find_sonos_devices(self) -> SonosDevicesByName:
		discovered = soco.discover()
		if not discovered:
			logger.warning('No Sonos zones found.')
			discovered = []
		sonos_devices: SonosDevicesByName = dict(map(lambda zone: (zone.player_name, zone), discovered))
		if not sonos_devices:
			logger.warning('No Sonos devices found.')
		else:
			logger.info(f"Sonos discovery routine found the following devices: "
						f"{self._create_devices_description(sonos_devices)}")
		return sonos_devices

	def _add_all_devices_to_one_zone(self, sonos_devices: SonosDevicesByName) -> bool:
		sonos_devices_list = list(sonos_devices.values())
		if len(sonos_devices_list) > 0 and len(set([vz.group.uid for vz in sonos_devices_list[0].visible_zones])) > 1:
			logger.info(f"Visible zones are in more than one group. Unifying all devices to one group. "
						f"First device: {sonos_devices_list[0]}")
			sonos_devices_list[0].partymode() # call only on one device in network
			return True
		return False

	def _find_sonos_coordinators(self, sonos_devices: SonosDevicesByName) -> List[SoCo]:
		coordinators = [device for device in sonos_devices.values() if device.is_coordinator]
		if not coordinators:
			raise ValueError('No Sonos coordinator device found. Found devices: {0}'.format(sonos_devices))
		logger.debug('Found Sonos coordinator devices: %s', coordinators)
		return coordinators

	def _create_devices_description(self, sonos_devices: SonosDevicesByName) -> List[str]:
		r = []
		for item in sonos_devices.items():
			group = item[1].group
			if group:
				r.append(f"[{item[0]}: {item[1]!r}, group_label: <{group.label}>, group_id: "
						 f"{group.uid}, coordinator: {group.coordinator!r}]")
			else:
				r.append(f"[{item[0]}: {item[1]!r}]")
		return r
