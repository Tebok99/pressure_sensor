from machine import I2C, Pin
import time

# 상수 정의
ADDRESS = 0x77
REG_CHIP_ID = 0x00
REG_CMD = 0x7E
REG_OSR = 0x1C
REG_ODR = 0x1D
REG_IIR = 0x1F
REG_PWR_CTRL = 0x1B
REG_STATUS = 0x03
REG_DATA = 0x04
CALIB_START = 0x31
CALIB_LEN = 21

# I2C 설정
i2c = I2C(1, sda=Pin(6), scl=Pin(7), freq=400000)

# CHIP_ID 확인
logs = []
start_time = time.ticks_ms()
try:
    chip_id = i2c.readfrom_mem(ADDRESS, REG_CHIP_ID, 1)[0]
    success = (chip_id == 0x50)
    if not success:
        raise ValueError("Invalid CHIP_ID")
except Exception as e:
    success = False
    logs.append(f"Check CHIP_ID: failed with {e}")
end_time = time.ticks_ms()
logs.append(f"Check CHIP_ID: time={time.ticks_diff(end_time, start_time)}ms, success={success}")
if not success:
    print("Sensor not found")
    raise SystemExit

# 소프트 리셋
def soft_reset(i2c, address):
    global logs
    start_time = time.ticks_ms()
    try:
        i2c.writeto_mem(address, REG_CMD, b'\xB6')
        success = True
    except Exception as e:
        success = False
        logs.append(f"Soft reset: failed with {e}")
    end_time = time.ticks_ms()
    logs.append(f"Soft reset: time={time.ticks_diff(end_time, start_time)}ms, success={success}")
    time.sleep_ms(10)

soft_reset(i2c, ADDRESS)
time.sleep_ms(10)  # 리셋 후 대기

# 보정 데이터 읽기
def read_calibration(i2c, address):
    global logs
    start_time = time.ticks_ms()
    try:
        calib_data = i2c.readfrom_mem(address, CALIB_START, CALIB_LEN)
        # 보정 계수 파싱
        t1 = (calib_data[1] << 8) | calib_data[0]
        t2 = (calib_data[3] << 8) | calib_data[2]
        t3 = calib_data[4]
        if t3 & 0x80:
            t3 -= 0x100
        p1 = (calib_data[6] << 8) | calib_data[5]
        if p1 & 0x8000:
            p1 -= 0x10000
        p2 = (calib_data[8] << 8) | calib_data[7]
        if p2 & 0x8000:
            p2 -= 0x10000
        p3 = calib_data[9]
        if p3 & 0x80:
            p3 -= 0x100
        p4 = calib_data[10]
        if p4 & 0x80:
            p4 -= 0x100
        p5 = (calib_data[12] << 8) | calib_data[11]
        p6 = (calib_data[14] << 8) | calib_data[13]
        p7 = calib_data[15]
        if p7 & 0x80:
            p7 -= 0x100
        p8 = calib_data[16]
        if p8 & 0x80:
            p8 -= 0x100
        p9 = (calib_data[18] << 8) | calib_data[17]
        if p9 & 0x8000:
            p9 -= 0x10000
        p10 = calib_data[19]
        if p10 & 0x80:
            p10 -= 0x100
        p11 = calib_data[20]
        if p11 & 0x80:
            p11 -= 0x100
        # 보정 공식 적용
        par_t1 = t1 * 256.0
        par_t2 = t2 / 1073741824.0
        par_t3 = t3 / 281474976710656.0
        par_p1 = (p1 - 16384.0) / 1048576.0
        par_p2 = (p2 - 16384.0) / 536870912.0
        par_p3 = p3 / 4294967296.0
        par_p4 = p4 / 137438953472.0
        par_p5 = p5 * 8.0
        par_p6 = p6 / 64.0
        par_p7 = p7 / 256.0
        par_p8 = p8 / 32768.0
        par_p9 = p9 / 281474976710656.0
        par_p10 = p10 / 281474976710656.0
        par_p11 = p11 / 36893488147419103232.0
        success = True
        result = {
            'par_t1': par_t1, 'par_t2': par_t2, 'par_t3': par_t3,
            'par_p1': par_p1, 'par_p2': par_p2, 'par_p3': par_p3,
            'par_p4': par_p4, 'par_p5': par_p5, 'par_p6': par_p6,
            'par_p7': par_p7, 'par_p8': par_p8, 'par_p9': par_p9,
            'par_p10': par_p10, 'par_p11': par_p11
        }
    except Exception as e:
        success = False
        result = None
        logs.append(f"Read calibration: failed with {e}")
    end_time = time.ticks_ms()
    logs.append(f"Read calibration: time={time.ticks_diff(end_time, start_time)}ms, success={success}")
    return result, success

cal, success = read_calibration(i2c, ADDRESS)
if not success:
    print("Failed to read calibration data")
    raise SystemExit

# 보정 함수
def compensate_temperature(uncomp_temp, cal):
    partial_data1 = uncomp_temp - cal['par_t1']
    partial_data2 = partial_data1 * cal['par_t2']
    t_lin = partial_data2 + (partial_data1 * partial_data1) * cal['par_t3']
    return t_lin

def compensate_pressure(uncomp_press, t_lin, cal):
    partial_data1 = cal['par_p6'] * t_lin
    partial_data2 = cal['par_p7'] * (t_lin ** 2)
    partial_data3 = cal['par_p8'] * (t_lin ** 3)
    partial_out1 = cal['par_p5'] + partial_data1 + partial_data2 + partial_data3
    partial_data1 = cal['par_p2'] * t_lin
    partial_data2 = cal['par_p3'] * (t_lin ** 2)
    partial_data3 = cal['par_p4'] * (t_lin ** 3)
    partial_out2 = uncomp_press * (cal['par_p1'] + partial_data1 + partial_data2 + partial_data3)
    partial_data1 = uncomp_press ** 2
    partial_data2 = cal['par_p9'] + cal['par_p10'] * t_lin
    partial_data3 = partial_data1 * partial_data2
    partial_data4 = partial_data3 + (uncomp_press ** 3) * cal['par_p11']
    comp_press = partial_out1 + partial_out2 + partial_data4
    return comp_press

