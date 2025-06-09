"""
MicroPython BMP280 라이브러리
I2C 인터페이스를 통한 온도 및 기압 측정 지원
저전력 모드와 일반 모드 모두 지원
"""
import time
from micropython import const

# BMP280 레지스터 주소
_BMP280_CHIP_ID = const(0xD0)
_BMP280_RESET = const(0xE0)
_BMP280_STATUS = const(0xF3)
_BMP280_CTRL_MEAS = const(0xF4)
_BMP280_CONFIG = const(0xF5)
_BMP280_TEMP_DATA = const(0xFA)
_BMP280_PRESS_DATA = const(0xF7)
_BMP280_DIG_T1 = const(0x88)

# ID 값
_BMP280_ID = const(0x58)

# 전력 모드 상수
_BMP280_POWER_SLEEP = const(0x00)
_BMP280_POWER_FORCED = const(0x01)  # or 0x02
_BMP280_POWER_NORMAL = const(0x03)

# 오버샘플링 설정
_BMP280_OS_NONE = const(0x00)
_BMP280_OS_1X = const(0x01)
_BMP280_OS_2X = const(0x02)
_BMP280_OS_4X = const(0x03)
_BMP280_OS_8X = const(0x04)
_BMP280_OS_16X = const(0x05)

# 대기 시간 설정
_BMP280_STANDBY_0_5 = const(0x00)  # 0.5 ms
_BMP280_STANDBY_62_5 = const(0x01)  # 62.5 ms
_BMP280_STANDBY_125 = const(0x02)  # 125 ms
_BMP280_STANDBY_250 = const(0x03)  # 250 ms
_BMP280_STANDBY_500 = const(0x04)  # 500 ms
_BMP280_STANDBY_1000 = const(0x05)  # 1 sec
_BMP280_STANDBY_2000 = const(0x06)  # 2 sec
_BMP280_STANDBY_4000 = const(0x07)  # 4 sec

# 필터 설정
_BMP280_IIR_FILTER_OFF = const(0x00)
_BMP280_IIR_FILTER_2 = const(0x01)
_BMP280_IIR_FILTER_4 = const(0x02)
_BMP280_IIR_FILTER_8 = const(0x03)
_BMP280_IIR_FILTER_16 = const(0x04)


