# sensor_utils.py
import time
import math
from machine import Pin, I2C

import bmp280
import bmp388
import dps310

class SensorManager:
    def __init__(self, mode='low_power'):
        # I2C 버스 초기화
        self.i2c0 = I2C(0, sda=Pin(0), scl=Pin(1), freq=100000)
        self.i2c1 = I2C(1, sda=Pin(6), scl=Pin(7), freq=100000)
        self.mode = mode
        self._init_sensors()

    def _init_bmp280(self):
        try:
            sensor = bmp280.BMP280(self.i2c0, addr=0x76)
            sensor.oversample(bmp280.BMP280_OS_LOW if self.mode=='low_power' else bmp280.BMP280_OS_HIGH)
            sensor.standby = bmp280.BMP280_STANDBY_1000 if self.mode=='low_power' else bmp280.BMP280_STANDBY_500
            return sensor
        except:
            return None

    def _init_bmp388(self):
        try:
            sensor = bmp388.BMP388_I2C(self.i2c1, addr=0x77)
            sensor.oversampling = 1 if self.mode=='low_power' else 8
            return sensor
        except:
            return None

    def _init_dps310(self):
        try:
            sensor = dps310.DPS310(self.i2c0, address=0x77)
            sensor.mode = dps310.MODE_STANDBY if self.mode=='low_power' else dps310.MODE_CONT_MEAS
            return sensor
        except:
            return None

    def _init_sensors(self):
        self.bmp280 = self._init_bmp280()
        self.bmp388 = self._init_bmp388()
        self.dps310 = self._init_dps310()

    @staticmethod
    def calc_altitude(pressure_hpa):
        return 44330 * (1 - (pressure_hpa / 1013.25) ** 0.1903)

    @staticmethod
    def get_timestamp():
        t = time.localtime()
        ms = time.ticks_ms() % 1000
        return f"{t[3]:02d}:{t[4]:02d}:{t[5]:02d}:{ms:03d}"