import time
from pathlib import Path

import serial

PORT = "COM4"
BAUD = 115200
OUTPUT = Path(__file__).with_name("gyro_log.csv")
HEADER = "t_us,gx_rad_s,gy_rad_s,gz_rad_s"

count = 0
recording = False

try:
    with serial.Serial(PORT, BAUD, timeout=2) as board:
        print(f"Connected to {PORT}. Waiting for gyro data...")
        time.sleep(2)

        with OUTPUT.open("w", encoding="utf-8", newline="") as log:
            while True:
                raw = board.readline()
                if not raw:
                    continue

                line = raw.decode("ascii", errors="replace").strip()

                # Ignore ESP32 startup messages; begin at the CSV header.
                if not recording:
                    if line == HEADER:
                        log.write(HEADER + "\n")
                        recording = True
                        print(f"Recording to {OUTPUT}")
                    continue

                fields = line.split(",")
                if len(fields) != 4:
                    continue

                try:
                    int(fields[0])
                    float(fields[1])
                    float(fields[2])
                    float(fields[3])
                except ValueError:
                    continue

                log.write(line + "\n")
                count += 1

                if count % 104 == 0:
                    log.flush()
                    print(f"Saved {count} samples", end="\r")

except KeyboardInterrupt:
    print(f"\nStopped. Saved {count} samples to {OUTPUT}")
except serial.SerialException as error:
    print(f"\nSerial connection error: {error}")