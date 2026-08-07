# Assisted and autonomous decision layer

The assisted-control module contains pure decision logic. The separately armed
`hullrakshak-assisted-forward` application can apply that guard to movement
using adaptive self-expiring pulses and a 60-second maximum runtime. Pulses are
250 ms above 30 cm, 150 ms from 30 cm through 21 cm, and 75 ms from 20 cm down
to the 15 cm stop threshold. It requires
untethered Wi-Fi floor-test mode and calibrated differential firmware.

The stationary guard diagnostic cannot move
hardware by itself, which allows it to be thoroughly tested first.

## Obstacle guard

- Forward motion is rejected when a valid ultrasonic reading is at or below
  the configured 15 cm stop distance.
- Reverse and turn commands remain available so the operator can retreat.
- A zero reading is treated as invalid and causes a fail-safe stop; future UNO
  firmware should expose validity explicitly.

## Conservative line following

- Middle dark, sides light: request forward.
- Left dark: request left.
- Right dark: request right.
- All dark: stop.
- No dark sensor: request a search state, but do not move automatically.

This is deliberately more conservative than the vendor blind-search routine.
Search motion remains disabled until loss-of-line behaviour is logged and
tested in a bounded environment.

## Separation of sensing and actuation

```text
sample -> validate -> classify -> decide -> safety guard -> bounded command
```

Every stage produces inspectable data. A decision never writes directly to
motor pins.
