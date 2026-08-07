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

## Untethered Wi-Fi floor control verified on 2026-08-04

- Wi-Fi telemetry through the ESP32 bridge returned line and ultrasonic data.
- One raised-track Wi-Fi forward pulse at PWM 100 for 500 ms moved both tracks
  and stopped automatically.
- With USB disconnected, one Wi-Fi forward floor pulse at PWM 100 for 1500 ms
  travelled approximately 20.5 cm, reproduced the approximately 1 cm leftward
  front deviation, and stopped automatically.
- Matching USB and Wi-Fi floor results confirm that the measured drift is not
  caused by the host transport.

Wi-Fi keyboard control must be recommissioned with raised tracks before any
floor teleoperation.

## Wi-Fi keyboard control verified on 2026-08-04

- With tracks raised, Up, Down, Left, and Right produced the expected track
  directions using 250 ms self-expiring pulses at PWM 100.
- Every raised-track key pulse stopped automatically; Space sent stop and Q
  sent stop and exited normally.
- Wi-Fi-only floor teleoperation was then verified with USB disconnected,
  `--floor-test`, and the `CLEAR` confirmation.
- A single floor Up-arrow pulse moved and stopped correctly; Space and Q also
  worked. The previously measured slight drivetrain drift remained present.
- Serial floor teleoperation is intentionally rejected.

Manual computer control over Wi-Fi is now commissioned. Straight-line drift
correction remains the next control-development milestone.

## Differential firmware candidate compiled on 2026-08-04

- The inactive UNO candidate preserves `N=2`, `N=21`, `N=22`, and `N=100`.
- It adds a read-only `N=41` capability probe and locally time-limited signed
  left/right PWM command `N=40`.
- Raw signed PWM and duration fields are range-checked before conversion.
- The candidate compiles for Arduino UNO using 7,046 bytes (21%) of flash and
  394 bytes (19%) of RAM.
- Nothing was uploaded; the robot remains on the verified factory firmware.

Python capability detection and refusal-by-default are now implemented:

- `probe_differential_capability()` sends read-only `N=41` and enables the
  capability only after receiving exact frame `{CAP_1}` on that connection.
- Opening or closing a connection clears the verified capability.
- `drive_differential_timed()` validates signed PWM and duration first, then
  refuses to write `N=40` unless the current connection passed the probe.
- Automated tests prove a factory-like transport never receives `N=40`, while
  a verified candidate receives the exact bounded differential frame.

The next gate is a read-only probe against the currently installed factory
firmware. No candidate upload or differential motor test has occurred.

## Differential control and obstacle guard verified by 2026-08-07

- The custom UNO firmware was uploaded, and its `{CAP_1}` capability response
  and bounded differential command were physically verified.
- Straight-motion calibration is left PWM 100 and right PWM 86. Forward uses
  `100/86`; reverse uses the signed pair `-100/-86`.
- Normal cabled Python forward and reverse floor pulses used those calibrated
  values successfully and stopped automatically. The corresponding calibrated
  Wi-Fi commands have not been physically repeated after the final change.
- Ultrasonic measurements were approximately 219 cm with an open path, 19 cm
  for an object placed at 20 cm, and 9 cm for an object placed at 10 cm.
- The stationary obstacle guard was physically verified: repeated 9 cm readings
  produced `STOP`, while 33--38 cm readings produced `CLEAR`, using the
  configured 15 cm threshold.
- The diagnostic remains read-only: it commands stop on connection entry and
  exit and never sends a movement command.

The next safety gate is an explicitly armed, bounded assisted-forward test that
checks the ultrasonic distance before permitting a single motion pulse.
