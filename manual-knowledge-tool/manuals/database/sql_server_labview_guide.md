# SQL Server / MariaDB LabVIEW 연동 가이드

## 1. 연결 문자열 (Connection String)

### SQL Server (로컬)

```
Provider=SQLOLEDB;Data Source=.\SQLEXPRESS;Initial Catalog=측정DB;
Integrated Security=SSPI;Connection Timeout=30;
```

### SQL Server (원격)

```
Provider=SQLOLEDB;Data Source=192.168.1.100\SQLEXPRESS;
Initial Catalog=측정DB;User ID=sa;Password=yourpass;
Connection Timeout=30;Command Timeout=60;
```

### MariaDB / MySQL

```
Driver={MariaDB ODBC 3.1 Driver};Server=localhost;Port=3306;
Database=sensor_db;User=labview;Password=yourpass;Option=3;
```

---

## 2. 테이블 설계 (측정 데이터 로깅)

### 기본 측정 테이블

```sql
CREATE TABLE sensor_log (
    id          BIGINT IDENTITY(1,1) PRIMARY KEY,
    log_time    DATETIME2(3) NOT NULL DEFAULT GETDATE(),
    tag_name    NVARCHAR(50) NOT NULL,
    value       FLOAT,
    unit        NVARCHAR(20),
    quality     TINYINT DEFAULT 1   -- 1=Good, 0=Bad
);

CREATE INDEX ix_sensor_log_time ON sensor_log (log_time);
CREATE INDEX ix_sensor_log_tag  ON sensor_log (tag_name, log_time);
```

### 이벤트/알람 테이블

```sql
CREATE TABLE event_log (
    id          BIGINT IDENTITY(1,1) PRIMARY KEY,
    event_time  DATETIME2(3) NOT NULL DEFAULT GETDATE(),
    event_type  NVARCHAR(20),  -- 'ALARM', 'WARNING', 'INFO'
    description NVARCHAR(200),
    value       FLOAT
);
```

---

## 3. Prepared Statement 예시 (LabVIEW ADO)

### LabVIEW 에서 Prepare → Execute 순서

```
[초기화 (루프 밖)]
  DB Open Connection → connection reference
  DB Tools Prepare Statement.vi
    SQL: "INSERT INTO sensor_log (log_time, tag_name, value) VALUES (?, ?, ?)"
    → statement reference

[루프 안]
  DB Tools Set Prepared Parameters.vi
    parameters: [현재시간, 태그명, 측정값]
  DB Tools Execute Prepared Statement.vi

[종료 (루프 밖)]
  DB Tools Destroy Statement.vi
  DB Close Connection.vi
```

---

## 4. Transaction 처리

### 단건 Insert vs Transaction 묶음

| 방식 | Insert 100건 소요 시간 (참고값) |
|-----|--------------------------|
| 단건 Auto-commit | ~5,000 ms |
| Transaction 100건 일괄 | ~50 ms |

### LabVIEW Transaction 구현

```
DB Begin Transaction.vi → transaction reference

[루프: 100번 반복]
  DB Tools Execute Prepared Statement.vi

DB Commit Transaction.vi   ← 100건 한꺼번에 디스크에 기록
```

Transaction 중 에러 발생 시:
```
DB Rollback Transaction.vi   ← 전체 취소
```

---

## 5. 성능 최적화

### Connection Pool

SQL Server 드라이버는 기본적으로 Connection Pooling 을 지원한다.
동일 Connection String 으로 열고 닫으면 물리적 연결을 재사용해 오버헤드를 줄인다.

### 인덱스 관리

```sql
-- 느린 쿼리 확인
SELECT TOP 10 total_elapsed_time/execution_count AS avg_ms,
       total_logical_reads/execution_count AS avg_reads,
       SUBSTRING(st.text, 1, 200) AS query_text
FROM sys.dm_exec_query_stats qs
CROSS APPLY sys.dm_exec_sql_text(sql_handle) st
ORDER BY avg_ms DESC;
```

### 데이터 보관 정책

```sql
-- 3개월 이전 데이터 삭제 (정기 실행)
DELETE FROM sensor_log
WHERE log_time < DATEADD(MONTH, -3, GETDATE());
```

---

## 6. 연결 에러 대처

| 에러 코드 | 원인 | 확인 항목 |
|---------|------|---------|
| -2147467259 | DB 연결 실패 | 서버 주소, 포트, 방화벽 |
| -2147217900 | SQL 문법 오류 | 쿼리 문자열 확인 |
| -2147217887 | 제약 조건 위반 | 중복 키, NOT NULL 열 |
| Timeout | 쿼리 실행 초과 | Command Timeout 값 증가, 인덱스 확인 |

### LabVIEW Error Cluster 처리

```
DB Tools Execute.vi ──→ error out ──→ Simple Error Handler.vi
                                       (에러 코드 + 메시지 로깅)
```

Error Cluster 를 처리하지 않으면 에러 발생 시 VI 가 정지해 데이터 누락이 발생한다.
