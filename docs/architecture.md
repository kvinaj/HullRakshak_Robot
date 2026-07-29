# Architecture

## Responsibility split

```text
Mac Python application
  - operator interface
  - telemetry display and logging
  - calibration
  - future high-level autonomy
          |
          | USB serial now; ESP32 TCP later
          v
UNO controller
  - motor output
  - immediate stop and command timeout
  - deterministic sensor sampling
  - future track-speed control
          |
          v
motors, servos, line sensors, ultrasonic sensor, MPU6050, battery monitor
```

The computer may request movement, but the embedded controller remains
responsible for enforcing safe bounds. A disconnected or crashed computer must
not leave the tracks running.

## Milestones

1. Read-only USB telemetry.
2. Sensor calibration and logging.
3. Time-limited low-speed movement.
4. Dead-man keyboard teleoperation.
5. Wi-Fi transport and video.
6. Maintainable UNO firmware and local failsafes.
7. Encoders and closed-loop track control.
8. Assisted and autonomous behaviours.
