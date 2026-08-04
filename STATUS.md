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

## Recommissioning verified on 2026-08-03

- The exact factory TB6612 hex was written and all 31,500 bytes were verified.
- USB telemetry at 9600 baud returned line and ultrasonic sensor readings.
- With motor power on, the robot remained stopped while idle.
- Factory stop command `{"N":100}` returned `{ok}`.
- Direct factory `N=4` tests identified `D1` as the right track and `D2` as the
  left track; each channel and both channels together moved and stopped.
- PWM 80 moved the right track but did not reliably start the left track.
- PWM 100 reliably started both raised tracks in the same direction.
- Factory timed command `N=2`, forward, PWM 100, 500 ms returned
  `{FORWARD_ok}`; both tracks moved and stopped.
- The normal `hullrakshak-pulse` Python path repeated that physical result.
- The active commissioning limit is therefore PWM 100 and 500 ms.

## Direction tests verified on 2026-08-04

After fully charging the robot batteries, one bounded raised-track test passed
in each direction at PWM 100 for 500 ms:

- forward: both tracks forward, then automatic stop;
- backward: both tracks backward, then automatic stop;
- left: right track forward and left track backward, then automatic stop;
- right: left track forward and right track backward, then automatic stop.

The earlier intermittent pivot behavior occurred before charging and did not
recur in this four-direction sequence. This is consistent with insufficient
motor-supply charge, but battery voltage was not measured directly.

Floor operation and autonomous actuation remain untested.
