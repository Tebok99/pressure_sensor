"""
MicroPython BMP388 라이브러리
I2C 인터페이스를 통한 온도 및 기압 측정 지원
저전력 모드와 일반 모드 모두 지원
"""
import time
from micropython import const

# BMP388 레지스터 주소
_BMP388_CHIP_ID = const(0x00)
_BMP388_ERR_REG = const(0x02)
_BMP388_STATUS = const(0x03)
_BMP388_DATA_0 = const(0x04)  # 압력 데이터 LSB
_BMP388_DATA_1 = const(0x05)  # 압력 데이터
_BMP388_DATA_2 = const(0x06)  # 압력 데이터 MSB
_BMP388_DATA_3 = const(0x07)  # 온도 데이터 LSB
_BMP388_DATA_4 = const(0x08)  # 온도 데이터
_BMP388_DATA_5 = const(0x09)  # 온도 데이터 MSB
_BMP388_SENSORTIME_0 = const(0x0C)
_BMP388_SENSORTIME_1 = const(0x0D)
_BMP388_SENSORTIME_2 = const(0x0E)
_BMP388_EVENT = const(0x10)
_BMP388_INT_STATUS = const(0x11)
_BMP388_FIFO_LENGTH_0 = const(0x12)
_BMP388_FIFO_LENGTH_1 = const(0x13)
_BMP388_FIFO_DATA = const(0x14)
_BMP388_FIFO_WTM_0 = const(0x15)
_BMP388_FIFO_WTM_1 = const(0x16)
_BMP388_FIFO_CONFIG_1 = const(0x17)
_BMP388_FIFO_CONFIG_2 = const(0x18)
_BMP388_INT_CTRL = const(0x19)
_BMP388_IF_CONF = const(0x1A)
_BMP388_PWR_CTRL = const(0x1B)
_BMP388_OSR = const(0x1C)
_BMP388_ODR = const(0x1D)
_BMP388_CONFIG = const(0x1F)
_BMP388_CALIB_DATA = const(0x31)
_BMP388_CMD = const(0x7E)

# ID 값
_BMP388_ID = const(0x50)

# 커맨드
_BMP388_CMD_SOFTRESET = const(0xB6)
_BMP388_CMD_FIFO_FLUSH = const(0xB0)

# 전력 모드
_BMP388_POWER_SLEEP = const(0x00)
_BMP388_POWER_NORMAL = const(0x33)  # 압력 및 온도 모두 활성화
_BMP388_POWER_FORCED = const(0x13)  # 압력 및 온도 강제 측정

# 오버샘플링 설정 (OSR)
_BMP388_OSR_1X = const(0x00)    # BMP388_OSR_NONE
_BMP388_OSR_2X = const(0x01)
_BMP388_OSR_4X = const(0x02)
_BMP388_OSR_8X = const(0x03)
_BMP388_OSR_16X = const(0x04)
_BMP388_OSR_32X = const(0x05)

# 출력 데이터 속도 (ODR)
_BMP388_ODR_200HZ = const(0x00)
_BMP388_ODR_100HZ = const(0x01)
_BMP388_ODR_50HZ = const(0x02)
_BMP388_ODR_25HZ = const(0x03)
_BMP388_ODR_12_5HZ = const(0x04)
_BMP388_ODR_6_25HZ = const(0x05)
_BMP388_ODR_3_1HZ = const(0x06)
_BMP388_ODR_1_5HZ = const(0x07)
_BMP388_ODR_0_78HZ = const(0x08)
_BMP388_ODR_0_39HZ = const(0x09)
_BMP388_ODR_0_2HZ = const(0x0A)
_BMP388_ODR_0_1HZ = const(0x0B)
_BMP388_ODR_0_05HZ = const(0x0C)
_BMP388_ODR_0_02HZ = const(0x0D)
_BMP388_ODR_0_01HZ = const(0x0E)
_BMP388_ODR_0_006HZ = const(0x0F)
_BMP388_ODR_0_003HZ = const(0x10)
_BMP388_ODR_0_0015HZ = const(0x11)

# 필터 설정
_BMP388_IIR_FILTER_COEFF_0 = const(0x00)
_BMP388_IIR_FILTER_COEFF_1 = const(0x01)
_BMP388_IIR_FILTER_COEFF_3 = const(0x02)
_BMP388_IIR_FILTER_COEFF_7 = const(0x03)
_BMP388_IIR_FILTER_COEFF_15 = const(0x04)
_BMP388_IIR_FILTER_COEFF_31 = const(0x05)
_BMP388_IIR_FILTER_COEFF_63 = const(0x06)
_BMP388_IIR_FILTER_COEFF_127 = const(0x07)

