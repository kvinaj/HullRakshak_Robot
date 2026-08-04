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

## Initial floor tests verified on 2026-08-04

- One forward floor pulse at PWM 100 for 500 ms moved approximately 10 cm,
  curved very slightly left, and stopped automatically.
- A separately armed forward-only floor pulse at PWM 100 for 1500 ms moved
  approximately 20 cm, ended about 1 cm left of the projected straight line,
  and stopped automatically.
- Three consecutive 1500 ms repeatability trials each travelled approximately
  20.5 cm, placed the front about 1 cm left of the projected straight line, and
  stopped automatically. The repeatable heading deviation is approximately
  2.8 degrees over 20.5 cm.
- The longer floor-test ceiling is isolated from normal motion: floor mode is
  capped at 1500 ms while normal and raised-track motion remain capped at
  500 ms.

The slight left drift is now repeatable enough for a future measured correction;
no correction has been applied yet. Autonomous actuation remains untested.

## Reverse floor baseline verified on 2026-08-04

- Three consecutive backward floor trials at PWM 100 for 1500 ms each travelled
  approximately 20.5 cm and stopped automatically.
- The robot showed approximately 1 cm of heading deviation in the direction
  opposite to the forward deviation.
- Forward and backward therefore have matching travel distance and a repeatable
  direction-reversing bias. This is consistent with a small left/right track
  speed mismatch; it is not evidence of random command loss.
- Floor mode now permits forward and backward only, with direction-specific
  clearance and USB-cable instructions. Floor turning remains prohibited.

Mechanical track resistance and tension should be checked before choosing a
software differential-speed correction.
