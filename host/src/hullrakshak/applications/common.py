"""Shared application connection arguments."""

from __future__ import annotations

import argparse
from dataclasses import replace

from hullrakshak.robot import Robot
from hullrakshak.settings import Settings


def add_connection_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--transport",
        choices=("serial", "wifi", "simulated"),
        default="serial",
        help="Robot connection type (default: %(default)s)",
    )
    parser.add_argument("--port", help="Override serial port auto-discovery")
    parser.add_argument("--host", help="Override robot Wi-Fi host")


def apply_connection_overrides(
    settings: Settings, args: argparse.Namespace
) -> Settings:
    if getattr(args, "port", None):
        settings = replace(
            settings,
            serial=replace(settings.serial, port=args.port),
        )
    if getattr(args, "host", None):
        settings = replace(
            settings,
            wifi=replace(settings.wifi, host=args.host),
        )
    return settings


def connect_robot(settings: Settings, transport_name: str) -> Robot:
    if transport_name == "wifi":
        return Robot.connect_wifi(settings)
    if transport_name == "simulated":
        return Robot.connect_simulated(settings)
    return Robot.connect_serial(settings)
