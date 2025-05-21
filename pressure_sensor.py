# code.py
# 라즈베리파이 피코2에서 DPS310, BMP388, BMP280 센서를 테스트하는 Micropython 코드
import time

from machine import Pin, I2C, SoftI2C

# 센서 모듈 임포트 (실제 라이브러리 또는 커스텀 모듈 필요)
from bmp280.bmp280 import BMP280  # pico-bmp280 라이브러리
from bmp388.bmpxxx import BMP390  # MicroPython_BMPxxx, BMP390 호환 가정
from dps310.dps310 import DPS310  # 커스텀 또는 조정된 라이브러리 가정

# I2C 버스 초기화
i2c0 = I2C(0, sda=Pin(0), scl=Pin(1))  # DPS310, BMP280용
i2c1 = SoftI2C(sda=Pin(4), scl=Pin(5))  # BMP388용

# 센서 초기화
bmp280 = BMP280(i2c=i2c0, address=0x76)
dps310 = DPS310(i2c=i2c0, address=0x77)
bmp388 = BMP390(i2c=i2c1, address=0x77)

# 모드 정의
low_power_mode = {
    'bmp280': {'pressure_oversample': 1, 'temp_oversample': 1},
    'dps310': {'pressure_rate': 1, 'temp_rate': 1},
    'bmp388': {'pressure_oversample': 1, 'temp_oversample': 1}
}
normal_mode = {
    'bmp280': {'pressure_oversample': 16, 'temp_oversample': 16},
    'dps310': {'pressure_rate': 16, 'temp_rate': 16},
    'bmp388': {'pressure_oversample': 16, 'temp_oversample': 16}
}

# 센서 모드 설정 함수
def set_mode(sensor, mode):
    if sensor == 'bmp280':
        bmp280.oversample_set(pressure=mode['pressure_oversample'], temp=mode['temp_oversample'])
    elif sensor == 'dps310':
        dps310.set_measurement_rate(pressure=mode['pressure_rate'], temp=mode['temp_rate'])
    elif sensor == 'bmp388':
        bmp388.oversample_set(pressure=mode['pressure_oversample'], temp=mode['temp_oversample'])

# 센서 데이터 읽기 함수
def read_sensor(sensor):
    if sensor == 'bmp280':
        return bmp280.measurements['p'], bmp280.measurements['t']
    elif sensor == 'dps310':
        return dps310.pressure, dps310.temperature
    elif sensor == 'bmp388':
        return bmp388.pressure, bmp388.temperature
    return None


# 메인 함수 (자동 실행 방지)
def main():
    # 저전력 모드 테스트
    print("저전력 모드")
    set_mode('bmp280', low_power_mode['bmp280'])
    set_mode('dps310', low_power_mode['dps310'])
    set_mode('bmp388', low_power_mode['bmp388'])
    for i in range(10):
        p1, t1 = read_sensor('bmp280')
        p2, t2 = read_sensor('dps310')
        p3, t3 = read_sensor('bmp388')
        print(f"시간 {i+1}s: BMP280 P={p1} T={t1}, DPS310 P={p2} T={t2}, BMP388 P={p3} T={t3}")
        time.sleep(1)

    # 일반 모드 테스트
    print("일반 모드")
    set_mode('bmp280', normal_mode['bmp280'])
    set_mode('dps310', normal_mode['dps310'])
    set_mode('bmp388', normal_mode['bmp388'])
    for i in range(10):
        p1, t1 = read_sensor('bmp280')
        p2, t2 = read_sensor('dps310')
        p3, t3 = read_sensor('bmp388')
        print(f"시간 {i+1}s: BMP280 P={p1} T={t1}, DPS310 P={p2} T={t2}, BMP388 P={p3} T={t3}")
        time.sleep(1)

# REPL에서 main()을 수동 호출해야 실행됨