class BMP280:
    """BMP280 디지털 압력 센서 드라이버"""

    def __init__(self, i2c, addr=0x76):
        """
        BMP280 센서 초기화
        :param i2c: I2C 인터페이스 객체
        :param addr: 센서의 I2C 주소 (기본값 0x76)
        """
        self.i2c = i2c
        self.addr = addr
        self.t_fine = 0

        # 센서 ID 확인
        chip_id = self._read_byte(_BMP280_CHIP_ID)
        if chip_id != _BMP280_ID:
            raise RuntimeError("BMP280 센서를 찾을 수 없습니다. ID: %x" % chip_id)

        # 초기화 및 보정 데이터 읽기
        self._reset()

        self._read_coefficients()

        # 기본 설정: 일반 모드, 16x 압력 오버샘플링, 2x 온도 오버샘플링, 0.5ms 대기 시간, 필터 끔
        # self._write_byte(_BMP280_CONFIG, (_BMP280_STANDBY_0_5 << 5) | (_BMP280_IIR_FILTER_OFF << 2))
        self.set_normal_mode()

    def _read_byte(self, register):
        """레지스터에서 1바이트 읽기"""
        result = self.i2c.readfrom_mem(self.addr, register, 1)
        return result[0]

    def _write_byte(self, register, value):
        """레지스터에 1바이트 쓰기"""
        self.i2c.writeto_mem(self.addr, register, bytes([value]))

    def _read_word(self, register):
        """레지스터에서 2바이트(16비트) 읽기 (리틀 엔디안)"""
        data = self.i2c.readfrom_mem(self.addr, register, 2)
        return data[0] | (data[1] << 8)

    def _read_signed_word(self, register):
        """레지스터에서 부호있는 16비트 정수 읽기"""
        raw = self._read_word(register)
        if raw & 0x8000:  # MSB가 1이면 음수
            raw = raw - 0x10000
        return raw

    def _reset(self):
        """센서 리셋"""
        self._write_byte(_BMP280_RESET, 0xB6)
        time.sleep_ms(200)  # 리셋 후 대기

    def _read_coefficients(self):
        """보정 계수 읽기"""
        while True:
            if self._read_signed_word(_BMP280_STATUS) == 0:
                break
            time.sleep_ms(5)
        self.dig_T1 = self._read_word(_BMP280_DIG_T1)
        self.dig_T2 = self._read_signed_word(_BMP280_DIG_T1 + 2)
        self.dig_T3 = self._read_signed_word(_BMP280_DIG_T1 + 4)

        self.dig_P1 = self._read_word(_BMP280_DIG_T1 + 6)
        self.dig_P2 = self._read_signed_word(_BMP280_DIG_T1 + 8)
        self.dig_P3 = self._read_signed_word(_BMP280_DIG_T1 + 10)
        self.dig_P4 = self._read_signed_word(_BMP280_DIG_T1 + 12)
        self.dig_P5 = self._read_signed_word(_BMP280_DIG_T1 + 14)
        self.dig_P6 = self._read_signed_word(_BMP280_DIG_T1 + 16)
        self.dig_P7 = self._read_signed_word(_BMP280_DIG_T1 + 18)
        self.dig_P8 = self._read_signed_word(_BMP280_DIG_T1 + 20)
        self.dig_P9 = self._read_signed_word(_BMP280_DIG_T1 + 22)

    def set_low_power_mode(self):
        """저전력 모드 설정
        - 온도: 1x 오버샘플링
        - 압력: 1x 오버샘플링
        - 대기 시간: 1초
        - 필터: 꺼짐
        """
        self._write_byte(_BMP280_CONFIG, (_BMP280_STANDBY_1000 << 5) | (_BMP280_IIR_FILTER_OFF << 2))
        self._write_byte(_BMP280_CTRL_MEAS, (_BMP280_OS_1X << 5) | (_BMP280_OS_1X << 2) | _BMP280_POWER_NORMAL)

        time.sleep_ms(10)

    def set_normal_mode(self):
        """일반 모드 설정
        - 온도: 2x 오버샘플링
        - 압력: 16x 오버샘플링
        - 대기 시간: 0.5ms
        - 필터: 4x
        """
        self._write_byte(_BMP280_CONFIG, (_BMP280_STANDBY_0_5 << 5) | (_BMP280_IIR_FILTER_4 << 2))
        self._write_byte(_BMP280_CTRL_MEAS, (_BMP280_OS_16X << 5) | (_BMP280_OS_2X << 2) | _BMP280_POWER_NORMAL)

        time.sleep_ms(10)

    def sleep(self):
        """슬립 모드로 전환"""
        mode = self._read_byte(_BMP280_CTRL_MEAS)
        self._write_byte(_BMP280_CTRL_MEAS, (mode & 0xFC) | _BMP280_POWER_SLEEP)

    def force_measure(self):
        """강제 측정 모드"""
        mode = self._read_byte(_BMP280_CTRL_MEAS)
        self._write_byte(_BMP280_CTRL_MEAS, (mode & 0xFC) | _BMP280_POWER_FORCED)
        while self.is_measuring():
            time.sleep_ms(5)

    def is_measuring(self):
        """측정 중인지 확인"""
        return (self._read_byte(_BMP280_STATUS) & 0x08) > 0

    def read_raw_temperature(self):
        """원시 온도 데이터 읽기"""
        data = self.i2c.readfrom_mem(self.addr, _BMP280_TEMP_DATA, 3)
        return (data[0] << 16 | data[1] << 8 | data[2]) >> 4

    def read_raw_pressure(self):
        """원시 압력 데이터 읽기"""
        data = self.i2c.readfrom_mem(self.addr, _BMP280_PRESS_DATA, 3)
        return (data[0] << 16 | data[1] << 8 | data[2]) >> 4

    def compensate_temperature(self, adc_t):
        """온도 보정 계산 데이터시트의 보정 공식 구현"""
        var1 = ((adc_t >> 3) - (self.dig_T1 << 1)) * self.dig_T2 >> 11
        var2 = (((((adc_t >> 4) - self.dig_T1) * ((adc_t >> 4) - self.dig_T1)) >> 12) * self.dig_T3) >> 14
        self.t_fine = var1 + var2
        return (self.t_fine * 5 + 128) >> 8

    def compensate_pressure(self, adc_p):
        """압력 보정 계산 데이터시트의 보정 공식 구현"""
        var1 = self.t_fine - 128000
        var2 = var1 * var1 * self.dig_P6
        var2 = var2 + ((var1 * self.dig_P5) << 17)
        var2 = var2 + (self.dig_P4 << 35)
        var1 = ((var1 * var1 * self.dig_P3) >> 8) + ((var1 * self.dig_P2) << 12)
        var1 = ((1 << 47) + var1) * self.dig_P1 >> 33

        if var1 == 0:
            return 0  # 0으로 나누기 방지

        p = 1048576 - adc_p
        p = (((p << 31) - var2) * 3125) // var1
        var1 = (self.dig_P9 * (p >> 13) * (p >> 13)) >> 25
        var2 = (self.dig_P8 * p) >> 19

        p = ((p + var1 + var2) >> 8) + (self.dig_P7 << 4)
        return p / 256.0

    @property
    def temperature(self):
        """보정된 온도 읽기 (°C)"""
        raw_temp = self.read_raw_temperature()
        return self.compensate_temperature(raw_temp) / 100.0

    @property
    def pressure(self):
        """보정된 기압 읽기 (hPa)"""
        self.read_raw_temperature()  # t_fine 업데이트
        raw_pressure = self.read_raw_pressure()
        return self.compensate_pressure(raw_pressure) / 100.0  # Pa -> hPa