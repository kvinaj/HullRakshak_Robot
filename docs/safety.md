# Safety rules

## Current commissioning milestone

- Keep Arduino Serial Monitor closed while Python owns the port.
- Keep the Upload/Cam switch in `Upload` for direct USB communication.
- The sensor monitor sends `N=100` when opening and closing the connection.
- Python movement remains explicitly armed and time-limited.
- Raised-track forward motion is verified at PWM 100 for 500 ms.
- Backward and turning directions still require sequential raised-track checks.

## Before motor-control work

- Raise both tracks clear of the bench.
- Keep the physical power switch within reach.
- Use only time-limited commands initially.
- Cap commissioning PWM at the measured value of 100 out of 255.
- Implement a local UNO command timeout before indefinite commands.
- Stop on program exit, communication failure, and `Ctrl+C`.
- Never rely on the computer as the only emergency-stop mechanism.

## Autonomy

Autonomous behaviour will be introduced only after manual control, telemetry,
logging, and local failsafes work independently. Each autonomy layer must be
able to transition immediately into a safe stopped state.
