from machine import I2C, Pin
import ustruct

class BMP280:
    def __init__(self, i2c, address=0x76):
        """BMP280 센서를 초기화합니다.
        Args:
            i2c: I2C 객체
            address: 센서의 I2C 주소 (기본값: 0x76)
        """
        self.i2c = i2c
        self.address = address
        self._reset()
        self._load_calibration()

    def _reset(self):
        """센서를 소프트 리셋합니다."""
        self.i2c.writeto_mem(self.address, 0xE0, b'\xB6')

    def _load_calibration(self):
        """보정 데이터를 읽어옵니다."""
        self.calib = self.i2c.readfrom_mem(self.address, 0x88, 24)
        # 보정 데이터 파싱 (데이터 시트 참조 필요)
        # 예: self.dig_T1 = ustruct.unpack('<H', self.calib[0:2])[0]

    def _read_raw_data(self):
        """raw 압력과 온도 데이터를 읽어옵니다."""
        data = self.i2c.readfrom_mem(self.address, 0xF7, 6)
        pressure = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
        temperature = (data[3] << 12) | (data[4] << 4) | (data[5] >> 4)
        return pressure, temperature

    def _compensate_temperature(self, raw_temp):
        """raw 온도 데이터를 보정합니다. (데이터 시트의 공식 필요)"""
        # 임시 값 반환, 실제 보정 공식은 데이터 시트 참조
        return 25.0

    def _compensate_pressure(self, raw_pressure, t_fine):
        """raw 압력 데이터를 보정합니다. (데이터 시트의 공식 필요)"""
        # 임시 값 반환, 실제 보정 공식은 데이터 시트 참조
        return 1013.25

    def begin(self):
        """센서를 측정 준비 상태로 초기화합니다."""
        self.i2c.writeto_mem(self.address, 0xF4, b'\x27')  # 온도 x1, 압력 x5, 일반 모드

    def read_temperature(self):
        """보정된 온도 값을 읽습니다."""
        raw_pressure, raw_temp = self._read_raw_data()
        t_fine = self._compensate_temperature(raw_temp)
        return t_fine

    def read_pressure(self):
        """보정된 압력 값을 읽습니다."""
        raw_pressure, raw_temp = self._read_raw_data()
        t_fine = self._compensate_temperature(raw_temp)
        pressure = self._compensate_pressure(raw_pressure, t_fine)
        return pressure

# 사용 예시
i2c = I2C(scl=Pin(1), sda=Pin(0))
sensor = BMP280(i2c)
sensor.begin()
temp = sensor.read_temperature()
pressure = sensor.read_pressure()
print(f"BMP280 - Temperature: {temp} °C, Pressure: {pressure} hPa")