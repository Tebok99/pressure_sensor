from sensor_utils import SensorManager
import time


def main():
    mgr = SensorManager()

    # 고정밀 모드 설정
    mgr.bmp280.set_normal_mode()
    mgr.dps310.set_normal_mode()
    mgr.bmp388.set_normal_mode()

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
                    if name == 'BMP280':
                        vals[name] = mgr.bmp280.pressure
                    elif name == 'DPS310':
                        vals[name] = mgr.dps310.pressure
                    elif name == 'BMP388':
                        vals[name] = mgr.bmp388.pressure
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