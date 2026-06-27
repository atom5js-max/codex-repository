# LS XGB PLC Modbus RTU 마스터 설정 가이드

## 1. Modbus RTU 통신 개요

XGB PLC 는 내장 RS-485 포트 또는 통신 모듈을 통해 Modbus RTU 마스터로 동작한다.

**지원 Function Code**:
- FC 01: Read Coil Status
- FC 02: Read Input Status
- FC 03: Read Holding Registers
- FC 04: Read Input Registers
- FC 06: Write Single Register
- FC 16: Write Multiple Registers

---

## 2. 통신 파라미터 설정

XG5000 소프트웨어에서 설정:

| 항목 | 설정 위치 | 일반 설정값 |
|-----|---------|------------|
| Baudrate | 통신 파라미터 | 9600 bps |
| Parity | 통신 파라미터 | None |
| Stop Bit | 통신 파라미터 | 1 |
| Timeout | 통신 파라미터 | 200 ms |
| Station No | 슬레이브 장치 설정 | 1~247 |

---

## 3. Modbus 명령 블록 (MBUS_RD / MBUS_WR)

XGB 래더 프로그램에서 Modbus 통신을 위해 MBUS_RD, MBUS_WR 펑션블록 사용.

### MBUS_RD (Read Holding Registers, FC 03)

```
MBUS_RD
  EN      : 실행 트리거
  PORT    : COM 포트 번호
  SLAVE   : 슬레이브 국번 (1~247)
  FUNC    : Function Code (3 = Read Holding Registers)
  ADDR    : 시작 레지스터 주소
  CNT     : 읽을 레지스터 수
  DATA    : 수신 데이터 저장 주소
  DONE    : 완료 비트
  ERR     : 에러 비트
  ERRCODE : 에러 코드
```

### MBUS_WR (Write Single Register, FC 06)

```
MBUS_WR
  EN      : 실행 트리거
  PORT    : COM 포트 번호
  SLAVE   : 슬레이브 국번
  FUNC    : Function Code (6 = Write Single Register)
  ADDR    : 대상 레지스터 주소
  DATA    : 쓸 데이터
  DONE    : 완료 비트
  ERR     : 에러 비트
```

---

## 4. Timeout 및 에러 처리

CRC 에러, Timeout 발생 시 ERR 비트가 ON 된다.
ERRCODE 레지스터에서 구체적 에러 코드를 확인한다.

**일반적인 에러 원인**:
- Station No 중복 → 응답 충돌 → CRC 에러
- 종단저항 미설치 → 신호 반사 → 간헐적 에러
- Timeout 값이 너무 짧음 → 슬레이브 응답 시간 초과
- Baudrate 불일치 → 통신 자체 불가
- Parity / Stop Bit 불일치

---

## 5. 아날로그 입력 모듈 (AI)

### 4-20mA 입력 설정

XGI-AD4A 또는 XGI-AD8A 모듈 사용 시:
- 입력 범위: 4-20 mA (또는 0-20 mA, 0-10V)
- 분해능: 16비트 (0~32767 count)
- 4 mA → count 0
- 20 mA → count 32767 (모듈마다 다름, 사양서 확인)

**스케일링 공식**:
```
공학값 = (count × (최대 공학값 - 최소 공학값)) / 32767 + 최소 공학값
```

### Analog Input 관련 주의사항

- 입력 범위(Range) 설정이 현장 계기 출력과 반드시 일치해야 함
- 배선 단선 시 Burnout 처리 (모듈 설정에 따라 count 최소 또는 최대로 고정됨)
- Filter 상수: 노이즈가 심한 현장에서는 100~500 ms 설정
- 공통단(COM) 전위 불일치 시 오프셋 오차 발생

---

## 6. 디지털 입력/출력 (DI/DO)

### 입력 신호 확인 방법

XG5000 → 모니터링 → IO 모니터링에서 실시간 ON/OFF 확인 가능.

입력 신호가 들어오지 않을 때:
- DI LED 점등 여부 확인
- 공통단(COM) 전압 확인 (DC 24V)
- 외부 접점 및 배선 확인
- 강제 입력(Force) 잠금 여부 확인

### 고속카운터 (HSC: High Speed Counter)

전력량계 펄스 입력 등 고속 신호는 일반 DI 대신 HSC 사용 권장.
XGB 내장 HSC 채널: HSC0~HSC3 (기종마다 다름)

설정 항목:
- 카운터 모드 (단상/2상)
- 카운터 방향 (UP/DOWN)
- 프리셋 값 (오버플로우 전 리셋 기준)
