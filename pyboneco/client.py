import logging
from bleak import BleakScanner, BleakClient
from bleak.backends.device import BLEDevice
from bleak_retry_connector import BLEAK_RETRY_EXCEPTIONS

from .advertising_data import BonecoAdvertisingData
from .auth import AuthState, BonecoAuth
from .constants import (
    CHARACTERISTIC_AUTH,
    CHARACTERISTIC_AUTH_AND_SERVICE,
    CHARACTERISTIC_DEVICE_STATE,
    CHARACTERISTIC_DEVICE_INFO,
    CHARACTERISTIC_DEVICE_NAME,
)
from .device_info import BonecoDeviceInfo
from .device_state import DeviceState

logger = logging.getLogger(__name__)


class BonecoClient:
    _auth_data: BonecoAuth
    _client: BleakClient

    def __init__(self, client: BleakClient, auth_data: BonecoAuth):
        self._client = client
        self._auth_data = auth_data

    def require_auth(func):
        async def wrapped(self, *args, **kwargs):
            await self._ensure_connected()
            if self._auth_data.current_state != AuthState.AUTH_SUCCESS:
                await self.authorize()
                if self._auth_data.current_state == AuthState.AUTH_ERROR:
                    raise ValueError()
            return await func(self, *args, **kwargs)

        return wrapped

    @staticmethod
    async def find_boneco_devices(
        timeout: float = 5.0,
    ) -> dict[BLEDevice, BonecoAdvertisingData]:
        devices_data = await BleakScanner.discover(timeout, return_adv=True)
        manufacturer_data = {
            device: BonecoAdvertisingData(
                *next(iter(adv_data.manufacturer_data.items()))
            )
            for device, adv_data in devices_data.values()
            if len(adv_data.manufacturer_data) > 0
        }
        return {k: v for k, v in manufacturer_data.items() if v.is_boneco_device}

    async def connect(self) -> bool:
        await self._client.connect()

    async def disconnect(self) -> None:
        try:
            await self._client.disconnect()
        except BLEAK_RETRY_EXCEPTIONS as ex:
            logger.warning(f"{self._get_internal_name()}: Error disconnecting: {ex}")
        else:
            logger.debug(
                f"{self._get_internal_name()}: Disconnect completed successfully"
            )

    async def authorize(self) -> None:
        try:
            await self._client.start_notify(
                CHARACTERISTIC_AUTH, self._auth_data.auth_handler
            )
            while True:
                await self._auth_data.state_changed.wait()
                logger.debug(
                    f"{self._get_internal_name()}: Current state is {self._auth_data.current_state}"
                )
                self._auth_data.state_changed.clear()
                match self._auth_data.current_state:
                    case AuthState.AUTH_ERROR:
                        logger.error(
                            f"{self._get_internal_name()}: Can't auth. Exiting"
                        )
                        break
                    case AuthState.GOT_NONCE:
                        await self._client.start_notify(
                            CHARACTERISTIC_AUTH_AND_SERVICE,
                            self._auth_data.characteristics_handler,
                        )
                        logger.debug(
                            f"{self._get_internal_name()}: Sending challenge response"
                        )
                        await self._client.write_gatt_char(
                            CHARACTERISTIC_AUTH,
                            self._auth_data.get_request_for_auth_level(0),
                        )
                    case AuthState.CONFIRM_WAITING:
                        logger.info(
                            f"{self._get_internal_name()}: Press device button to confirm"
                        )
                    case AuthState.CONFIRMED:
                        logger.debug(
                            f"{self._get_internal_name()}: Sending request buffer to device"
                        )
                        await self._client.write_gatt_char(
                            CHARACTERISTIC_AUTH,
                            self._auth_data.generate_request_buffer(),
                        )
                    case AuthState.GOT_DEVICE_KEY:
                        logger.debug(
                            f"{self._get_internal_name()}: Sending auth request"
                        )
                        await self._client.write_gatt_char(
                            CHARACTERISTIC_AUTH,
                            self._auth_data.get_request_for_auth_level(1),
                        )
                    case AuthState.AUTH_SUCCESS:
                        logger.info(
                            f"{self._get_internal_name()}: Auth finished. Exiting"
                        )
                        break
                    case _:
                        logger.warning(
                            f"{self._get_internal_name()}: Unknown state value"
                        )

            await self._client.stop_notify(CHARACTERISTIC_AUTH)
            await self._client.stop_notify(CHARACTERISTIC_AUTH_AND_SERVICE)
        except Exception as e:
            logger.error(e)

    @require_auth
    async def get_state(self) -> DeviceState:
        data = await self._client.read_gatt_char(CHARACTERISTIC_DEVICE_STATE)
        return DeviceState(self._auth_data.name, data)

    @require_auth
    async def set_state(self, state: DeviceState) -> None:
        await self._client.write_gatt_char(CHARACTERISTIC_DEVICE_STATE, state.hex_value)

    @require_auth
    async def get_device_info(self) -> BonecoDeviceInfo:
        data = await self._client.read_gatt_char(CHARACTERISTIC_DEVICE_INFO)
        return BonecoDeviceInfo(data)

    @require_auth
    async def get_device_name(self) -> str:
        data = await self._client.read_gatt_char(CHARACTERISTIC_DEVICE_NAME)
        return data.strip(b"\x00").decode()

    def _get_internal_name(self) -> str:
        return f"{self._auth_data.device.name} ({self._auth_data.device.address})"

    async def _ensure_connected(self) -> None:
        if self._client and self._client.is_connected:
            logger.debug(f"{self._get_internal_name()}: Already connected")
            return
        await self.connect
