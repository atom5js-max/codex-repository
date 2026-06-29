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
| 7 | 웹 검색 결과 카드에 해당 PDF 페이지 축소 이미지와 관련 내용 표시 |
| 8 | 축소 이미지를 누르면 해당 PDF 페이지 원문과 페이지 전체 추출문 표시 |

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

## 가장 쉬운 실행 방법 (Windows)

1. 최상위 폴더의 `실행_산업설비_검색.bat`를 더블클릭한다.
   - 또는 `manual-knowledge-tool` 폴더의 `start_web.bat`를 실행한다.
2. 처음 실행할 때만 가상환경 생성과 패키지 설치가 진행된다.
3. 명령창에 표시된 접속 주소를 확인한다.

```text
PC 접속 주소     : http://localhost:5000
태블릿/스마트폰 : http://192.168.x.x:5000
```

4. PC 브라우저는 자동으로 열리며, 검색어를 입력하고 `검색`을 누른다.
5. 검색 결과의 `PDF 원문 보기 · N쪽`을 누르면 해당 PDF 페이지가 대시보드 안에서 열린다.

> 주의: `src/templates/index.html` 파일을 직접 열면 검색 API가 연결되지 않는다.
> 반드시 `start_web.bat`로 서버를 실행한 뒤 `http://localhost:5000`으로 접속한다.

### 서버 종료

실행 중인 명령창에서 `Ctrl+C`를 누르거나 명령창을 닫는다.

---

## 태블릿·스마트폰 접속

### 같은 사무실 또는 현장 Wi-Fi에서 접속

다음 조건을 모두 충족하면 접속할 수 있다.

- PC와 모바일 기기가 동일한 Wi-Fi 또는 사내 LAN에 연결되어 있어야 한다.
- PC가 켜져 있고 `start_web.bat` 서버가 실행 중이어야 한다.
- Windows 방화벽에서 Python의 `개인 네트워크` 통신이 허용되어야 한다.
- 모바일 브라우저 주소창에 실행창의 `http://PC-IP:5000` 주소를 입력해야 한다.

예시:

```text
http://192.168.0.103:5000
```

PC의 IP 주소가 변경되면 실행창에 새로 표시되는 주소를 사용한다.

### 접속되지 않을 때 확인 순서

1. PC에서 `http://localhost:5000` 접속 여부 확인
2. PC와 모바일 기기의 Wi-Fi 이름이 같은지 확인
3. 모바일 데이터(5G/LTE)를 잠시 끄고 Wi-Fi로 재접속
4. Windows 방화벽에서 Python의 개인 네트워크 허용 여부 확인
5. 공유기의 `AP isolation`, `게스트 Wi-Fi`, 단말 간 통신 차단 설정 확인

### 외부에서 접속

PC와 다른 네트워크에서 접속하려면 별도 구성이 필요하다.

| 방식 | PC 전원 | 특징 | 권장 용도 |
|---|---:|---|---|
| 동일 Wi-Fi 직접 접속 | 켜짐 | 추가 서비스 불필요 | 사내·현장 사용 |
| VPN/Tailscale 계열 사설 접속 | 켜짐 | 외부 공개 없이 접속 가능 | 담당자 제한 사용 |
| Render 등 웹 서버 배포 | 꺼져도 가능 | 인터넷 어디서나 접속 가능 | 상시 서비스 |

현재 저장소에는 Render 배포 설정이 포함되어 있으나, 공개 배포 시 로그인 기능이 없으므로 저장된 매뉴얼 PDF가 인터넷에 노출될 수 있다. 비공개 자료가 포함된 경우 인증 기능을 추가한 뒤 배포해야 한다.

---

## 수동 설치 및 실행

`start_web.bat`를 사용하지 않는 경우에만 아래 절차를 사용한다.

### 1. Python 환경 (3.9 이상)

```bash
python --version
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 웹 대시보드 실행

```bash
cd src
python web_app.py
```

접속 주소:

```text
http://localhost:5000
```

### 3. CLI 검색

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

### 웹 대시보드에서 PDF 원문 확인

검색 결과 카드의 `PDF 원문 보기 · N쪽` 버튼을 누르면 다음 내용을 한 화면에서 확인할 수 있다.

- 검색 카드: 해당 PDF 페이지의 실제 축소 이미지, PDF 페이지 번호, 관련 내용 발췌
- 왼쪽: 검색 결과가 나온 페이지로 이동한 실제 PDF 원본
- 오른쪽: 해당 페이지의 전체 추출 텍스트와 검색어 강조
- 상단: PDF를 새 창에서 여는 버튼

PDF 글꼴 인코딩 문제로 추출문에 `(cid:...)`가 표시되는 경우에는 왼쪽 PDF 원본 화면을 기준으로 확인한다.

예시: `S300 자동튜닝` 검색 시 `S300 User Manual` PDF 92~93쪽의 자동 튜닝 본문이 우선 표시된다.

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

2. 실행 중인 웹 서버를 종료한 뒤 `start_web.bat`를 다시 실행하면 새 파일이 검색 대상에 반영된다.

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
