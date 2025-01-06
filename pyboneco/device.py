from typing import Optional

from .enums import OperationMode, ModeStatus

OperationModeConfig = Optional[dict[ModeStatus, bool]]


class BonecoDevice:
    device_type: int
    product_id: str
    product_name: str
    operating_modes: dict[OperationMode, OperationModeConfig]
    device_timer_support: bool
    history_support: bool
    particle_sensor: bool

    @staticmethod
    def is_device_air_fan(model: str):
        return model in ["F225", "F235"]

    @staticmethod
    def has_service_operating_counter(model: str):
        return model in ["H700", "H700 US"]

    @staticmethod
    def has_device_history_support(model: str):
        return model in ["H700", "H700 US"]

    def __init__(
        self,
        device_type: int,
        product_id: str,
        product_name,
        operating_modes: dict[OperationMode, OperationModeConfig],
        device_timer_support: bool = False,
        history_support: bool = False,
        particle_sensor: bool = False,
    ) -> None:
        self.device_type = device_type
        self.product_id = product_id
        self.product_name = product_name
        self.operating_modes = operating_modes
        self.device_timer_support = device_timer_support
        self.history_support = history_support
        self.particle_sensor = particle_sensor


class BonecoAirFanDevice(BonecoDevice):
    def __init__(self, device_type: int, product_id: str, product_name: str) -> None:
        super().__init__(
            device_type,
            product_id,
            product_name,
            dict(
                {
                    OperationMode.HUMIDIFIER: None,
                    OperationMode.PURIFIER: None,
                    OperationMode.HYBRID: None,
                }
            ),
        )


class BonecoHumidifierDevice(BonecoDevice):
    def __init__(self, device_type: int, product_id: str, product_name: str) -> None:
        super().__init__(
            device_type,
            product_id,
            product_name,
            dict(
                {
                    OperationMode.HUMIDIFIER: {
                        ModeStatus.CUSTOM: True,
                        ModeStatus.AUTO: True,
                        ModeStatus.BABY: True,
                        ModeStatus.SLEEP: True,
                    },
                    OperationMode.PURIFIER: None,
                    OperationMode.HYBRID: None,
                }
            ),
        )


class BonecoSimpleClimateDevice(BonecoDevice):
    def __init__(self, device_type: int, product_id: str, product_name: str) -> None:
        super().__init__(
            device_type,
            product_id,
            product_name,
            dict(
                {
                    OperationMode.HUMIDIFIER: {
                        ModeStatus.CUSTOM: True,
                        ModeStatus.AUTO: True,
                        ModeStatus.BABY: True,
                        ModeStatus.SLEEP: True,
                    },
                    OperationMode.PURIFIER: {
                        ModeStatus.CUSTOM: True,
                        ModeStatus.AUTO: False,
                        ModeStatus.BABY: False,
                        ModeStatus.SLEEP: False,
                    },
                    OperationMode.HYBRID: {
                        ModeStatus.CUSTOM: True,
                        ModeStatus.AUTO: True,
                        ModeStatus.BABY: True,
                        ModeStatus.SLEEP: True,
                    },
                }
            ),
        )


class BonecoTopClimateDevice(BonecoDevice):
    def __init__(self, device_type: int, product_id: str, product_name: str) -> None:
        super().__init__(
            device_type,
            product_id,
            product_name,
            dict(
                {
                    OperationMode.HUMIDIFIER: {
                        ModeStatus.CUSTOM: True,
                        ModeStatus.AUTO: True,
                        ModeStatus.BABY: True,
                        ModeStatus.SLEEP: True,
                    },
                    OperationMode.PURIFIER: {
                        ModeStatus.CUSTOM: True,
                        ModeStatus.AUTO: True,
                        ModeStatus.BABY: True,
                        ModeStatus.SLEEP: True,
                    },
                    OperationMode.HYBRID: {
                        ModeStatus.CUSTOM: True,
                        ModeStatus.AUTO: True,
                        ModeStatus.BABY: True,
                        ModeStatus.SLEEP: True,
                    },
                }
            ),
            device_timer_support=True,
            history_support=True,
            particle_sensor=True,
        )
