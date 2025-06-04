from machine import Pin, I2C
import time
import math
import bmp280
import bmp388
import dps310

class SensorManager:
    def __init__(self):
        """I2C 버스 및 센서 초기화 (에러 처리 없음)"""
        # I2C 버스 설정
        self.i2c0 = I2C(0, sda=Pin(0), scl=Pin(1), freq=100000)
        self.i2c1 = I2C(1, sda=Pin(6), scl=Pin(7), freq=100000)

        # 센서 초기화
        self.bmp280 = bmp280.BMP280(self.i2c0, addr=0x76)
        self.dps310 = dps310.DPS310(self.i2c0, addr=0x77)
        self.bmp388 = bmp388.BMP388(self.i2c1, addr=0x77)

    @staticmethod
    def calculate_altitude(pressure_hpa, sea_level=1013.25):
        """기압 → 고도 변환 (복소수 및 음수 방지)"""
        try:
            # 입력값 음수 방지
            pressure = abs(float(pressure_hpa))

            # 비율 계산 (0~1 범위 강제)
            ratio = (pressure / sea_level) ** (1.0/5.255)
            # ratio = max(0.0, min(1.0, ratio))  # 0~1 범위 제한

            # 고도 계산 및 음수 방지
            altitude = 44330 * (1 - ratio)
            return max(0.0, altitude)  # 최소 0m 보장

        except Exception as e:
            print(f"고도 계산 오류: {e}")
            return 0.0

    @staticmethod
    def format_timestamp():
        t = time.localtime()
        ms = time.ticks_ms() % 1000
        return f"{t[3]:02d}:{t[4]:02d}:{t[5]:02d}:{ms:03d}"