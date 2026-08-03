# HullRakshak Robot Foundation

This project turns the ELEGOO Conqueror tank into a controlled learning
platform for telemetry, safe teleoperation, feedback control, and gradual
autonomy.

The original ELEGOO files in the parent directory remain untouched and serve as
the vendor reference. This directory contains only our maintainable code.

## Current status

Previously demonstrated on hardware:

- macOS USB connection to the UNO at 9600 baud;
- stop command on connection entry and exit;
- left, middle, and right line-sensor telemetry;
- ultrasonic distance telemetry;
- timestamped CSV logging;
- measured light/dark classification;
- bounded USB and Wi-Fi motor control;
- raised-track keyboard teleoperation.

Implemented and automatically tested:

- bounded, self-expiring motion commands;
- explicitly armed keyboard teleoperation;
- ESP32 Wi-Fi transport and heartbeat;
- operating-state transitions and fault state;
- obstacle-guard and conservative line-following decisions;
- simulated robot transport;
- repeatable interactive calibration.

The project is currently being recommissioned from a factory-firmware baseline.
Historical demonstrations are recorded, but motor operation must be revalidated
in order from powered idle through a single raised-track pulse. Experimental
UNO firmware is inactive and must not be uploaded during this baseline.

See [STATUS.md](STATUS.md) for the exact validation boundary.

## Environment

```bash
cd "/Users/vinaykamuju/Documents/Sensor_Tutorials/Elegro Robot/hullrakshak_foundation"
source .venv/bin/activate
```

Close Arduino Serial Monitor before using the USB port.

## Sensor monitor

```bash
hullrakshak-sensors --port /dev/cu.usbserial-10 --classify
```

Record every displayed sample:

```bash
hullrakshak-sensors \
  --port /dev/cu.usbserial-10 \
  --classify \
  --log data/logs/session.csv
```

## Simulated robot

Develop and verify applications without opening a hardware port:

```bash
hullrakshak-sensors --transport simulated --once --classify
```

## Calibration

The current measured calibration is stored in `config/calibration.toml`.
Interactive recalibration refuses to overwrite it unless explicitly requested:

```bash
hullrakshak-calibrate \
  --port /dev/cu.usbserial-10 \
  --samples 20 \
  --overwrite
```

## Teleoperation

Read [docs/controls.md](docs/controls.md) and [docs/safety.md](docs/safety.md)
before the first physical motion test. Teleoperation is disarmed unless
`--arm` is supplied, then requires typing `RAISED` interactively.

The first movement test uses `hullrakshak-pulse`, not keyboard teleoperation.

## Project layout

```text
config/                  Runtime and calibration settings
docs/                    Architecture, protocol, pinout, and safety notes
firmware/                Future maintainable UNO and ESP32 firmware
host/src/hullrakshak/    Python control and telemetry package
tests/                   Hardware-independent automated tests
data/                    Generated logs and calibration results
```

## Tests

```bash
make check
make simulate
```

The repository also includes a GitHub Actions workflow for hardware-independent
tests.

## Roadmap

1. Read-only telemetry and sensor calibration.
2. Time-limited low-speed motor commands.
3. Keyboard teleoperation with self-expiring pulses.
4. Session logging and visualization.
5. Wi-Fi transport through the ESP32.
6. Safer, non-blocking UNO firmware.
7. Encoders, closed-loop track-speed control, and assisted driving.
8. HullRakshak inspection sensors and mission behaviours.
