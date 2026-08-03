# Control system

## Safe timed-motion command

The host API currently exposes the factory protocol's time-limited command:

```python
robot.drive_timed(
    MotionDirection.FORWARD,
    speed=60,
    duration_ms=250,
)
```

Default host limits:

- maximum commissioning PWM: 80 out of 255;
- maximum command duration: 500 ms;
- keyboard pulse: 250 ms.

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
  --speed 60 \
  --arm
```

Do not run this until both tracks are physically raised.

## First movement: one pulse

The first physical movement should not use keyboard control. Use the dedicated
one-shot tool with raised tracks:

```bash
hullrakshak-pulse \
  --transport serial \
  --port /dev/cu.usbserial-10 \
  --direction forward \
  --speed 50 \
  --duration-ms 200 \
  --arm
```

It requires the same `RAISED` confirmation, sends exactly one time-limited
command, waits for it to expire, sends stop, and exits. Validate forward,
backward, left, and right in separate runs.

## Operating states

The host supports `safe`, `manual`, `assisted`, `autonomous`, and `fault`.
Changing directly between active modes is forbidden; the controller must
return to `safe` first. A fault must also return through `safe` before movement
can be enabled again.
