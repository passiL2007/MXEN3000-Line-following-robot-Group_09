# MXEN3000-Line-following-robot-Group_09

**Project Overview**

This project is a line-following robotic vehicle designed for autonomous motion using a Bang-Bang control strategy. The control system operates through the Arduino Nano, which communicates with DAC modules, op-amps, and a push-pull amplifier to drive two DC motors.

IR sensors continuously detect the track condition (black/white surface), and the controller adjusts motor speeds accordingly to maintain the path. The system integrates both hardware and software elements to achieve real-time responsiveness and stable navigation.

**Core Features**

_Bang-Bang Motion Control:_
Binary on/off logic that drives the motors based on sensor readings for fast, precise corrections.

_Dual Motor Speed Control:_
Independent left and right motor speed adjustment to improve turn handling.

_Smart Line Recovery:_
Memory-based recovery function that remembers which side lost the line first, helping the robot realign smoothly.
_
GUI Integration (Python):_
A custom graphical interface allows users to monitor sensor data, adjust speeds, and control the robot manually.

_Safety and Flexibility:_
Includes an emergency stop function and configurable settings (thresholds, baud rate, ports).

**How It Works**

The Arduino continuously reads IR sensor data (A6 = left, A7 = right).

Sensor readings are compared against a threshold to determine line position.

The control logic sends DAC output signals to regulate motor voltage.

The car adjusts its path — going straight, turning left/right, or performing recovery if off-track.

The GUI (Python) displays real-time data and allows manual control if needed.

**Usage Instructions**

Upload the Arduino sketch to the Nano using the Arduino IDE.

Connect IR sensors, DAC, op-amp, and motor driver as per the schematic.

Run the Python GUI to start communication.

Set desired thresholds and motor speeds in the interface.

Place the robot on the track and activate Autonomous Mode.

Authors

Group_09 – Curtin University Colombo
Mechatronics Engineering – MXEN300 (2025)