# 작업 수행 및 로깅
def perform_action(action_name, func, logs):
    start_time = time.ticks_ms()
    try:
        result = func()
        success = True
    except Exception as e:
        result = None
        success = False
        logs.append(f"{action_name}: failed with {e}")
    end_time = time.ticks_ms()
    elapsed = time.ticks_diff(end_time, start_time)
    logs.append(f"{action_name}: time={elapsed}ms, success={success}")
    return result, success

# 측정 대기
def wait_for_measurement(i2c, address, logs):
    start_time = time.ticks_ms()
    timeout = 1000  # 1 second
    while True:
        try:
            status = i2c.readfrom_mem(address, REG_STATUS, 1)[0]
            if (status & 0x60) == 0x60:
                break
            if time.ticks_diff(time.ticks_ms(), start_time) > timeout:
                logs.append("Wait for measurement: timeout")
                return False
            time.sleep_ms(1)
        except Exception as e:
            logs.append(f"Wait for measurement: failed with {e}")
            return False
    end_time = time.ticks_ms()
    logs.append(f"Wait for measurement: time={time.ticks_diff(end_time, start_time)}ms, success=True")
    return True

# 데이터 처리
def read_data():
    # 원시 데이터 읽기
    raw_data, success = perform_action("Read raw data", lambda: i2c.readfrom_mem(ADDRESS, REG_DATA, 6), logs)
    if not success:
        return None
    # 원시 기압 및 온도 추출
    raw_press = raw_data[0] | (raw_data[1] << 8) | (raw_data[2] << 16)
    raw_temp = raw_data[3] | (raw_data[4] << 8) | (raw_data[5] << 16)
    # 온도 보정
    start_time = time.ticks_ms()
    try:
        t_lin = compensate_temperature(raw_temp, cal)
        success = True
    except Exception as e:
        t_lin = None
        success = False
        logs.append(f"Compensate temperature: failed with {e}")
    end_time = time.ticks_ms()
    logs.append(f"Compensate temperature: time={time.ticks_diff(end_time, start_time)}ms, success={success}")
    if not success:
        return None
    # 기압 보정
    start_time = time.ticks_ms()
    try:
        comp_press = compensate_pressure(raw_press, t_lin, cal)
        success = True
    except Exception as e:
        comp_press = None
        success = False
        logs.append(f"Compensate pressure: failed with {e}")
    end_time = time.ticks_ms()
    logs.append(f"Compensate pressure: time={time.ticks_diff(end_time, start_time)}ms, success={success}")
    if not success:
        return None
    # 결과 출력
    logs.append(f"Mode: {mode}, Measurement {i + 1}: Temp = {t_lin:.2f} ℃, Press = {comp_press:.2f} Pa")
    print(f"Mode: {mode}, Measurement {i + 1}: Temp = {t_lin:.2f} ℃, Press = {comp_press:.2f} Pa")
    return None

# 모드 정의
modes = {
    'low_power': {'osr_value': 0, 'pwr_ctrl': (1 << 4) | 3},  # osr_p=x1, osr_t=x1, forced mode
    'normal': {'osr_value': (1 << 3) | 4, 'pwr_ctrl': (3 << 4) | 3}  # osr_t=x2, osr_p=x16, normal mode
}

# 각 모드에서 측정 수행
for mode in ['low_power', 'normal']:
    osr_value = modes[mode]['osr_value']
    pwr_ctrl = modes[mode]['pwr_ctrl']

    # perform_action("Set to sleep mode", lambda: i2c.writeto_mem(ADDRESS, REG_PWR_CTRL, b'\x00'), logs)

    if mode == 'normal':
        soft_reset(i2c, ADDRESS)
        time.sleep_ms(10)  # 리셋 후 대기

        i2c.writeto_mem(ADDRESS, REG_ODR, b'\x02')
        i2c.writeto_mem(ADDRESS, REG_IIR, b'\x02')
        perform_action("Set OSR", lambda: i2c.writeto_mem(ADDRESS, REG_OSR, bytes([osr_value])), logs)
        time.sleep_ms(20)

        perform_action("Set to normal mode", lambda: i2c.writeto_mem(ADDRESS, REG_PWR_CTRL, bytes([pwr_ctrl])), logs)

        for i in range(10):
            # 측정 대기
            success = wait_for_measurement(i2c, ADDRESS, logs)
            if not success:
                continue
            read_data()
            time.sleep_ms(20)  # Wait for next measurement at 50Hz
    else:   # 'low power mode' 측정 시작
        logs.append("Set to low power mode")
        perform_action("Set OSR", lambda: i2c.writeto_mem(ADDRESS, REG_OSR, bytes([osr_value])), logs)
        time.sleep_ms(20)
        for i in range(10):
            perform_action("Start measurement", lambda: i2c.writeto_mem(ADDRESS, REG_PWR_CTRL, bytes([pwr_ctrl])), logs)
            # 측정 대기
            success = wait_for_measurement(i2c, ADDRESS, logs)
            if not success:
                continue
            read_data()
            time.sleep_ms(100)  # Wait for next measurement after 100 ms

# 로그 파일 작성
try:
    with open("log.txt", "w") as f:
        for log in logs:
            f.write(log + "\n")
    print("Log file written: log.txt")
except Exception as e:
    print(f"Failed to write log file : {e}")