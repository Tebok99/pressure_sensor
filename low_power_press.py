# low_power.py
from sensor_utils import SensorManager
import time

def main():
    sensors = SensorManager(mode='low_power')
    max_interval = 1  # 초, 최대 1초
    try:
        while True:
            ts = sensors.get_timestamp()
            # 센서 데이터 읽기
            try:
                pressure_bmp280 = sensors.bmp280.pressure / 100 if sensors.bmp280 else 0
                pressure_dps = sensors.dps310.pressure if sensors.dps310 else 0
                sensors.bmp388.force_measure()
                pressure_bmp388 = sensors.bmp388.pressure / 100 if sensors.bmp388 else 0
            except:
                pressure_bmp280 = pressure_dps = pressure_bmp388 = 0

            # 출력
            print(f"[{ts}]")
            print(f"['BMP280', '{pressure_bmp280:.2f}hPa', '{sensors.calc_altitude(pressure_bmp280):.2f}m']")
            print(f"['DPS310', '{pressure_dps:.2f}hPa', '{sensors.calc_altitude(pressure_dps):.2f}m']")
            print(f"['BMP388', '{pressure_bmp388:.2f}hPa', '{sensors.calc_altitude(pressure_bmp388):.2f}m']")
            print("="*50)
            time.sleep(max_interval)
    except KeyboardInterrupt:
        print("저전력 모드 종료")

if __name__ == "__main__":
    main()