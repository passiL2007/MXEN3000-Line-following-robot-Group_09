<img width="1063" height="598" alt="image" src="https://github.com/user-attachments/assets/c4af678a-3292-4af3-8dd0-b02e727087e0" />

This Graphical User Interface (GUI) is designed for controlling and monitoring an autonomous line-following robot built on Arduino hardware. Developed using Python (PyQt5), the interface provides a real-time connection between the robot’s sensors, DAC outputs, and motor control system.

The GUI integrates multiple advanced features — including live data visualization, system diagnostics, and an AI-based lab assistant — all within a single control window.

⚙️ Key Features

Real-Time Monitoring: Displays IR sensor readings, DAC outputs, and motor speed levels with continuous updates from the Arduino.

Dual Motor Meters: Analog gauges show independent left and right motor performance with voltage and byte values.

DAC Pin Visualizer: View live binary DAC outputs for both channels.

AI Terminal Assistant: Built-in assistant that answers technical questions and explains system components.

Multi-Mode Operation: Four configurable modes — Race, Precision, Power Saver, and Learning — for speed and performance control.

Stopwatch Timer: Measures lap time and total runtime for performance testing.

Safety System: Includes an emergency stop button and live connection status indicator.

🧩 System Integration

The GUI directly communicates with the Arduino control firmware through serial communication.
All essential commands and sensor feedback are processed within the GUI — no manual uploads or serial monitoring are required.
However, for standalone use, the robot can be run without the GUI by uploading the Arduino sketch directly.
Refer to the README instructions in this repository for detailed steps.
