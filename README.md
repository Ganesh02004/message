🌐 ESP32 Hub Chat

A real-time local network chat system powered by ESP32 (MicroPython) and a browser-based modern UI.
This project turns your ESP32 into a lightweight HTTP server that supports:

✔ Multiple chat rooms
✔ Password-protected rooms
✔ User presence (online list)
✔ Real-time updates (polling)
✔ Web UI with animations
✔ Works on any phone or computer connected to same Wi-Fi

🚀 Features
Server (ESP32 with MicroPython)

Lightweight HTTP REST API

Create / list chat rooms

Optional room password (key)

Join / leave rooms

Send + receive messages

Automatic stale connection cleanup

Stores last 100 messages per room

Auto-generated connection ID for each client

CORS enabled (works on local browsers)

Web Client (HTML / JS)

A modern responsive UI:

Connect to ESP32 by entering IP address

Choose username

Browse available rooms

Create new room

Join room

Real-time chat

Online users list

Auto-polling for new messages

Smooth animations and clean design

🛠 Requirements
Hardware

ESP32 board (recommended: ESP32 DevKit, ESP32-WROOM, ESP32-S3)
❌ ESP8266 NOT recommended — not enough memory

Software

MicroPython firmware

ampy or mpremote to upload files

A device connected to the same Wi-Fi as the ESP32

📡 How It Works

The ESP32 runs a MicroPython script that:

Connects to your Wi-Fi network

Starts an HTTP server on port 80

Handles REST API endpoints for:

Registering a connection

Creating rooms

Joining rooms

Sending messages

Fetching new messages/users

Stores all chat data in RAM

The browser UI communicates with ESP32 using fetch() over HTTP.

📁 Project File Structure
/ESP32-Hub-Chat
   ├── esp32_server.py     # MicroPython chat server
   ├── index.html          # Web user interface
   └── README.md           # Documentation

🔧 Installation
1️⃣ Flash MicroPython

Download firmware from:
https://micropython.org/download/esp32/

Flash using:

esptool.py --chip esp32 erase_flash
esptool.py --chip esp32 write_flash -z 0x1000 firmware.bin

2️⃣ Upload Server Code

Using mpremote:

mpremote connect ttyUSB0 fs put esp32_server.py


Or using ampy:

ampy put esp32_server.py

3️⃣ Edit Wi-Fi Credentials

Inside esp32_server.py:

SSID = "YOUR_WIFI_SSID"
PASSWORD = "YOUR_WIFI_PASSWORD"

4️⃣ Run the Server

Open REPL:

mpremote connect ttyUSB0 repl


And run:

import esp32_server


It will print:

WiFi Connected!
Server running on: 192.168.x.x

5️⃣ Open the Web Interface

Open index.html on your PC or phone.

Enter the ESP32 IP (ex: 192.168.1.100)
→ Press Connect

🖥 API Reference
GET /api/rooms

Returns list of all chat rooms.

POST /api/rooms/create

Create a new chat room.

POST /api/register

Get a new connection ID.

POST /api/join

Join a chat room.

POST /api/message

Send a message.

POST /api/updates

Poll for new messages + online users.

POST /api/leave

Leave room.

GET /api/health

Check server status.

⚠ Limitations

ESP32 RAM is limited → supports ~5–20 users depending on message traffic

Because HTTP polling is used, rapid polling may slow the ESP32

Messages and room list reset on reboot

📌 Recommended Improvements (Optional)

Use WebSockets instead of HTTP (faster + fewer requests)

Store rooms/messages in flash (FS)

Add encryption (AES) for room keys

Add avatars or colors for users

Add admin interface

🧪 Tested On

ESP32-WROOM DevKit

MicroPython v1.21+

Chrome, Edge, Firefox, Mobile browsers
