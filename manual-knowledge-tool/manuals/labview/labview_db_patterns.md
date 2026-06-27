# LabVIEW 데이터베이스 연동 패턴

## 1. Producer-Consumer 패턴 (데이터 수집 + DB 저장)

데이터 수집 속도와 DB Insert 속도가 다를 때 Queue를 버퍼로 사용한다.

```
[Producer Loop] → Queue → [Consumer Loop]
  100 ms 수집        1000개      500 ms Insert
```

**Queue 설정**:
- 크기: 예상 지연 시간 동안 누적될 데이터 수 × 1.5 이상
- Queue 가 꽉 차면(Enqueue Timeout) 데이터 누락 발생
- Queue 누적량을 주기적으로 모니터링해 DB 성능 지표로 활용

---

## 2. DB 연결 관리

### 잘못된 패턴 (성능 저하)

```
[루프 시작]
  DB Open Connection   ← 루프마다 연결
  Execute SQL Insert
  DB Close Connection  ← 루프마다 종료
[루프 반복]
```

루프마다 연결/종료를 반복하면 연결 오버헤드가 누적되어 Insert 지연이 발생한다.

### 올바른 패턴 (권장)

```
[초기화]
  DB Open Connection   ← 1회만 연결

[루프]
  Prepare Statement    ← 루프 밖에 위치
  Execute Prepared     ← 파라미터만 교체

[종료]
  DB Close Connection  ← 1회만 종료
```

---

## 3. Prepared Statement 사용법

Prepared Statement 는 쿼리를 한 번만 파싱하고 파라미터만 교체해 실행하므로
매번 Execute SQL 하는 것보다 훨씬 빠르다.

**위치 규칙**:
- `DB Tools Prepare Statement.vi` → **루프 밖** (초기화 구간)
- `DB Tools Execute Prepared Statement.vi` → **루프 안** (반복 구간)
- `DB Tools Destroy Statement.vi` → **루프 밖** (종료 구간)

---

## 4. Transaction (일괄 커밋)

개별 Insert 마다 자동 커밋(Auto-commit)되면 Disk I/O 가 자주 발생해 느리다.
Transaction 으로 묶어서 한 번에 커밋하면 성능이 크게 향상된다.

```
DB Begin Transaction
  [루프: N번 Insert]
DB Commit Transaction   ← N건 한꺼번에 커밋
```

권장 Transaction 크기: 50~200건 (DB 서버 성능과 수집 주기에 따라 조정)

---

## 5. Timeout 및 Error Cluster 처리

### 연결 Timeout

DB Server 가 원격(네트워크)인 경우 Timeout 값을 충분히 설정한다.

- Connection String 의 `Connection Timeout` 파라미터
- `Command Timeout` (쿼리 실행 제한 시간)

### Error Cluster 확인

Error Cluster 를 반드시 처리해야 에러 발생 시 VI 가 멈추지 않는다.
Simple Error Handler 또는 General Error Handler 로 에러 코드와 메시지를 기록한다.

**Error Code -2147467259**: DB 연결 실패 (Connection String 또는 DB 서버 확인)  
**Error Code -2147217900**: SQL 문법 오류  
**Error Code -2147217887**: 제약 조건 위반 (중복 키 등)

---

## 6. DB Insert 성능 참고값

| 방식 | 대략적 속도 |
|-----|-----------|
| 매 루프 Open/Close + Execute SQL | 100~500 ms/건 |
| 연결 유지 + Execute SQL | 10~50 ms/건 |
| 연결 유지 + Prepared Statement | 1~10 ms/건 |
| 연결 유지 + Prepared + Transaction(100건) | 0.1~1 ms/건 |

100 ms 수집 주기라면 Prepared + Transaction 방식을 사용해야 누락 없이 저장 가능하다.