# 측정 준비 상태
_BMP388_DRDY_PRESS = const(0x20)
_BMP388_DRDY_TEMP = const(0x40)


class BMP388:
    """BMP388 디지털 압력 센서 드라이버"""

    def __init__(self, i2c, addr=0x77):
        """
        BMP388 센서 초기화
        :param i2c: I2C 인터페이스 객체
        :param addr: 센서의 I2C 주소 (기본값 0x76)
        """
        self.i2c = i2c
        self.addr = addr

        # 센서 ID 확인
        chip_id = self._read_byte(_BMP388_CHIP_ID)
        if chip_id != _BMP388_ID:
            raise RuntimeError("BMP388 센서를 찾을 수 없습니다. ID: %x" % chip_id)

        # 소프트 리셋 및 초기화
        self._reset()

        self._read_calibration_data()

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
        self._write_byte(_BMP388_CMD, _BMP388_CMD_SOFTRESET)
        time.sleep_ms(200)  # 리셋 후 대기

    def _read_calibration_data(self):
        """보정 데이터 읽기"""
        # BMP388 보정 데이터 읽기 (총 21바이트)
        calib_data = self._read_bytes(_BMP388_CALIB_DATA, 21)
        if len(calib_data) != 21:
            raise ValueError("BMP388 calibration data read failed.")

        # 데이터시트에 따라 보정 계수 추출
        self.T1 = (calib_data[1] << 8) | calib_data[0]  # 부호 없는 16비트
        self.T2 = (calib_data[3] << 8) | calib_data[2]  # 부호 없는 16비트
        self.T3 = calib_data[4]  # 부호 있는 8비트
        self.P1 = (calib_data[6] << 8) | calib_data[5]  # 부호 있는 16비트
        self.P2 = (calib_data[8] << 8) | calib_data[7]  # 부호 있는 16비트
        self.P3 = calib_data[9]  # 부호 있는 8비트
        self.P4 = calib_data[10]  # 부호 있는 8비트
        self.P5 = (calib_data[12] << 8) | calib_data[11]  # 부호 없는 16비트
        self.P6 = (calib_data[14] << 8) | calib_data[13]  # 부호 없는 16비트
        self.P7 = calib_data[15]  # 부호 있는 8비트
        self.P8 = calib_data[16]  # 부호 있는 8비트
        self.P9 = (calib_data[18] << 8) | calib_data[17]  # 부호 있는 16비트
        self.P10 = calib_data[19]  # 부호 있는 8비트
        self.P11 = calib_data[20]  # 부호 있는 8비트

        # 부호 있는 16비트 정수로 변환
        if self.P1 > 32767:
            self.P1 -= 65536
        if self.P2 > 32767:
            self.P2 -= 65536
        if self.P9 > 32767:
            self.P9 -= 65536

        # 부호 있는 8비트 정수로 변환
        if self.T3 > 127:
            self.T3 -= 256
        if self.P3 > 127:
            self.P3 -= 256
        if self.P4 > 127:
            self.P4 -= 256
        if self.P7 > 127:
            self.P7 -= 256
        if self.P8 > 127:
            self.P8 -= 256
        if self.P10 > 127:
            self.P10 -= 256
        if self.P11 > 127:
            self.P11 -= 256

        # 보정 계수 스케일링 (데이터시트 9.1)
        self.par_t1 = float(self.T1) * 256.0
        self.par_t2 = float(self.T2) / (1 << 30)
        self.par_t3 = float(self.T3) / (1 << 48)
        self.par_p1 = (float(self.P1) - 16384.0) / (1 << 20)
        self.par_p2 = (float(self.P2) - 16384.0) / (1 << 29)
        self.par_p3 = float(self.P3) / (1 << 32)
        self.par_p4 = float(self.P4) / (1 << 37)
        self.par_p5 = float(self.P5) * 8.0
        self.par_p6 = float(self.P6) / 64.0
        self.par_p7 = float(self.P7) / 256.0
        self.par_p8 = float(self.P8) / (1 << 15)
        self.par_p9 = float(self.P9) / (1 << 48)
        self.par_p10 = float(self.P10) / (1 << 48)
        self.par_p11 = float(self.P11) / (1 << 65)

    def set_low_power_mode(self):
        """저전력 모드 설정
        - 온도: 1x 오버샘플링
        - 압력: 1x 오버샘플링
        - 출력 데이터 속도: 1Hz
        - 필터: 꺼짐
        """
        # 출력 데이터 속도 설정 (1Hz)
        self._write_byte(_BMP388_ODR, _BMP388_ODR_1_5HZ)

        # 오버샘플링 설정 (1x)
        self._write_byte(_BMP388_OSR, (_BMP388_OSR_1X << 3) | _BMP388_OSR_1X)

        # 필터 설정 (꺼짐)
        self._write_byte(_BMP388_CONFIG, _BMP388_IIR_FILTER_COEFF_0 << 1)

        # 전력 모드 설정 (일반 모드)
        self._write_byte(_BMP388_PWR_CTRL, _BMP388_POWER_NORMAL)

        time.sleep_ms(20)

    def set_normal_mode(self):
        """일반 모드 설정
        - 온도: 2x 오버샘플링
        - 압력: 16x 오버샘플링
        - 출력 데이터 속도: 50Hz
        - 필터: 2x
        """
        # 출력 데이터 속도 설정 (50Hz)
        self._write_byte(_BMP388_ODR, _BMP388_ODR_50HZ)

        # 오버샘플링 설정 (온도 2x, 압력 8x)
        self._write_byte(_BMP388_OSR, (_BMP388_OSR_2X << 3) | _BMP388_OSR_8X)

        # 필터 설정 (2x)
        self._write_byte(_BMP388_CONFIG, _BMP388_IIR_FILTER_COEFF_1 << 1)

        # 전력 모드 설정 (일반 모드)
        self._write_byte(_BMP388_PWR_CTRL, _BMP388_POWER_NORMAL)

        time.sleep_ms(20)

    def sleep(self):
        """슬립 모드로 전환"""
        self._write_byte(_BMP388_PWR_CTRL, _BMP388_POWER_SLEEP)

    def force_measure(self):
        """강제 측정 모드"""
        self._write_byte(_BMP388_PWR_CTRL, _BMP388_POWER_FORCED)

        while self.is_measuring():
            time.sleep_ms(5)

    def is_measuring(self):
        """측정 중인지 확인"""
        return not (self._read_byte(_BMP388_STATUS) & 0x10)  # 압력 또는 온도 변환 중인지 확인

    def is_data_ready(self):
        status = self._read_byte(_BMP388_STATUS)
        return (status & _BMP388_DRDY_TEMP) and (status & _BMP388_DRDY_PRESS)

    def read_raw_data(self):
        timeout = 200   # 최대 200번 반복
        while self.is_measuring() and not self.is_data_ready() and timeout > 0:
            time.sleep_ms(5)
            timeout -= 1
        if timeout == 0:
            raise RuntimeError("Sensor measurement timed out.")

        data = self._read_bytes(_BMP388_DATA_0, 6)
        if len(data) != 6:
            raise ValueError("Sensor data read failed.")

        # 압력 데이터 조합 (리틀 엔디언)
        raw_pressure = (data[2] << 16) | (data[1] << 8) | data[0]

        # 온도 데이터 조합 (리틀 엔디언)
        raw_temperature = (data[5] << 16) | (data[4] << 8) | data[3]

        return raw_pressure, raw_temperature

    def compensate_temperature(self, raw_temp):
        """온도 보정 계산 (데이터시트 9.2)"""
        partial_data1 = float(raw_temp) - self.par_t1
        partial_data2 = partial_data1 * self.par_t2
        t_lin = partial_data2 + (partial_data1 * partial_data1) * self.par_t3
        return t_lin  # 섭씨 온도 (°C)

    def compensate_pressure(self, raw_press, t_lin):
        """기압 보정 계산 (데이터시트 9.3)"""
        partial_data1 = self.par_p6 * t_lin
        partial_data2 = self.par_p7 * (t_lin ** 2)
        partial_data3 = self.par_p8 * (t_lin ** 3)
        partial_out1 = self.par_p5 + partial_data1 + partial_data2 + partial_data3

        partial_data1 = self.par_p2 * t_lin
        partial_data2 = self.par_p3 * (t_lin ** 2)
        partial_data3 = self.par_p4 * (t_lin ** 3)
        partial_out2 = float(raw_press) * (self.par_p1 + partial_data1 + partial_data2 + partial_data3)

        partial_data1 = float(raw_press) * float(raw_press)
        partial_data2 = self.par_p9 + self.par_p10 * t_lin
        partial_data3 = partial_data1 * partial_data2
        partial_data4 = partial_data3 + (float(raw_press) ** 3) * self.par_p11

        comp_press = partial_out1 + partial_out2 + partial_data4
        return comp_press  # 파스칼 (Pa)

    @property
    def temperature(self):
        """보정된 온도 읽기 (°C)"""
        _, raw_temp = self.read_raw_data()
        return self.compensate_temperature(raw_temp)

    @property
    def pressure(self):
        """보정된 기압 읽기 (hPa)"""
        raw_press, raw_temp = self.read_raw_data()
        t_lin = self.compensate_temperature(raw_temp)
        pressure_pa = self.compensate_pressure(raw_press, t_lin)
        return pressure_pa / 100.0  # Pa -> hPa