from sensor_utils import SensorManager
import time


def main():
    mgr = SensorManager()

    # 고정밀 모드 설정
    mgr.bmp280.use_case(mgr.bmp280.BMP280_CASE_INDOOR)
    mgr.dps310.mode = mgr.dps310.MODE_CONT_MEAS
    mgr.bmp388.set_normal_mode()

    try:
        while True:
            # 센서 측정
            data = {
                'BMP280': mgr.bmp280.pressure,
                'DPS310': mgr.dps310.pressure,
                'BMP388': mgr.bmp388.pressure
            }

            # 결과 출력
            ts = mgr.format_timestamp()
            print(f"[{ts}]")
            for name, value in data.items():
                altitude = mgr.calculate_altitude(value)
                print(f"['{name}', '{value:.2f}hPa', '{altitude:.2f}m']")
            print("=" * 50)

            time.sleep(0.5)

    except KeyboardInterrupt:
        print("프로그램 종료")

if __name__ == "__main__":
    main()