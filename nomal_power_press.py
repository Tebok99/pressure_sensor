from sensor_utils import SensorManager
import time


def main():
    mgr = SensorManager()

    # 고정밀 모드 설정
    mgr.bmp280.set_normal_mode()
    mgr.dps310.set_normal_mode()
    mgr.bmp388.set_normal_mode()

    # 센서 매핑 딕셔너리
    sensor_map = {
        'BMP280': mgr.bmp280,
        'DPS310': mgr.dps310,
        'BMP388': mgr.bmp388
    }

    # 모드별 주기 결정
    mode = 'normal'
    periods = SensorManager.MODES[mode]
    last_time = {k: 0 for k in periods}
    vals = {k: None for k in periods}

    try:
        while True:
            now = time.ticks_ms()
            for name, period in periods.items():
                # 센서별로 주기에 따라 측정
                if time.ticks_diff(now, last_time[name]) >= int(period * 1000):
                    vals[name] = sensor_map.get(name).pressure
                    last_time[name] = now

            ts = mgr.format_timestamp()
            print(f"[{ts}]")
            for name in periods:
                value = vals[name]
                if value is not None:
                    altitude = mgr.calculate_altitude(value)
                    print(f"['{name}', '{value:.2f}hPa', '{altitude:.2f}m']")
            print("=" * 50)

            time.sleep_ms(10)

    except KeyboardInterrupt:
        print("프로그램 종료")

if __name__ == "__main__":
    main()