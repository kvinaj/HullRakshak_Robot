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
class WifiSettings:
    host: str
    port: int
    connect_timeout_seconds: float
    response_timeout_seconds: float


@dataclass(frozen=True)
class SafetySettings:
    maximum_initial_speed: int
    maximum_command_duration_ms: int
    maximum_floor_test_duration_ms: int
    maximum_differential_floor_test_duration_ms: int
    teleop_pulse_duration_ms: int
    assisted_pulse_duration_ms: int
    assisted_medium_distance_cm: int
    assisted_medium_pulse_duration_ms: int
    assisted_near_distance_cm: int
    assisted_near_pulse_duration_ms: int
    maximum_assisted_run_seconds: float
    obstacle_stop_distance_cm: int


@dataclass(frozen=True)
class DriveSettings:
    forward_trim_enabled: bool
    forward_left_pwm: int
    forward_right_pwm: int
    reverse_trim_enabled: bool
    reverse_left_pwm: int
    reverse_right_pwm: int


@dataclass(frozen=True)
class Settings:
    serial: SerialSettings
    monitor: MonitorSettings
    wifi: WifiSettings
    safety: SafetySettings
    drive: DriveSettings


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
        wifi=WifiSettings(
            host=str(raw["wifi"]["host"]),
            port=int(raw["wifi"]["port"]),
            connect_timeout_seconds=float(raw["wifi"]["connect_timeout_seconds"]),
            response_timeout_seconds=float(raw["wifi"]["response_timeout_seconds"]),
        ),
        safety=SafetySettings(
            maximum_initial_speed=int(raw["safety"]["maximum_initial_speed"]),
            maximum_command_duration_ms=int(
                raw["safety"]["maximum_command_duration_ms"]
            ),
            maximum_floor_test_duration_ms=int(
                raw["safety"]["maximum_floor_test_duration_ms"]
            ),
            maximum_differential_floor_test_duration_ms=int(
                raw["safety"]["maximum_differential_floor_test_duration_ms"]
            ),
            teleop_pulse_duration_ms=int(
                raw["safety"]["teleop_pulse_duration_ms"]
            ),
            assisted_pulse_duration_ms=int(
                raw["safety"]["assisted_pulse_duration_ms"]
            ),
            assisted_medium_distance_cm=int(
                raw["safety"]["assisted_medium_distance_cm"]
            ),
            assisted_medium_pulse_duration_ms=int(
                raw["safety"]["assisted_medium_pulse_duration_ms"]
            ),
            assisted_near_distance_cm=int(
                raw["safety"]["assisted_near_distance_cm"]
            ),
            assisted_near_pulse_duration_ms=int(
                raw["safety"]["assisted_near_pulse_duration_ms"]
            ),
            maximum_assisted_run_seconds=float(
                raw["safety"]["maximum_assisted_run_seconds"]
            ),
            obstacle_stop_distance_cm=int(
                raw["safety"]["obstacle_stop_distance_cm"]
            ),
        ),
        drive=DriveSettings(
            forward_trim_enabled=bool(raw["drive"]["forward_trim_enabled"]),
            forward_left_pwm=int(raw["drive"]["forward_left_pwm"]),
            forward_right_pwm=int(raw["drive"]["forward_right_pwm"]),
            reverse_trim_enabled=bool(raw["drive"]["reverse_trim_enabled"]),
            reverse_left_pwm=int(raw["drive"]["reverse_left_pwm"]),
            reverse_right_pwm=int(raw["drive"]["reverse_right_pwm"]),
        ),
    )
