"""
MicroPython DPS310 라이브러리
I2C 인터페이스를 통한 온도 및 기압 측정 지원
저전력 모드와 일반 모드 모두 지원
"""
import time
from micropython import const

# DPS310 레지스터 주소
_DPS310_PROD_ID = const(0x0D)
_DPS310_SPI_WRITE = const(0x00)
_DPS310_SPI_READ = const(0x80)
_DPS310_RESET = const(0x0C)
_DPS310_PRS_CFG = const(0x06)
_DPS310_TMP_CFG = const(0x07)
_DPS310_MEAS_CFG = const(0x08)
_DPS310_COEF_RDY = const(0x80)
_DPS310_SENSOR_RDY = const(0x40)
_DPS310_TMP_RDY = const(0x20)
_DPS310_PRS_RDY = const(0x10)
_DPS310_CFG_REG = const(0x09)
_DPS310_INT_STS = const(0x0A)
_DPS310_FIFO_STS = const(0x0B)
_DPS310_TMP_B2 = const(0x03)
_DPS310_TMP_B1 = const(0x04)
_DPS310_TMP_B0 = const(0x05)
_DPS310_PRS_B2 = const(0x00)
_DPS310_PRS_B1 = const(0x01)
_DPS310_PRS_B0 = const(0x02)
_DPS310_COEF = const(0x10)
_DPS310_TMP_COEF_SRCE = const(0x28)

# 제품 ID
_DPS310_PROD_ID_VAL = const(0x10)

# 제어 설정
_DPS310_TEMP_MEAS = const(0x02)
_DPS310_PRES_MEAS = const(0x01)
_DPS310_BACKGROUND_MODE = const(0x07)
_DPS310_ONESHOT_MODE = const(0x00)

# 오버샘플링 속도
_DPS310_RATE_1_HZ = const(0x00)
_DPS310_RATE_2_HZ = const(0x10)
_DPS310_RATE_4_HZ = const(0x20)
_DPS310_RATE_8_HZ = const(0x30)
_DPS310_RATE_16_HZ = const(0x40)
_DPS310_RATE_32_HZ = const(0x50)
_DPS310_RATE_64_HZ = const(0x60)
_DPS310_RATE_128_HZ = const(0x70)

# 오버샘플링 계수
_DPS310_OSR_1 = const(0x00)
_DPS310_OSR_2 = const(0x01)
_DPS310_OSR_4 = const(0x02)
_DPS310_OSR_8 = const(0x03)
_DPS310_OSR_16 = const(0x04)
_DPS310_OSR_32 = const(0x05)
_DPS310_OSR_64 = const(0x06)
_DPS310_OSR_128 = const(0x07)


