# TB6612 robot pinout

| UNO pin | Function |
|---|---|
| D2 | Mode button |
| D3 | TB6612 standby |
| D4 | WS2812 RGB LED |
| D5 | Motor A PWM |
| D6 | Motor B PWM |
| D7 | Motor A direction |
| D8 | Motor B direction |
| D9 | Infrared receiver |
| D10 | Servo Z |
| D11 | Servo Y |
| D12 | Ultrasonic echo |
| D13 | Ultrasonic trigger |
| A0 | Right line sensor |
| A1 | Middle line sensor |
| A2 | Left line sensor |
| A3 | Battery voltage |
| A4/A5 | MPU6050 I2C |

This mapping is for the confirmed TB6612 expansion board. Do not substitute the
DRV8835 firmware because its motor direction mapping and timer behaviour differ.
