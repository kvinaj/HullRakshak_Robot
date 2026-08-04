# Testing

Run the hardware-independent suite:

```bash
cd "/Users/vinaykamuju/Documents/Sensor_Tutorials/Elegro Robot/hullrakshak_foundation"
source .venv/bin/activate
python -m unittest discover -s tests -v
```

Run one simulated telemetry sample:

```bash
hullrakshak-sensors --transport simulated --once --classify
```

Hardware tests are sequential:

1. USB read-only telemetry.
2. One raised-track timed pulse.
3. Four raised-track directions.
4. Raised-track keyboard control.
5. Low-speed floor control in a clear area.
6. Read-only Wi-Fi telemetry.
7. Wi-Fi manual control.
8. Assisted control.

Passing a later software test never substitutes for the preceding physical
safety test.

## Raw timed-motion diagnostic

Use only with both tracks securely raised and the physical power switch within
reach:

```bash
hullrakshak-serial-diagnostic \
  --port /dev/cu.usbserial-10 \
  --arm
```

The command requires typing `RAISED`. It waits for the configured UNO startup
delay, sends a startup stop, then sends the fixed factory command `N=2`, forward,
speed 80, and 500 ms. It prints timestamped raw transmitted and received bytes,
plus complete brace-delimited frames, for three seconds. A final `N=100` stop is
sent on normal exit, exception, or Ctrl+C before the serial port is closed.

## Differential raised-track diagnostic

`hullrakshak-differential-pulse` validates signed left/right PWM and duration,
requires `--arm` plus the interactive `RAISED` confirmation, and probes `N=41`
before sending any `N=40` frame. Factory firmware is refused. Startup, normal
exit, exceptions, and Ctrl+C all pass through a stop-on-close robot context.

After an asymmetric pair passes with raised tracks, `--floor-test` permits only
same-sign, nonzero PWM on both tracks for straight forward or reverse travel.
It uses a separate 3000 ms differential calibration ceiling and requires the
direction-specific `CLEAR` confirmation. Mixed signs and zero-track commands
are rejected. Normal floor pulses remain capped at 1500 ms and raised-track
pulses at 500 ms.
