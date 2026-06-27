# LS S300 인버터 빠른 참조 매뉴얼

## 1. 주파수지령 (Frequency Reference) 설정

### Command Source 파라미터 (DRV-05)

주파수지령 소스를 결정하는 파라미터.

| 설정값 | 의미 |
|--------|------|
| 0 | Keypad (조작패널) |
| 1 | V1 단자 (0-10V) |
| 2 | I 단자 (4-20mA) |
| 3 | RS-485 Communication |
| 4 | 다단속 (Multi-Step Speed) |

**Speed Command 를 RS-485(Modbus)로 받으려면 DRV-05 = 3 으로 설정해야 한다.**

---

## 2. 운전지령 (Run Command) 설정

### DRV-06: Run Command Source

| 설정값 | 의미 |
|--------|------|
| 0 | Keypad |
| 1 | FX/RX 단자 (디지털 입력) |
| 2 | RS-485 Communication |

Speed Command 와 Run Command 소스는 **별도 파라미터**이므로 둘 다 확인해야 한다.

---

## 3. Modbus RTU 통신 설정

### COM 파라미터 그룹

| 파라미터 | 기능 | 기본값 |
|---------|------|--------|
| COM-01 | Station No (국번) | 1 |
| COM-02 | Baudrate (통신속도) | 9600 |
| COM-03 | Parity (패리티) | None (0) |
| COM-04 | Stop Bit | 1 |
| COM-05 | Response Delay | 5 ms |

Baudrate 설정값: 1200 / 2400 / 4800 / 9600 / 19200 / 38400 / 57600 / 115200

---

## 4. 주요 Modbus 레지스터 (Function Code 03/06)

| 레지스터 | 기능 | 접근 |
|---------|------|------|
| 0x0001 | Run Command | Read/Write |
| 0x0002 | Frequency Reference (단위: 0.01 Hz) | Read/Write |
| 0x000C | Inverter Status | Read Only |
| 0x000D | Output Frequency | Read Only |
| 0x000E | Output Current (단위: 0.1A) | Read Only |
| 0x000F | Output Voltage | Read Only |
| 0x0010 | DC Link Voltage | Read Only |

주파수지령 레지스터에 3000 을 Write하면 30.00 Hz 지령이다.

---

## 5. 트립/폴트 (Trip / Fault)

### 주요 Fault Code

| 코드 | 이름 | 원인 |
|-----|------|------|
| OC | Overcurrent (과전류) | 부하 과다, 가감속 너무 빠름, 모터 단락 |
| OV | Overvoltage (과전압) | 감속 너무 빠름, 회생에너지 과다 |
| UV | Undervoltage (저전압) | 전원 불안정 |
| OH | Overheat (과열) | 주변 온도 높음, 환기 불량 |
| GF | Ground Fault (지락) | 모터 또는 케이블 지락 |

**Fault History**: 마지막 5개 트립 이력을 TRP-xx 파라미터에서 확인 가능.

---

## 6. 가감속 시간 설정

| 파라미터 | 기능 | 단위 |
|---------|------|------|
| BAS-09 | Acceleration Time (가속 시간) | 초 (s) |
| BAS-10 | Deceleration Time (감속 시간) | 초 (s) |

과전압(OV) 트립 시 Deceleration Time 을 늘리는 것을 검토한다.

---

## 7. 아날로그 입력 (Analog Input)

V1 단자: 0-10V 입력  
I 단자: 4-20mA 입력  

Analog Input 입력 범위와 주파수 범위는 IN 파라미터 그룹에서 설정한다.

---

## 8. RS-485 배선 주의사항

- RS-485 A(+) / B(-) 극성 정확히 확인
- 버스 양 끝단에 종단저항 120Ω 설치
- 데이지체인(직렬) 연결, T-분기 금지
- 쉴드 케이블 사용, 한쪽만 접지
- Station No(국번) 중복 금지