class DPS310:
    """DPS310 디지털 압력 센서 드라이버"""

    def __init__(self, i2c, addr=0x77):
        """
        DPS310 센서 초기화
        :param i2c: I2C 인터페이스 객체
        :param addr: 센서의 I2C 주소 (기본값 0x77)
        """
        self.i2c = i2c
        self.addr = addr
        self.temp_scale = 524288.0  # 기본값 (1x 오버샘플링)
        self.press_scale = 524288.0  # 기본값 (1x 오버샘플링)

        # 센서 ID 확인
        prod_id = self._read_byte(_DPS310_PROD_ID)
        if prod_id != _DPS310_PROD_ID_VAL:
            raise RuntimeError("DPS310 센서를 찾을 수 없습니다. ID: %x" % prod_id)

        # 소프트 리셋 수행
        self._reset()

        # 보정 계수 읽기
        self._read_calibration()

        # 기본 설정: 일반 모드
        self.set_normal_mode()

    def _read_byte(self, register):
        """레지스터에서 1바이트 읽기"""
        result = self.i2c.readfrom_mem(self.addr, register, 1)
        return result[0]

    def _write_byte(self, register, value):
        """레지스터에 1바이트 쓰기"""
        self.i2c.writeto_mem(self.addr, register, bytes([value]))

    def _read_bytes(self, register, count):
        """레지스터에서 여러 바이트 읽기"""
        return self.i2c.readfrom_mem(self.addr, register, count)

    def _reset(self):
        """소프트 리셋 수행"""
        self._write_byte(_DPS310_RESET, 0x89)
        time.sleep_ms(300)  # 리셋 후 대기

    def _read_calibration(self):
        """보정 계수 읽기"""
        while True:
            status = self._read_byte(_DPS310_MEAS_CFG)
            if status & _DPS310_COEF_RDY:
                break
            time.sleep_ms(5)
        # 보정 계수 블록 읽기 (18바이트)
        coef_data = self._read_bytes(_DPS310_COEF, 18)

        # 온도 계수 소스 설정
        # tmp_coef_src = self._read_byte(_DPS310_TMP_COEF_SRCE) & 0x80

        # 보정 계수 추출
        c0 = ((coef_data[0] << 4) | (coef_data[1] >> 4)) & 0x0FFF
        if c0 & 0x0800:  # 음수 처리
            c0 -= 0x1000

        c1 = ((coef_data[1] & 0x0F) << 8) | coef_data[2]
        if c1 & 0x0800:  # 음수 처리
            c1 -= 0x1000

        c00 = ((coef_data[3] << 12) | (coef_data[4] << 4) | (coef_data[5] >> 4)) & 0xFFFFF
        if c00 & 0x80000:  # 음수 처리
            c00 -= 0x100000

        c10 = ((coef_data[5] & 0x0F) << 16) | (coef_data[6] << 8) | coef_data[7]
        if c10 & 0x80000:  # 음수 처리
            c10 -= 0x100000

        c01 = ((coef_data[8] << 8) | coef_data[9])
        if c01 & 0x8000:  # 음수 처리
            c01 -= 0x10000

        c11 = ((coef_data[10] << 8) | coef_data[11])
        if c11 & 0x8000:  # 음수 처리
            c11 -= 0x10000

        c20 = ((coef_data[12] << 8) | coef_data[13])
        if c20 & 0x8000:  # 음수 처리
            c20 -= 0x10000

        c21 = ((coef_data[14] << 8) | coef_data[15])
        if c21 & 0x8000:  # 음수 처리
            c21 -= 0x10000

        c30 = ((coef_data[16] << 8) | coef_data[17])
        if c30 & 0x8000:  # 음수 처리
            c30 -= 0x10000

        self.c0 = c0
        self.c1 = c1
        self.c00 = c00
        self.c10 = c10
        self.c01 = c01
        self.c11 = c11
        self.c20 = c20
        self.c21 = c21
        self.c30 = c30
        # self.temp_source = tmp_coef_src

    def set_low_power_mode(self):
        """저전력 모드 설정
        - 온도: 1x 오버샘플링, 1Hz
        - 압력: 1x 오버샘플링, 1Hz
        - 백그라운드 모드
        """
        # 온도 설정: 1x 오버샘플링, 1Hz
        self._write_byte(_DPS310_TMP_CFG, _DPS310_RATE_1_HZ | _DPS310_OSR_1)

        # 압력 설정: 1x 오버샘플링, 1Hz
        self._write_byte(_DPS310_PRS_CFG, _DPS310_RATE_1_HZ | _DPS310_OSR_1)

        # 백그라운드 모드 활성화
        self._write_byte(_DPS310_MEAS_CFG, _DPS310_BACKGROUND_MODE)

        self.temp_scale = 524288.0  # 1x 오버샘플링
        self.press_scale = 524288.0  # 1x 오버샘플링

        # 대기
        time.sleep_ms(50)

    def set_normal_mode(self):
        """일반 모드 설정
        - 온도: 16x 오버샘플링, 8Hz
        - 압력: 64x 오버샘플링, 8Hz
        - 백그라운드 모드
        """
        # 온도 설정: 16x 오버샘플링, 8Hz
        self._write_byte(_DPS310_TMP_CFG, _DPS310_RATE_8_HZ | _DPS310_OSR_16)

        # 압력 설정: 64x 오버샘플링, 8Hz
        self._write_byte(_DPS310_PRS_CFG, _DPS310_RATE_8_HZ | _DPS310_OSR_64)

        # 백그라운드 모드 활성화
        self._write_byte(_DPS310_MEAS_CFG, _DPS310_BACKGROUND_MODE)

        self.temp_scale = 253952.0  # 16x 오버샘플링
        self.press_scale = 1040384.0  # 64x 오버샘플링
        # 대기
        time.sleep_ms(50)

    def read_raw_pressure(self):
        """원시 압력 데이터 읽기"""
        # while True:
        #     status = self._read_byte(_DPS310_MEAS_CFG)
        #     if status & _DPS310_SENSOR_RDY:
        #         break
        #     time.sleep_ms(5)
        data = self._read_bytes(_DPS310_PRS_B2, 3)
        raw_pressure = (data[0] << 16) | (data[1] << 8) | data[2]
        if raw_pressure & 0x800000:  # 음수 처리
            raw_pressure -= 0x1000000
        return raw_pressure

    def read_raw_temperature(self):
        """원시 온도 데이터 읽기"""
        # while True:
        #     status = self._read_byte(_DPS310_MEAS_CFG)
        #     if status & _DPS310_SENSOR_RDY:
        #         break
        #     time.sleep_ms(5)
        data = self._read_bytes(_DPS310_TMP_B2, 3)
        raw_temperature = (data[0] << 16) | (data[1] << 8) | data[2]
        if raw_temperature & 0x800000:  # 음수 처리
            raw_temperature -= 0x1000000
        return raw_temperature

    def compensate_temperature(self, raw_temp):
        """온도 보정 계산"""
        scaled_temp = float(raw_temp) / self.temp_scale
        compensated_temp = self.c0 * 0.5 + self.c1 * scaled_temp
        return compensated_temp

    def compensate_pressure(self, raw_pressure, scaled_temp):
        """압력 보정 계산"""
        scaled_pressure = float(raw_pressure) / self.press_scale

        compensated_pressure = (
                self.c00 +
                scaled_pressure * (self.c10 + scaled_pressure * (self.c20 + scaled_pressure * self.c30)) +
                scaled_temp * (self.c01 + scaled_pressure * (self.c11 + scaled_pressure * self.c21))
        )

        return compensated_pressure

    @property
    def temperature(self):
        """보정된 온도 읽기 (°C)"""
        raw_temp = self.read_raw_temperature()
        return self.compensate_temperature(raw_temp)

    @property
    def pressure(self):
        """보정된 기압 읽기 (hPa)"""
        raw_temp = self.read_raw_temperature()
        temp_comp = self.compensate_temperature(raw_temp)
        raw_pressure = self.read_raw_pressure()
        pressure = self.compensate_pressure(raw_pressure, temp_comp)
        return pressure / 100.0  # Pa -> hPa