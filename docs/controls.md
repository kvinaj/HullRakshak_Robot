# Control system

## Safe timed-motion command

The host API currently exposes the factory protocol's time-limited command:

```python
robot.drive_timed(
    MotionDirection.FORWARD,
    speed=100,
    duration_ms=500,
)
```

Default host limits:

- maximum commissioning PWM: 100 out of 255;
- maximum command duration: 500 ms;
- explicitly armed straight floor-test duration: 1500 ms;
- keyboard pulse: 250 ms.

Measured forward trim is stored in `config/robot.toml`: left PWM 100 and right
PWM 87. Forward one-shot and keyboard commands use this differential pair only
after the current connection returns `{CAP_1}`. Reverse and turning commands
continue using the locally timed direction command. Missing capability causes
refusal, never an untrimmed fallback.

Values outside these limits raise an exception before serial or Wi-Fi output.
The API sends factory `N=2`. It never sends the factory firmware's indefinite
`N=3` or `N=4` command.

## Keyboard control

The controller is intentionally difficult to start accidentally:

1. `--arm` must be supplied.
2. An interactive terminal is required.
3. The operator must type `RAISED`.
4. Each movement key sends only a self-expiring pulse.
5. Space sends stop.
6. Q sends stop and exits.
7. Normal exit and exceptions both send stop.

| Key | Action |
|---|---|
| W / Up | Forward pulse |
| S / Down | Backward pulse |
| A / Left | Left pulse |
| D / Right | Right pulse |
| Space | Immediate stop |
| Q | Stop and quit |

First hardware run:

```bash
hullrakshak-teleop \
  --transport serial \
  --port /dev/cu.usbserial-10 \
  --speed 100 \
  --arm
```

Do not run this until both tracks are physically raised.

After raised-track Wi-Fi keyboard control passes, floor teleoperation can be
armed only over Wi-Fi. It uses the same self-expiring 250 ms key pulses,
requires two metres clear all around, no attached USB cable, and typing
`CLEAR`:

```bash
hullrakshak-teleop \
  --transport wifi \
  --host 192.168.4.1 \
  --speed 100 \
  --floor-test \
  --arm
```

## First movement: one pulse

The first physical movement should not use keyboard control. Use the dedicated
one-shot tool with raised tracks:

```bash
hullrakshak-pulse \
  --transport serial \
  --port /dev/cu.usbserial-10 \
  --direction forward \
  --speed 100 \
  --duration-ms 500 \
  --arm
```

It requires the same `RAISED` confirmation, sends exactly one time-limited
command, waits for it to expire, sends stop, and exits. Validate forward,
backward, left, and right in separate runs.

## First floor movement

Floor testing is a separate mode and never accepts the raised-track
confirmation. Floor mode permits forward and backward only and requires typing
`CLEAR` after checking the direction-specific clear area and USB cable route:

```bash
hullrakshak-pulse \
  --transport serial \
  --port /dev/cu.usbserial-10 \
  --direction forward \
  --speed 100 \
  --duration-ms 1500 \
  --floor-test \
  --arm
```

## Operating states

The host supports `safe`, `manual`, `assisted`, `autonomous`, and `fault`.
Changing directly between active modes is forbidden; the controller must
return to `safe` first. A fault must also return through `safe` before movement
can be enabled again.
