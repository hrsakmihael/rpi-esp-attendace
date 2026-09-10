# IoT Attendance System

IoT system for automating student attendance tracking and access control for classrooms.

This project was developed as part of a final thesis at the Faculty of Electrical Engineering, Computer Science and Information Technology Osijek.

The system uses:

* ESP8266 and MFRC522 RFID reader
* Servo motor as an electronic lock
* MQTT communication
* Raspberry Pi as the central server
* MySQL database
* Tornado web application

## Project Structure

* `sketch_apr28a.ino` – runs on ESP8266 connected to an MFRC522 and a servomotor that simulated an electric lock
* `mqtt/` – MQTT communication
* `web/` – web application and database management

everything besides the .ino is located on the Raspberry Pi 3 device that acts as a central server,
all components are connected to the local wifi network
