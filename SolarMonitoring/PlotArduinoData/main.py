
# Program to gather data from an arduino device, plot it, and save it to a csv file.

'''
If you run this code on Linux and get a Permission Denied error regarding
the serial port /dev/ttyACM0, it means your Linux user profile does not
have hardware access rights. You may be able fix this permanently by adding
your account to the dialout group via your terminal:
bash script: sudo usermod -a -G dialout $USER
You will need to log out of Linux and log back in for this permission change
to take effect.
'''

import csv
import os
import platform
import sys
import time
import matplotlib.pyplot as plt
import serial

# ==============================================================================
# 1. AUTO-DETECT OPERATING SYSTEM & SET SERIAL PORT
# ==============================================================================
SYSTEM = platform.system()
BAUD_RATE = 9600  # Must match Serial.begin() in your Arduino code
CSV_FILE = "arduino_data.csv"

if SYSTEM == "Windows":
    # Change 'COM3' to the specific port your Arduino uses on Windows
    SERIAL_PORT = "COM3"
elif SYSTEM == "Linux":
    # Change 'ttyACM0' to your specific port (often ttyUSB0 or ttyACM0)
    SERIAL_PORT = "/dev/ttyACM0"
else:
    print(f"Unsupported operating system: {SYSTEM}")
    sys.exit(1)

print(f"Running on {SYSTEM}. Attempting to connect to {SERIAL_PORT}...")

# ==============================================================================
# 2. INITIALIZE CSV FILE AND GRAPH SETUP
# ==============================================================================
# Write headers to the CSV if it's a brand new file
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Timestamp", "Solar Panel", "Battery"])

# Setup matplotlib live window
plt.ion()
fig, ax = plt.subplots(figsize=(8, 6))
x_data, y1_data, y2_data = [], [], []

(line1,) = ax.plot([], [], "r-", label="Solar Panel Voltage")
(line2,) = ax.plot([], [], "b-", label="Battery Voltage")
plt.legend(bbox_to_anchor=(0.0, -0.20), loc='center left')
plt.title("Solar Voltage vs Battery Voltage")
fig.subplots_adjust(bottom=0.25)
ax.set_xlabel("Time (Seconds into test)")
ax.set_ylabel("Sensor Values")

# ==============================================================================
# 3. MAIN DATA COLLECTION LOOP
# ==============================================================================
try:
    # Open the serial port and the CSV file using a nested context
    with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1) as ser, open(
        CSV_FILE, mode="a", newline=""
    ) as file:

        csv_writer = csv.writer(file)
        start_time = time.time()

        print(f"Successfully connected! Logging data to {CSV_FILE}...")
        print("Press Ctrl+C in your terminal to safely stop.")

        while True:
            # Read a line of binary bytes from serial and decode to text string
            raw_line = ser.readline().decode("utf-8").strip()

            if raw_line:
                try:
                    # Parse comma-separated variables sent by Arduino
                    parsed_values = [float(val) for val in raw_line.split(",")]

                    # Ensure we received exactly the number of variables expected
                    if len(parsed_values) == 2:
                        val1, val2 = parsed_values
                        current_timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

                        # A. Log to CSV immediately
                        csv_writer.writerow(["'"+current_timestamp, val1, val2])
                        file.flush()  # Forces system to write data to disk right away

                        # B. Update graph data arrays
                        elapsed_time = time.time() - start_time
                        x_data.append(elapsed_time)
                        y1_data.append(val1)
                        y2_data.append(val2)

                        # Maintain a scrolling visual window (keeps last 50 points)
                        if len(x_data) > 50:
                            x_data.pop(0)
                            y1_data.pop(0)
                            y2_data.pop(0)

                        # C. Refresh live plot
                        line1.set_data(x_data, y1_data)
                        line2.set_data(x_data, y2_data)

                        ax.relim()
                        ax.autoscale_view()
                        fig.canvas.flush_events()
                        plt.pause(0.01)

                except ValueError:
                    # Ignore incomplete bits or text garbage during script startup
                    pass

except serial.SerialException:
    print(f"\nError: Could not open {SERIAL_PORT}.")
    print("Check that your Arduino is plugged in and the IDE Serial Plotter is CLOSED.")
except KeyboardInterrupt:
    print("\nLogging stopped cleanly by user. Data saved successfully.")
finally:
    plt.close()

exit(0)
