# Assisted and autonomous decision layer

The current assisted-control module is pure decision logic. It cannot move
hardware by itself, which allows it to be thoroughly tested first.

## Obstacle guard

- Forward motion is rejected when a valid ultrasonic reading is at or below
  the configured 15 cm stop distance.
- Reverse and turn commands remain available so the operator can retreat.
- A zero reading is treated as invalid rather than as a zero-distance obstacle;
  future UNO firmware should expose validity explicitly.

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
