# 산업설비 기술자료 검색 도구

현장어로 검색하면 매뉴얼어로 확장해 관련 기술문서를 빠르게 찾아주는 로컬 검색 도구.

인터넷 연결 불필요. 외부 API 없음. Python 표준 + YAML.

---

## 기능 요약

| 단계 | 기능 |
|-----|------|
| 1 | `manuals/` + `notes/` 폴더의 .md / .txt / .pdf 파일 자동 로드 |
| 2 | 파일 경로를 기준으로 제품군 자동 분류 (inverter / plc / loadcell 등) |
| 3 | `synonym_rules.yaml` 로 현장어 → 매뉴얼어 확장 |
| 4 | 원본 + 확장 키워드로 관련 문단 검색 |
| 5 | 결과를 `output/search_result.md` 로 저장 |
| 6 | 현장 확인 항목 목록 자동 생성 |

---

## 폴더 구조

```
manual-knowledge-tool/
├─ manuals/
│  ├─ inverter/          ← 인버터 매뉴얼 (.md, .txt, .pdf)
│  ├─ plc/               ← PLC 매뉴얼
│  ├─ loadcell/          ← 로드셀·증폭기 매뉴얼
│  ├─ instruments/       ← 계측기 매뉴얼
│  ├─ labview/           ← LabVIEW 관련 문서
│  └─ database/          ← DB 관련 문서
├─ notes/
│  ├─ troubleshooting_cases.md    ← 현장 트러블슈팅 사례
│  ├─ commissioning_records.md    ← 시운전 기록
│  └─ frequently_used_formulas.md ← 자주 쓰는 공식
├─ rules/
│  ├─ synonym_rules.yaml ← 현장어-매뉴얼어 매핑 규칙
│  └─ search_rules.yaml  ← 검색 동작 설정
├─ output/
│  └─ search_result.md   ← 검색 결과 저장 위치
└─ src/
   ├─ main.py            ← CLI 진입점
   ├─ document_loader.py ← 파일 로드 + 분류
   ├─ pdf_extractor.py   ← PDF 텍스트 추출
   ├─ text_chunker.py    ← 문단 분할
   ├─ synonym_expander.py← 현장어 확장
   ├─ keyword_search.py  ← 키워드 검색
   └─ result_writer.py   ← Markdown 결과 저장
```

---

## 설치 방법

### 1. Python 환경 (3.9 이상 권장)

```bash
python --version
```

### 2. 의존성 설치

```bash
cd manual-knowledge-tool
pip install -r requirements.txt
```

PDF 지원이 필요 없으면 `pdfplumber` 없이도 동작한다.  
PDF 지원이 필요하면:

```bash
pip install pdfplumber
# 또는
pip install pypdf
```

---

## 실행 방법

`src/` 폴더에서 실행한다.

```bash
cd manual-knowledge-tool/src
```

### 단일 검색어 모드

```bash
python main.py "S300 속도지령 안 먹음"
python main.py "Modbus 통신 안 됨"
python main.py "로드셀 값 튐"
python main.py "LabVIEW DB 저장 느림"
python main.py "전력량계 펄스 계산"
python main.py "PLC 아날로그 값 이상"
```

### 대화형 모드 (여러 검색어를 연속 입력)

```bash
python main.py --interactive
# 또는
python main.py -i
```

### 로드된 파일 목록 확인

```bash
python main.py --list-files
# 또는
python main.py -l
```

### 결과 수 조정

```bash
python main.py "인버터 트립" --max-results 15
```

### 상세 로그 출력

```bash
python main.py "속도 안 먹음" --verbose
```

---

## 예시 검색어 목록

| 입력 (현장어) | 발동 규칙 |
|-------------|---------|
| `S300 속도지령 안 먹음` | speed_command_problem |
| `인버터 주파수 안 바뀜` | speed_command_problem |
| `상한 주파수 걸림` | inverter_speed_no_change |
| `최고속도 안 나옴` | inverter_speed_no_change |
| `인버터 OC 트립` | inverter_trip |
| `인버터 가속 안 됨` | inverter_accel_problem |
| `로드셀 값 튐` | loadcell_noise |
| `무부하 값 흔들림` | loadcell_noise |
| `Modbus 통신 안 됨` | modbus_comm_problem |
| `HMI 통신 안 됨` | hmi_comm_problem |
| `유량계 RS485` | flowmeter_issue |
| `유량계 통신 안 됨` | flowmeter_issue |
| `PLC 아날로그 값 이상` | analog_input_issue |
| `압력 센서 이상` | pressure_sensor_issue |
| `온도 값 이상` / `PT100 이상` | temperature_sensor_issue |
| `DI 신호 안 읽힘` | plc_io_check |
| `PLC 에러` / `스캔 타임 이상` | plc_program_error |
| `PLC 스캔 느림` | plc_scan_slow |
| `LabVIEW DB 저장 느림` | labview_db_slow |
| `전력량계 펄스 계산` | power_meter_pulse |
| `영점 조정` / `캘리브레이션` | calibration_general |

---

## 매뉴얼 파일 추가 방법

1. 해당 제품군 폴더에 파일 복사

```
manuals/inverter/LS_iV5_manual.pdf
manuals/plc/Mitsubishi_iQR_guide.txt
manuals/instruments/WT300_power_meter.md
```

2. 다시 검색하면 자동으로 로드된다 (재시작 불필요, 대화형 모드는 재실행 필요)

---

## 현장어 규칙 추가 방법

`rules/synonym_rules.yaml` 에 새 규칙을 추가한다.

```yaml
my_new_rule:
  field_terms:
    - 현장에서 쓰는 표현 1
    - 현장에서 쓰는 표현 2
  manual_terms:
    - Manual Keyword A
    - 매뉴얼 키워드 B
  check_items:
    - 확인할 항목 1
    - 확인할 항목 2
```

---

## 검색 결과 형식

`output/search_result.md` 에 저장되며 다음 항목을 포함한다:

- 검색어 요약 (원본 / 발동 규칙 / 확장 키워드)
- 결과별: 제품군, 파일명, 위치(단락#/페이지), 매칭 키워드, 주변 문장, 매칭 유형
- 현장 확인 항목 체크리스트

---

## 향후 확장 계획

현재 구조는 다음 기능을 붙일 수 있도록 모듈화되어 있다.

| 모듈 | 향후 확장 |
|-----|---------|
| `document_loader.py` | 파일 캐시, 변경 감지 자동 재로드 |
| `keyword_search.py` | 벡터 임베딩 기반 시맨틱 검색으로 교체 |
| `result_writer.py` | HTML 보고서, Excel 내보내기 |
| `main.py` | 웹 UI (Flask/FastAPI), 터미널 UI |
| 신규 모듈 | LLM 요약 (로컬 Ollama 또는 API) |

---

## 주의사항

- 이 도구는 **매뉴얼 위치를 찾아주는 검색 도구**이다.
- AI 가 원인을 단정하거나 조치를 확정하지 않는다.
- 현장 확인 항목은 참고용 체크리스트이며, 최종 판단은 담당 엔지니어가 한다.
