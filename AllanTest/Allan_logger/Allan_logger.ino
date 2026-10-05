#include <Wire.h>
#include <Adafruit_LSM6DSO32.h>
#include <esp_timer.h>

Adafruit_LSM6DSO32 imu;

void setup() {
  Serial.begin(115200);
  delay(1000);

  // Feather ESP32 I2C pins: SDA = GPIO 23, SCL = GPIO 22
  Wire.begin(23, 22);

  if (!imu.begin_I2C(0x6A, &Wire)) {
    Serial.println("#ERROR: LSM6DSO32 not found at 0x6A");
    while (true) {
      delay(1000);
    }
  }

  imu.setGyroDataRate(LSM6DS_RATE_104_HZ);
  imu.setAccelDataRate(LSM6DS_RATE_SHUTDOWN);

  delay(500);
  Serial.println("t_us,gx_rad_s,gy_rad_s,gz_rad_s");
}

void loop() {
  if (imu.gyroscopeAvailable()) {
    float gx, gy, gz;

    if (imu.readGyroscope(gx, gy, gz)) {
      unsigned long long t = (unsigned long long)esp_timer_get_time();

      Serial.printf("%llu,%.8f,%.8f,%.8f\n",
              t,
              gx * 0.01745329252f,
              gy * 0.01745329252f,
              gz * 0.01745329252f);
    }
  }
}
