# Validation status

## Previously demonstrated on the physical TB6612 robot

- macOS USB port `/dev/cu.usbserial-10`
- factory firmware at 9600 baud
- stop command
- left, middle, and right line-sensor requests
- ultrasonic distance request
- continuous Python telemetry
- CSV session logging
- measured light/dark classification
- bounded USB motor pulses in all four directions
- raised-track USB keyboard teleoperation
- Wi-Fi sensor telemetry through the ESP32 bridge
- bounded Wi-Fi movement and keyboard teleoperation

## Verified automatically

- fragmented and concatenated protocol frames
- safe command encoding
- speed and duration bounds
- stop on API context entry and exit
- telemetry through a simulated robot
- CSV schema
- calibration derivation and round-trip storage
- explicit state-transition rules
- obstacle-guard decisions
- conservative line-following decisions
- ESP32 heartbeat response and frame queuing

## Current recommissioning boundary

- The repository is standardized on factory UNO protocol `N=2`.
- The exact firmware currently loaded on the UNO has not been independently
  identified in the new commissioning sequence.
- Historical motor results do not substitute for a fresh controlled baseline.
- No physical motor command is authorized until firmware identity, USB
  telemetry, and powered-idle checks are recorded again in order.
- Autonomous actuation remains untested.

Recommissioning must proceed in order. The first future motion test must use
raised tracks, speed 60 or lower, a 250 ms pulse, and immediate physical access
to the power switch.
