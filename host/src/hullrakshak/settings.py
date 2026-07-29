"""Project configuration loading."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "robot.toml"


@dataclass(frozen=True)
class SerialSettings:
    port: str | None
    baudrate: int
    reset_delay_seconds: float
    response_timeout_seconds: float


@dataclass(frozen=True)
class MonitorSettings:
    interval_seconds: float


@dataclass(frozen=True)
class Settings:
    serial: SerialSettings
    monitor: MonitorSettings


def load_settings(path: Path = DEFAULT_CONFIG_PATH) -> Settings:
    with path.open("rb") as config_file:
        raw = tomllib.load(config_file)

    serial_config = raw["serial"]
    configured_port = serial_config.get("port", "").strip()
    return Settings(
        serial=SerialSettings(
            port=configured_port or None,
            baudrate=int(serial_config["baudrate"]),
            reset_delay_seconds=float(serial_config["reset_delay_seconds"]),
            response_timeout_seconds=float(
                serial_config["response_timeout_seconds"]
            ),
        ),
        monitor=MonitorSettings(
            interval_seconds=float(raw["monitor"]["interval_seconds"])
        ),
    )
