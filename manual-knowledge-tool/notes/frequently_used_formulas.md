# 자주 쓰는 공식 모음

## 1. 인버터 / 모터

### 주파수 ↔ 속도 변환

```
N (rpm) = (120 × f) / P
f (Hz)  = (N × P) / 120

N  : 동기 회전속도 [rpm]
f  : 주파수 [Hz]
P  : 극수 (Poles)
```

예: 4극 모터, 60 Hz → 1800 rpm (동기)  
실제 속도는 슬립(Slip) 만큼 작음 (보통 1700~1750 rpm)

### 토크 ↔ 전류 (개략)

```
T ≈ (V × I × η × PF × 9550) / N

T  : 토크 [N·m]
V  : 전압 [V] (선간)
I  : 전류 [A]
η  : 효율 (0.85~0.95)
PF : 역률 (0.8~0.95)
N  : 회전속도 [rpm]
```

---

## 2. 로드셀 / 장력 계산

### 4-20 mA 아날로그 공학값 변환

```
공학값 = (I - 4) / (20 - 4) × 정격용량

I      : 증폭기 출력 전류 [mA]
정격용량: 로드셀 정격 [kgf 또는 N]
```

### PLC AI count → 공학값 (4-20 mA 기준)

```
공학값 = (count - count_zero) / (count_span - count_zero) × 정격용량

count_zero : 4 mA 시 count (보통 0)
count_span : 20 mA 시 count (모듈에 따라 4000, 8000, 16000, 32767 등)
```

### 로드셀 출력 (mV/V)

```
출력 [mV/V] = 로드셀_출력 [mV] / 공급전압 [V]
실제 하중  = (출력 / 정격출력) × 정격용량
```

---

## 3. Modbus 레지스터 계산

### 16bit 부호있는 정수 (Signed Int16)

```
값 범위: -32768 ~ +32767
음수 표현: 65536 + 음수값
예: -1 → 65535 (0xFFFF)
```

### 32bit 정수 (PLC에서 2 레지스터 사용)

```
상위 레지스터 × 65536 + 하위 레지스터 = 32bit 값
```

### 주파수지령 레지스터 계산 (S300 예시)

```
레지스터 값 = 목표주파수[Hz] × 100
예: 30 Hz → 3000
```

---

## 4. 전력 / 에너지

### 3상 전력

```
P [W]   = √3 × V × I × PF
S [VA]  = √3 × V × I
Q [VAR] = √3 × V × I × sin(θ)
PF      = cos(θ) = P / S
```

### 전력량 (kWh) 계산

```
E [kWh] = P [kW] × t [h]
펄스 방식: E = 펄스 수 / 펄스 레이트 [pulse/kWh]
예: 1000 pulse/kWh, 5000 펄스 → 5 kWh
```

### CT (전류 변성기) 실제 전류

```
실제 전류 [A] = 측정값 [A] × CT비율
예: CT 200/5A, 측정값 3.5 A → 실제 140 A
```

---

## 5. 신호 처리

### 1차 저역통과 필터 (LPF) 시정수

```
Y(k) = α × X(k) + (1 - α) × Y(k-1)

α  = Δt / (τ + Δt)
Δt : 샘플링 주기 [s]
τ  : 시정수 [s]
```

### 이동평균 (Moving Average)

```
MA(k) = (X(k) + X(k-1) + ... + X(k-N+1)) / N

N : 윈도우 크기 (클수록 부드럽지만 응답 느림)
```

---

## 6. RS-485 / Modbus RTU 타이밍

### CRC-16 (Modbus)

```
다항식: 0xA001 (역순 표현)
초기값: 0xFFFF
처리: 각 바이트에 대해 비트 연산
```

### 문자 간 침묵 시간 (Character Timeout)

```
3.5 문자 × (1 / 보레이트) × 비트 수 = 최소 프레임 구분 시간
예: 9600 bps, 11 bit/char → 3.5 × 11 / 9600 ≈ 4.0 ms
```

---

## 7. LabVIEW / DB

### Producer-Consumer 패턴 개요

```
Producer Loop : 센서 데이터 수집 → Queue에 Enqueue
Consumer Loop : Queue에서 Dequeue → DB Insert

- Queue 크기: 수집 주기 × 예상 지연 시간으로 설정
- Consumer가 느려도 Producer 블로킹 방지
```

### SQL Insert 성능 (경험치)

| 방식 | 대략적 Insert 속도 |
|-----|-----------------|
| 매번 연결 + Execute SQL | 수백 ms/건 |
| 연결 유지 + Execute SQL | 10~50 ms/건 |
| 연결 유지 + Prepared Statement | 1~10 ms/건 |
| Transaction 묶음 + Prepared | 0.1~1 ms/건 |
