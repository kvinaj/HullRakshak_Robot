<<<<<<< HEAD
# HullRakshak Foundation

This project turns the ELEGOO Conqueror tank into a controlled learning
platform for telemetry, safe teleoperation, feedback control, and gradual
autonomy.

The original ELEGOO files in the parent directory remain untouched and serve as
the vendor reference. This directory contains only our maintainable code.

## Current milestone

Milestone 1 is deliberately read-only:

- connect to the UNO over USB serial;
- stop the robot when the connection opens and closes;
- read all three line sensors;
- read the ultrasonic distance;
- print timestamped telemetry.

No firmware upload or motor movement is required.

## Run the sensor monitor

Close Arduino Serial Monitor first because only one application can own the
serial port at a time.

```bash
cd "/Users/vinaykamuju/Documents/Sensor_Tutorials/Elegro Robot/hullrakshak_foundation"
source .venv/bin/activate
hullrakshak-sensors
```

The program discovers the UNO automatically. An explicit port can be supplied:

```bash
hullrakshak-sensors --port /dev/cu.usbserial-10
```

Stop it with `Ctrl+C`.

To record every displayed sample for later analysis:

```bash
hullrakshak-sensors \
  --port /dev/cu.usbserial-10 \
  --log data/logs/first_session.csv
```

CSV rows are flushed immediately so completed samples survive a later
communication or program failure.

To display the calibrated surface classification:

```bash
hullrakshak-sensors --port /dev/cu.usbserial-10 --classify
```

The measured per-sensor centers, thresholds, and polarity are stored in
`config/calibration.toml`.

## Project layout

```text
config/                  Runtime and calibration settings
docs/                    Architecture, protocol, pinout, and safety notes
firmware/                Future maintainable UNO and ESP32 firmware
host/src/hullrakshak/    Python control and telemetry package
tests/                   Hardware-independent automated tests
data/                    Generated logs and calibration results
```

## Roadmap

1. Read-only telemetry and sensor calibration.
2. Time-limited low-speed motor commands.
3. Keyboard teleoperation with a dead-man control.
4. Session logging and visualization.
5. Wi-Fi transport through the ESP32.
6. Safer, non-blocking UNO firmware.
7. Encoders, closed-loop track-speed control, and assisted driving.
8. HullRakshak inspection sensors and mission behaviours.
=======
# HullRakshak_Robot
>>>>>>> f9ef5acfcfe7ca5ee3822383d003147d71c524d7
