# Smart Helmet System - Setup & Integration Guide

## Overview
This document explains the complete integration between:
- **Arduino/ESP32 (Final_Code.ino)** - Collects sensor data
- **Django Backend (monitoring app)** - Receives & stores data
- **Web Dashboard (dashboard.html)** - Displays data on graphs

---

## Step 1: Arduino Configuration

### File: `Final_Code/Final_Code.ino`

**Changes Made:**
✅ Updated WiFi credentials and server URL
✅ Fixed JSON payload structure
✅ Added proper device identification

**Key Configuration (Lines 18-23):**
```cpp
const char* ssid = "TASHINGA";
const char* password = "1234567890";

const char* servername = "http://192.168.1.100:8000/api/sensor-data/";
const char* device_id = "HELMET_001";  // UPDATE this for each helmet
```

**⚠️ IMPORTANT - BEFORE UPLOADING:**
1. Change `192.168.1.100` to your Django server's actual IP address
   - Find your server IP: Run `ipconfig` on Windows
   - Use an IP from the same network as your ESP32
   - Examples: `192.168.1.x`, `10.x.x.x`, `172.16.x.x`

2. Change `device_id` to a UNIQUE identifier for each helmet
   - Examples: `HELMET_001`, `HELMET_002`, `WORKER_Alice`, etc.
   - This ID must match a registered device in the Django database

### Data Being Sent
The Arduino now sends this JSON to the backend every 2 seconds:
```json
{
  "device_id": "HELMET_001",
  "heart_rate": 75,
  "spo2": 98.5,
  "gas_level": 250,
  "temperature": 25.3,
  "humidity": 55.2,
  "motion": 0.0,
  "latitude": 0.0,
  "longitude": 0.0
}
```

---

## Step 2: Django Backend Setup

### Database Migration

Run these commands in the backend directory:

```bash
# Navigate to backend folder
cd backend

# Activate virtual environment (if not already active)
venv\Scripts\activate.bat    # On Windows
source venv/bin/activate     # On Mac/Linux

# Apply database migrations
python manage.py migrate

# Create a superuser (if not already created)
python manage.py createsuperuser
```

### Register Helmet Devices

After migrating, register your devices in Django:

**Option A: Using Django Admin**
1. Start Django server: `python manage.py runserver 0.0.0.0:8000`
2. Go to: `http://YOUR_IP:8000/admin`
3. Login with superuser credentials
4. In "Monitoring" app → "Helmet Devices" → "Add Helmet Device"
5. Enter:
   - **Device ID**: Must match the `device_id` in Arduino code (e.g., `HELMET_001`)
   - **Worker**: (optional) Link to a worker
   - **Battery Level**: Leave as 100

**Option B: Using Python Shell**
```bash
python manage.py shell
```

```python
from monitoring.models import HelmetDevice

# Create device
HelmetDevice.objects.create(
    device_id='HELMET_001',
    battery_level=100
)

# Verify it was created
HelmetDevice.objects.all()
```

---

## Step 3: Files Updated

### Backend Models
📄 **`backend/monitoring/models.py`**
- ✅ Added `spo2` field to SensorData model
- Stores oxygen saturation percentage from MAX30102 sensor

### Backend Serializers
📄 **`backend/monitoring/serializers.py`**
- ✅ Added `spo2` field to SensorDataSerializer
- Made optional with default value

### Backend Views
📄 **`backend/monitoring/views.py`**
- ✅ Added `@csrf_exempt` decorator to `receive_sensor_data`
- Allows Arduino to send POST requests without CSRF token
- Automatically creates alerts based on sensor thresholds

### Database
📄 **`backend/monitoring/migrations/0004_sensordata_spo2.py`**
- ✅ New migration file to add spo2 column

---

## Step 4: Running the System

### Terminal 1 - Start Django Backend
```bash
cd backend
python manage.py runserver 0.0.0.0:8000
```
✓ Server runs on `http://0.0.0.0:8000`
✓ API endpoint: `http://YOUR_IP:8000/api/sensor-data/`
✓ Dashboard: `http://YOUR_IP:8000/`

### Terminal 2 - Upload Arduino Code
1. Open `Final_Code.ino` in Arduino IDE
2. Ensure constants at top are correct:
   - WiFi SSID and password
   - Server IP address
   - Device ID
3. Select board: "ESP32 Dev Module"
4. Upload the code

### Verify Connection
Watch the Django server terminal for messages:
```
=== SENSOR DATA RECEIVED ===
Device ID: HELMET_001
✓ Helmet found: Helmet HELMET_001
✓ Data saved successfully
```

---

## Step 5: Viewing Data on Dashboard

Once data is flowing:

1. **Open Dashboard**: `http://YOUR_IP:8000/`
2. **View Real-time Data**: Heart rate, SpO2, gas levels, temperature
3. **Check Alerts**: Monitor section at bottom
4. **Worker History**: Click on workers to see historical graphs

### Available Graphs and Displays
- ❤️ Heart Rate (BPM)
- 🫁 SpO2 / Oxygen Saturation (%)
- 💨 Gas Level (PPM)
- 🌡️ Temperature (°C)
- 💧 Humidity (%)
- 🚨 Alerts (automatic detection)

---

## Step 6: Troubleshooting

### Arduino Not Connecting to WiFi
- **Check**: WiFi SSID and password are correct
- **Check**: ESP32 is in range of WiFi network
- **Monitor**: Serial output shows "Connecting to WiFi..." repeatedly?
  - Verify WiFi credentials
  - Restart ESP32 with correct credentials

### Server Not Receiving Data
- **Check**: Server IP is correct in Arduino code
- **Check**: Django backend is running (`python manage.py runserver`)
- **Check**: Both devices on same network
- **Test**: Ping the server from Arduino's network
- **Monitor**: Check Django server terminal for error messages

### "Device not registered" Error
- **Fix**: Register the device_id in Django Admin or shell
- **Verify**: device_id matches exactly (case-sensitive)
- **Check**: Django migrations have been applied

### Graphs Not Updating
- **Check**: Data is being saved (check Django terminal)
- **Check**: Page is not cached (Ctrl+Shift+Delete to clear cache)
- **Wait**: Dashboard updates every 2 seconds
- **Refresh**: Press F5 to refresh dashboard

---

## Step 7: Configuration Summary

### Arduino Constants to Update
```cpp
// Line 18-19: WiFi
const char* ssid = "TASHINGA";
const char* password = "1234567890";

// Line 22-23: Server & Device
const char* servername = "http://192.168.1.100:8000/api/sensor-data/";
const char* device_id = "HELMET_001";
```

### Django Database
- Device must be registered with matching `device_id`
- Database stores: heart_rate, spo2, gas_level, temperature, humidity, motion, location
- Alerts trigger automatically on abnormal values

### API Endpoint
```
POST /api/sensor-data/
Content-Type: application/json

{
  "device_id": "HELMET_001",
  "heart_rate": int,
  "spo2": float,
  "gas_level": float,
  "temperature": float,
  "humidity": float,
  "motion": float,
  "latitude": float (optional),
  "longitude": float (optional)
}
```

---

## Next Steps (Optional Enhancements)

1. **Add GPS**: Connect GPS module to ESP32 for location tracking
2. **Add Motion Sensor**: Connect accelerometer for fall detection
3. **Mobile App**: Create React Native app for alerts
4. **Real-time Alerts**: Add email/SMS notifications
5. **Cloud Sync**: Back up data to cloud storage
6. **Multiple Helmets**: Register multiple devices and track them all

---

Generated: March 24, 2026
System: Smart Helmet Monitoring System
