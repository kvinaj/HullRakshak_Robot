# UNO firmware

The factory TB6612 firmware remains recoverable from the parent vendor material.

The active project baseline is the original ELEGOO TB6612 firmware in the
parent vendor directory. Python communicates with that firmware using its
factory `N=2`, `N=21`, `N=22`, and `N=100` commands.

`HullRakshakUno/HullRakshakUno.ino` is an **inactive experimental candidate**.
It retains the active project's `N=2`, `N=21`, `N=22`, and `N=100` protocol,
and adds:

- `N=41`: read-only capability probe returning `{CAP_1}`;
- `N=40`: locally time-limited signed left/right PWM using `L`, `R`, and `T`.

Both signed PWM values are limited to -100..100 and duration to 1..3000 ms
before any narrowing conversion. Invalid or unknown commands stop the motors.
The motion deadline is enforced on the UNO, independently of Python or Wi-Fi.

This candidate must not be uploaded yet. It has not passed physical motor
validation, and active Python continues to use the verified factory firmware.
