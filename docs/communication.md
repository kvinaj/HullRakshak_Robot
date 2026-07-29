# ELEGOO communication notes

The factory UNO firmware uses JSON commands at 9600 baud. Commands begin with
`{` and end with `}` without requiring a newline.

Examples:

```json
{"N":100}
{"N":22,"D1":0,"H":"L"}
{"N":21,"D1":2,"H":"U"}
```

- `N=100`: stop and enter standby.
- `N=22`: read one line sensor; `D1=0/1/2` selects left/middle/right.
- `N=21,D1=2`: read ultrasonic distance in centimetres.
- `H`: request identifier echoed in responses.

Example responses:

```text
{L_181}{M_193}{R_73}{U_42}
```

The decoder accepts fragmented or concatenated frames. This matters because
serial reads do not preserve message boundaries.

The factory ultrasonic implementation calls `pulseIn()` without an explicit
timeout. A missing echo can therefore delay its response by roughly one second;
the host uses a 2.5-second response deadline.

Opening the USB port resets the UNO. Its factory startup initializes the
servos, initializes and calibrates the MPU6050, and finally clears the serial
receive buffer. The host waits six seconds before sending its first command so
valid commands are not discarded during that startup sequence.

The ESP32 factory firmware exposes the same command stream on TCP port 100 and
bridges it to the UNO. It additionally requires the client to echo its
`{Heartbeat}` message.
