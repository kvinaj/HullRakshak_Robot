# ESP32 Wi-Fi transport

## Factory network

1. Upload mode routes USB serial to the UNO.
2. Cam mode connects the UNO UART to the ESP32.
3. The ESP32 creates an `ELEGOO-...` access point.
4. Its default address is `192.168.4.1`.
5. Robot commands use TCP port 100.
6. Camera HTTP endpoints are hosted separately.

The computer usually loses ordinary internet connectivity while attached to
the robot access point.

## Host implementation

`WifiTransport`:

- opens the TCP connection;
- continuously reads in a background thread;
- decodes fragmented or concatenated frames;
- immediately echoes `{Heartbeat}`;
- queues non-heartbeat responses for the Robot API;
- reports socket closure as a robot-connection fault.

Read-only Wi-Fi telemetry can later be tested with:

```bash
hullrakshak-sensors --transport wifi --once --classify
```

This command is implemented but not yet validated against the physical ESP32.
Wi-Fi motion should be attempted only after USB motion passes its raised-track
test.

## HullRakshak direction

The factory unencrypted access point is suitable for a laboratory learning
platform, not a deployed inspection robot. Later firmware should add
authentication, command sequence numbers, timestamps, expiry, structured
telemetry, and explicit connection/fault state.
