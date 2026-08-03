# UNO firmware

The factory TB6612 firmware remains recoverable from the parent vendor material.

The active project baseline is the original ELEGOO TB6612 firmware in the
parent vendor directory. Python communicates with that firmware using its
factory `N=2`, `N=21`, `N=22`, and `N=100` commands.

`HullRakshakUno/HullRakshakUno.ino` is an **inactive experimental artifact**.
It is retained only for engineering history and must not be uploaded during
factory-baseline commissioning. It is not compatible with the active Python
control protocol and has not passed physical motor validation.
