from __future__ import annotations

import copy
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path


WORKSPACE = Path(__file__).resolve().parents[1]
SOURCE_MARKER = "v3.1"
OUTPUT_NAME = "(벽진바이오텍)_FEMS플러스_사업계획서_GS시스템_중복정리본.hwpx"
SUMMARY_NAME = "벽진바이오텍_GS시스템_중복정리_수정요약.txt"

NS = {
    "ha": "http://www.hancom.co.kr/hwpml/2011/app",
    "hp": "http://www.hancom.co.kr/hwpml/2011/paragraph",
    "hp10": "http://www.hancom.co.kr/hwpml/2016/paragraph",
    "hs": "http://www.hancom.co.kr/hwpml/2011/section",
    "hc": "http://www.hancom.co.kr/hwpml/2011/core",
    "hh": "http://www.hancom.co.kr/hwpml/2011/head",
    "hhs": "http://www.hancom.co.kr/hwpml/2011/history",
    "hm": "http://www.hancom.co.kr/hwpml/2011/master-page",
}

for prefix, uri in NS.items():
    ET.register_namespace(prefix, uri)

HP = f"{{{NS['hp']}}}"
HH = f"{{{NS['hh']}}}"


REPLACEMENTS: dict[int, str] = {
    197: "❍ 본 컨소시엄은 기관별 역할을 분리하여 운영함. 벽진BIO텍은 현장자료 제공 및 FEMS+ 자체운영을 담당하고, GS시스템은 계측 인프라 구축·데이터 수집·연계·시운전·유지보수를 수행하며, KOTITI시험연구원은 LCA·제품단위 탄소배출량 산정·검증 대응을 수행함.",
    227: "ㆍ전력·LNG·스팀·용수 계측 포인트 선정 및 계측기 설치 수행",
    228: "ㆍ설비별·공정별 에너지 사용량 구분을 위한 배선·결선 및 현장 계측환경 구축",
    229: "ㆍ계측기 사양, 설치 위치, 유지보수 접근성 검토 수행",
    232: "ㆍPLC·HMI·Edge Gateway와 데이터 수집장치 연계 구축",
    233: "ㆍRS-485, Modbus RTU/TCP, Ethernet 기반 통신 설정 수행",
    234: "ㆍFEMS+ 및 MRV 연계용 데이터 항목·단위·수집주기·태그 체계 정리",
    235: "ㆍ수집률·연계율·이상값 점검 항목 운영",
    237: "ㆍ계측값, 통신상태, 데이터 수집상태 시운전 수행",
    238: "ㆍ장애 대응, 계측기·통신장비 점검 및 유지보수 수행",
    239: "ㆍ운영자 대상 계측장비 확인 및 통신장애 대응 교육 제공",
    240: "ㆍ성과활용기간 정기점검 및 유지보수 이력 관리",
    329: "전력·LNG·스팀·용수 계측 및 현장 자동화·계측제어 수행",
    330: "계측 포인트 선정, 계측기 사양 검토, 설치·결선·통신 설정 수행",
    331: "PLC·HMI·Gateway 기반 데이터 수집 및 FEMS+·MRV 연계자료 정리",
    332: "시운전, 운영자 교육, 장애 대응, 정기점검 및 유지보수 수행",
    333: "수집률·연계율·이상값 점검자료 제공",
    453: "- 설비별·공정별 에너지 사용량 계측을 위한 전력·LNG·스팀·용수 계측 인프라 구축 수행",
    454: "- 에너지원별 계측기 선정, 설치 위치 검토, 배선·결선 수행",
    475: "- 텐터기, 보일러, 스팀 배관, 유틸리티 설비 중심 계측 포인트 선정 수행",
    476: "- 고온·고압, 습도, 진동, 설치공간 등 현장 조건을 반영한 계측기 사양 검토",
    479: "- 기존 생산설비 운전 영향을 줄이는 설치·시공 계획 수립",
    480: "- 레거시 계측기와 신규 계측기의 통신·신호 변환 연계 수행",
    485: "- PLC·HMI·계측기·통신장비 기반 자동제어 및 데이터 수집체계 구축 수행",
    487: "- 생산설비, 열원설비, 유틸리티 설비의 운전상태와 계측데이터 수집 수행",
    489: "- PLC·HMI·Edge Gateway·데이터 수집 서버 간 연계 구축",
    510: "- RS-485, Modbus RTU/TCP, Ethernet 기반 현장 통신 구성",
    513: "- Raw Data / Processed Data 분리 저장을 위한 DB 구조 설계",
    514: "- 수집률·연계율·이상값·통신상태 점검 구조 구축",
    518: "- FEMS+ 대시보드에서 설비별·공정별·에너지원별 사용량 모니터링 구조 구축",
    519: "- 시간대별·일별·월별 에너지 사용량 분석 화면 구성",
    520: "- 전력·LNG·스팀·용수 사용량의 기준기간 대비 비교 구조 구축",
    522: "- 에너지 베이스라인 및 EnPI 산출용 기초 데이터 관리",
    523: "- 생산량, 운전시간, LOT 정보와 에너지 사용량 연계 구조 구축",
    526: "- 제품 단위 탄소배출량 산정에 필요한 시간 매칭 데이터 제공",
    530: "- FEMS+ 및 산업단지 MRV 플랫폼 연계를 고려한 현장 데이터 구조 설계",
    531: "- MES, ERP, FEMS+, MRV 연계에 필요한 데이터 항목 정리",
    532: "- 데이터 항목·단위·수집주기·태그 체계·설비코드 표준화 관리",
    533: "- REST API 기반 외부 연계 구조 구성",
    534: "- MRV 플랫폼 연계용 데이터 매핑표 및 정상 수집 데이터 샘플 제공",
    535: "- 현장 데이터 수집·저장·전송 산출물 관리",
    556: "- 섬유 염색·가공 공정의 에너지 사용특성과 설비 운전구조 반영",
    557: "- 텐터기, 보일러, 스팀 계통, 염색기, 정련기, 건조설비 계측 포인트 선정",
    558: "- Batch 생산구조와 작업조건별 에너지 변동을 반영한 데이터 구조 설계",
    559: "- 생산설비, 열원설비, 유틸리티 설비별 에너지 사용량 수집",
    560: "- 공정별·설비별 에너지 사용량 분석용 데이터 구조 구성",
    561: "- 스팀·용수·LNG·전력 사용량과 운전조건의 상관 분석 기반 구축",
    566: "- 현장 계측망, 제어망, 외부 연계망 분리 구성",
    567: "- 계측 데이터 수집장치, PLC, HMI, Edge Gateway, 서버 통신상태 점검",
    568: "- 통신장애, 계측값 이상, 데이터 누락, 센서 오류 현장 대응",
    569: "- 계측기 설치 후 정상작동, 통신상태, 데이터 수집상태 시운전 수행",
    570: "- 운영자 대상 계측장비 운전, 데이터 확인, 이상 발생 대응 교육 수행",
    571: "- 사업기간 및 성과활용기간 장애 대응, 정기점검 및 유지보수 수행",
    582: "전력·LNG·스팀·용수 계측기 선정, 설치, 배선·결선 수행",
    588: "PLC·HMI·Edge Gateway 기반 설비 운전상태 및 계측데이터 수집",
    591: "RS-485, Modbus RTU/TCP, Ethernet 기반 현장 통신 구성",
    594: "Edge Gateway 및 수집서버 기반 실시간 데이터 수집",
    597: "Raw Data / Processed Data 분리 저장 및 이력관리",
    600: "FEMS+ 대시보드 기반 설비별·공정별 사용량 모니터링",
    606: "MRV 연계용 데이터 항목·단위·수집주기·태그 체계 정리",
    615: "시운전, 운영자 교육, 장애 대응, 정기점검 및 유지보수",
    1597: "- GS시스템은 현장 계측 및 데이터 수집 기반 구축을 수행함.",
    1598: "- 세부 장비·통신 구성은 참여기관 수행내용과 계측 인프라 절에서 관리함.",
    1609: "- 데이터 수집률·연계율·이상값 점검 체계를 구축함.",
    1634: "- 에너지원별 세부 계측기 목록은 계측 인프라 구축 절에서 관리함.",
    1644: "- 현장 계측 데이터는 PLC·HMI·Edge Gateway·데이터 수집장치를 통해 수집함.",
    1645: "- 현장 조건에 따라 RS-485, Modbus RTU/TCP, Ethernet 통신을 적용함.",
    1647: "- 통신주소, 단위, 스케일링 값, 수집주기, 태그명을 정리함.",
    1656: "- Raw Data / Processed Data 분리 저장 구조를 구성함.",
    1659: "- 수집률·연계율·이상값 점검을 위해 계측기, PLC, Gateway, 서버 구간별 점검체계를 구성함.",
    1662: "- FEMS+ 대시보드 활용을 위한 데이터 항목·단위·태그·수집주기·설비구분 정보를 정리함.",
    1664: "- 에너지 사용량 조회, 베이스라인 설정, EnPI 산출이 가능한 데이터 기반을 구성함.",
    1665: "- 생산 LOT 정보와 에너지 사용량의 시간 매칭 구조를 구성함.",
    1682: "- 수집데이터를 LCA 분석, 제품 단위 탄소배출량 산정, 산업단지 MRV 플랫폼 연계 기초자료로 제공함.",
    1685: "- 산업단지 MRV 플랫폼 연계를 고려하여 현장 계측 데이터 표준화 기반을 구축함.",
    1686: "- 계측기별 데이터 항목, 단위, 수집주기, 태그명, 설비코드, 통신방식을 정리함.",
    1687: "- FEMS+에서 MRV 플랫폼으로 전송 가능한 데이터 구조를 지원함.",
    1700: "- 데이터 매핑, 수집현황 확인, 정상 수집 데이터 샘플을 제공함.",
    1701: "- 단위 불일치, 태그 중복, 수집주기 불일치 방지를 위한 표준화 자료를 정리함.",
    1815: "- 전력·LNG·스팀·용수 사용량 실시간 수집체계 구축",
    1816: "- 설비별·공정별 에너지 사용량 구분 관리",
    1817: "- FEMS+ 대시보드 기반 에너지 사용량, 설비 운전상태, 영향인자 통합 관리",
    1819: "- EnPI 산출용 기초 데이터 확보",
    1820: "- 제품 단위 탄소배출량 산정에 필요한 계측 데이터 제공",
    1821: "- 산업단지 MRV 플랫폼 연계용 데이터 구조 마련",
    1822: "- 수집률·연계율·이상값 점검 기반 성과지표 관리",
    1823: "- 정기점검 및 유지보수 체계 기반 성과활용기간 데이터 제공",
    1873: "- 수행 분야 : 계측 인프라 구축, PLC·HMI·Edge Gateway 연계, 데이터 수집장치·DB 구성, FEMS+·MRV 연계자료 정리, 시운전·유지보수",
    1877: "- 설비별·공정별 에너지 사용량 계측이 가능한 현장 계측 인프라 구축",
    1878: "- 전력·LNG·스팀·용수 사용량 실시간 수집체계 구축",
    1879: "- PLC·HMI·Edge Gateway와 데이터 수집장치 연계 구축",
    1880: "- 수집률·연계율·이상값 점검 항목 기반 품질관리 수행",
    1881: "- EnPI 및 제품 단위 탄소배출량 산정에 필요한 데이터 구조 정리",
    1882: "- 시운전, 운영자 교육, 장애 대응, 정기점검 및 유지보수 운영",
    1885: "- 현장조사 및 계측 포인트 선정",
    1886: "⦁ 생산설비, 열원설비, 유틸리티 설비 현황 및 에너지원 흐름 조사함",
    1887: "⦁ 설비별·공정별 계측 포인트, 설치공간, 배선경로, 유지보수 접근성 검토함",
    1888: "⦁ 전력·LNG·스팀·용수 계측기 사양 및 계측 항목 확정함",
    1892: "- 계측기 설치 및 통신 연계",
    1893: "⦁ 계측기 설치, 배선·결선, 통신주소·배율·단위 설정 수행함",
    1894: "⦁ PLC·HMI·Edge Gateway와 데이터 수집장치 연계 구축함",
    1895: "⦁ RS-485, Modbus RTU/TCP, Ethernet 기반 현장 통신 구성함",
    1899: "- 데이터 수집장치 및 DB 구성",
    1900: "⦁ 현장 계측 데이터를 Edge Gateway 또는 수집장치로 취득함",
    1901: "⦁ Raw Data / Processed Data 분리 저장 및 이력관리 구조 구축함",
    1904: "⦁ LOT ID, 설비 ID, Timestamp 기준 데이터 매칭 구조 제공함",
    1905: "⦁ 수집률·연계율·이상값 점검 항목 구성함",
    1906: "- FEMS+·MRV 연계자료 정리",
    1907: "⦁ FEMS+ 대시보드 활용 데이터 항목·단위·수집주기·태그 체계 정리함",
    1908: "⦁ 설비별·공정별 에너지 사용량 및 EnPI 산출용 데이터 구조 구성함",
    1912: "⦁ 제품 단위 탄소배출량 산정 및 산업단지 MRV 플랫폼 연계 매핑자료 제공함",
    1919: "- 시운전·교육·유지보수",
    1920: "⦁ 계측값, 통신상태, 데이터 수집상태 시운전 수행함",
    1924: "⦁ 운영자 대상 계측기 확인, 통신장애 대응, 데이터 확인 교육 제공함",
    1925: "⦁ 장애 대응, 정기점검 및 유지보수 이력 관리함",
    1926: "⦁ 성과활용기간 데이터 제공을 위한 반기 점검체계 운영함",
    1936: "전력·LNG·스팀·용수 사용 흐름 및 기존 계측기 현황 조사",
    1945: "계측기 사양, 통신방식, 수집항목 확정",
    1946: "데이터 항목·단위·수집주기·태그 체계 정리",
    1955: "계측기와 PLC·HMI·Edge Gateway 간 통신 구성",
    1956: "통신주소, 배율, 단위, 태그 설정",
    1965: "FEMS+ 대시보드 활용 데이터 구조 정리",
    1966: "단위, 수집주기, 설비코드, 데이터 매핑 정리",
    1975: "MRV 연계용 데이터 항목 및 매핑자료 정리",
    1976: "계측기 목록, 정상 수집 데이터 샘플 제공",
    1985: "정기점검 및 장애 대응",
    1986: "계측기, PLC, Gateway, 통신장비 점검",
    2010: "- 현장 계측 인프라 구축으로 실시간 에너지 데이터 확보",
    2011: "- 설비별·공정별 데이터 구조 구축으로 에너지 사용량 분석 기반 마련",
    2012: "- PLC·HMI·Edge Gateway 연계로 FEMS+ 데이터 수집 기반 확보",
    2013: "- 데이터 항목·단위·태그·수집주기 표준화로 연계율 관리",
    2014: "- 수집률·연계율·이상값 점검자료 제공",
    2015: "- EnPI 및 제품 단위 탄소배출량 산정용 계측 데이터 제공",
    2016: "- 산업단지 MRV 플랫폼 연계용 현장 데이터 자료 정리",
    2017: "- 정기점검 및 유지보수 체계로 성과활용기간 데이터 제공",
    2101: "- GS시스템은 현장 계측·제어·통신 기반으로 FEMS+ 구축사업의 데이터 수집 기반을 구축함.",
    2173: "❍ 본 사업은 벽진BIO텍, GS시스템 및 KOTITI시험연구원이 전담인력을 지정하여 단계별로 수행함. 벽진BIO텍은 현장 공정정보와 LOT 생산이력을 관리하고, GS시스템은 계측 인프라 구축·데이터 수집·운영 유지보수를 수행하며, KOTITI시험연구원은 LCA 방법론·데이터 품질관리·검증 대응을 수행함.",
    2416: "- GS시스템은 지역 기반 산업자동화·계측제어 기업으로서 현장 기술지원, 장애 대응, 정기점검을 제공함.",
    2463: "- GS시스템은 본 사업에서 계측 인프라 구축, PLC·HMI 연계, 현장 통신 구성, 데이터 수집장치 구축, FEMS+ 연계 데이터 기반 구축을 수행함.",
    2559: "전력·LNG·스팀·용수 사용계통 및 기존 계측기 현황 조사",
    2590: "계측 포인트 선정, 계측기 사양·설치 위치·배선·통신경로 확정",
    2598: "전력·LNG·스팀·용수 계측기 설치 및 배선·결선",
    2621: "PLC·HMI·Edge Gateway 연계 및 현장 계측 데이터 수집 구조 구축",
    2630: "데이터 항목·단위·태그·수집주기·설비코드 정리 및 시운전",
    2661: "MRV 연계용 계측기 목록, 데이터 매핑표, 정상 수집 데이터 샘플 제공",
    2693: "현장 계측망·제어망·외부 연계망 분리 구성 및 통신상태 점검",
    2701: "수집률·연계율·이상값 점검 및 유지보수 체계 수립",
    3373: "❍ 계측값은 PLC·HMI·Edge Gateway 또는 통신게이트웨이를 통해 FEMS+ 서버로 전송함.",
    3374: "❍ 수집 데이터는 설비 ID, 계측기 ID, Timestamp, LOT ID 기준으로 저장함.",
    3409: "❍ 에너지 사용량과 탄소배출량 산정에 필요한 핵심 공정·설비 중심으로 계측 인프라를 구축함.",
    3412: "❍ LOT 정보, 설비 운영정보, 계측데이터를 함께 관리하여 제품별 에너지 사용량과 탄소배출량 산정자료를 구축함.",
    3413: "❍ 구축 후 수집률·연계율·이상값·통신오류를 점검하여 FEMS+ 대시보드, 공정개선, 제품단위 탄소배출량 산정에 활용함.",
    3433: "수집률·연계율·이상값·시간 불일치 점검",
    3434: "제품단위 탄소배출량 산정자료 검토",
    3574: "❍ 설비별 계측데이터는 전력, 스팀, LNG, 용수 사용량을 시간 단위로 수집하고 LOT 생산이력과 매칭함.",
    3752: "❍ GS시스템은 현장 계측 인프라, 통신망, 데이터 수집장치, FEMS+ 연계 시스템 구축을 수행함.",
    3753: "❍ KOTITI의 제품단위 탄소배출량 산정에 필요한 계측데이터와 설비 운영데이터를 제공함.",
    3759: "전력·LNG·스팀·용수 등 주요 에너지원 계측기 설치",
    3761: "PLC·HMI·Edge Gateway 기반 계측데이터 수집",
    3765: "계측데이터를 FEMS+ 대시보드 및 서버로 전송",
    3767: "수집률·연계율·이상값·통신오류 점검",
    3773: "시운전, 운영자 교육, 장애 대응, 정기점검 수행",
    3780: "❍ KOTITI의 제품단위 탄소배출량 산정에 활용 가능하도록 데이터 항목·단위·수집주기·설비 구분체계를 표준화함.",
    3781: "❍ 구축 후 수집률·연계율·이상값 점검체계를 포함하여 운영함.",
    3829: "❍ 탄소배출량 산정은 KOTITI가 수행하고, GS시스템은 산정에 필요한 원천데이터를 제공함.",
    3861: "❍ 계측기별 태그명, 설비명, 단위, 수집주기, 통신주소를 표준화하여 관리함.",
    3893: "❍ 현장 조건에 따라 RS-485, Ethernet, Modbus RTU/TCP 등 적용 가능한 통신방식을 선정함.",
    3935: "❍ FEMS+ 시스템의 핵심 관리대상은 수집률·연계율·이상값 점검 체계임.",
    3936: "❍ 데이터 품질관리는 수집률, 연계율, 이상치 검출, 결측관리 중심으로 수행함.",
    3944: "이상값 점검",
    3945: "이상치·결측치·비정상값 검출 및 조치",
    3986: "❍ GS시스템은 원천데이터의 수집·저장·점검 구조를 관리함.",
    3989: "❍ FEMS+에서 수집한 에너지·온실가스 데이터를 산업단지 MRV 플랫폼과 연계할 수 있도록 데이터 구조를 정리함.",
    4013: "❍ 구축 완료 후 계측기, 통신, 서버, 화면, 데이터 저장, MRV 연계 기능의 정상운전 여부를 확인함.",
    4032: "❍ 정상운전 확인 후 시운전 확인서, 정상운전 확인서, 데이터 수집률·연계율 점검표를 작성함.",
    4056: "❍ 유지보수 대상은 계측기, 통신장치, PLC, Gateway, 서버, FEMS+ 대시보드, DB를 포함함.",
    4075: "❍ 성과활용기간 데이터 제공을 위한 유지보수 및 점검 이력 관리 기반을 마련함.",
    4088: "❍ 현장 계측·제어 기반 시스템 구축역량 보유",
    4089: "❍ 전력·LNG·스팀·용수 계측 인프라 구축 수행",
    4090: "❍ PLC·HMI·Edge Gateway·데이터 수집장치 연계 수행",
    4091: "❍ FEMS+ 대시보드 활용 데이터 구조 설계",
    4092: "❍ 설비 ID, 계측기 ID, Timestamp 기반 데이터 수집구조 적용",
    4093: "❍ 제품 단위 탄소배출량 산정에 필요한 원천데이터 제공",
    4094: "❍ 시운전, 운영자 교육, 정기점검 및 유지보수 수행",
    4095: "❍ 계측기 설치부터 데이터 수집·시각화·MRV 연계자료 제공까지 일괄 수행",
    4124: "❍ GS시스템은 계측기, PLC·HMI·Edge Gateway, FEMS+ 서버를 통해 원천데이터를 수집·저장·전송하고, KOTITI는 MRV 제출용 데이터 세트와 산정보고서 구조를 정리함.",
    4133: "전력·LNG·스팀·용수 계측데이터 수집",
    4148: "MRV 플랫폼 연계용 데이터 항목 변환 및 제출자료 지원",
    4469: "계측기 설치, 통신망 구축, 데이터 수집장치 구성",
    4472: "전력·LNG·스팀·용수 계측데이터 수집",
    4478: "수집률·연계율·이상값 1차 점검",
    4484: "연계 데이터 전송 및 오류 로그 제공",
    5165: "계측기 수신상태, 통신상태, 알람 확인",
    5168: "수집률·연계율·이상값, 백업상태, 서버 저장공간 확인",
    5174: "계측기 상태, 통신장비, 서버, 백업복구 절차 점검",
    5519: "❍ GS시스템은 성과활용기간 안정적 데이터 제공을 위해 계측기·통신망·PLC·Gateway·서버·DB·FEMS+ 대시보드 유지보수를 수행함.",
    5521: "❍ 사업 종료 후 월간 데이터 검토, 반기 유지보수 점검, 연간 성과활용 보고 체계를 유지함.",
    5530: "수집률·연계율·이상값 점검, 통신상태 점검, DB 백업, 오류 복구, 서버 상태 점검",
    5550: "계측기, 통신망, PLC·Gateway, 서버, DB, FEMS+ 대시보드, 백업",
    6992: "❍ 사업 종료 후에도 FEMS+ 시스템이 운영되도록 계측기, 통신망, 서버, DB, 대시보드, MRV 연계 기능 유지보수 체계를 운영함.",
    6993: "❍ 성과활용기간 동안 수요기업은 현장 운영, GS시스템은 유지보수와 데이터 제공, KOTITI는 산정자료 검토와 성과보고 대응을 수행함.",
    7006: "계측기, 통신망, PLC·Gateway, 서버, DB, FEMS+ 대시보드",
    7023: "RS-485, Ethernet, Gateway 통신상태",
    7047: "계측기 수신상태, 통신상태, 알람 확인",
    7050: "에너지 사용량, 원단위, 이상값, 결측치 검토",
    7053: "계측기·통신장비·서버·DB 유지보수 점검",
    7067: "❍ 장애조치 이력은 수집률·연계율·이상값 점검 및 성과활용보고서 작성자료로 활용함.",
    7071: "❍ 계측데이터 수집률·연계율·이상값 점검체계 유지",
    7074: "❍ 산업단지 MRV 플랫폼 연계 데이터 제공체계 유지",
    7246: "❍ GS시스템은 계측기 설치, 통신구성, FEMS+ 데이터 수집, 서버·DB·대시보드 운영, 유지보수 역할을 수행함.",
    7303: "❍ GS시스템의 계측·제어·통신 구축 역량과 KOTITI의 LCA·LCI·탄소배출량 산정 역량을 결합하여, 현장 데이터 수집부터 검증 가능한 산정보고서 작성까지 연계함.",
}

DELETE_INDICES = {
    455, 477, 478, 481, 482,
    486, 488, 490, 511, 512, 515,
    521, 524, 525, 527,
    536, 552, 553, 562, 563, 564, 572,
    1636, 1637, 1638, 1639, 1646, 1648, 1649, 1651, 1652, 1653, 1654, 1655, 1657, 1658,
    1663, 1666, 1668, 1669, 1670, 1671, 1672, 1673, 1674, 1675, 1677, 1678, 1679, 1680, 1681,
    1688, 1690, 1691, 1692, 1693, 1694, 1695, 1696, 1697, 1698, 1699,
    1889, 1890, 1891, 1896, 1897, 1898, 1902, 1903, 1909, 1910, 1911,
    1913, 1914, 1915, 1916, 1917, 1918, 1921, 1922, 1923,
}


def direct_text(p_node: ET.Element) -> str:
    texts: list[str] = []
    for run in p_node.findall(f"./{HP}run"):
        for t in run.findall(f"./{HP}t"):
            texts.append(t.text or "")
            for child in list(t):
                texts.append(child.tail or "")
    return "".join(texts).strip()


def set_t_text(t_node: ET.Element, text: str) -> None:
    for child in list(t_node):
        t_node.remove(child)
    parts = text.split("\n")
    t_node.text = parts[0]
    for part in parts[1:]:
        br = ET.SubElement(t_node, f"{HP}lineBreak")
        br.tail = part


def ensure_blue_charpr(header_root: ET.Element, charpr_id: str, cache: dict[str, str]) -> str:
    if charpr_id in cache:
        return cache[charpr_id]

    char_props = header_root.find(f".//{HH}charProperties")
    if char_props is None:
        raise RuntimeError("header.xml charProperties not found")

    source = None
    max_id = -1
    for char_pr in char_props.findall(f"{HH}charPr"):
        cid = char_pr.attrib.get("id")
        if cid and cid.isdigit():
            max_id = max(max_id, int(cid))
        if cid == charpr_id:
            source = char_pr

    if source is None:
        raise RuntimeError(f"charPr id {charpr_id} not found")

    candidate_key = tuple(sorted((k, "#0000FF" if k == "textColor" else v) for k, v in source.attrib.items() if k != "id"))
    for char_pr in char_props.findall(f"{HH}charPr"):
        existing_key = tuple(sorted((k, v) for k, v in char_pr.attrib.items() if k != "id"))
        if existing_key == candidate_key and char_pr.attrib.get("textColor") == "#0000FF":
            cache[charpr_id] = char_pr.attrib["id"]
            return cache[charpr_id]

    new_pr = copy.deepcopy(source)
    new_id = str(max_id + 1)
    new_pr.attrib["id"] = new_id
    new_pr.attrib["textColor"] = "#0000FF"
    char_props.append(new_pr)
    char_props.attrib["itemCnt"] = str(len(char_props.findall(f"{HH}charPr")))
    cache[charpr_id] = new_id
    return new_id


def replace_paragraph(p_node: ET.Element, text: str, header_root: ET.Element, blue_cache: dict[str, str]) -> None:
    runs = p_node.findall(f"./{HP}run")
    text_runs = [run for run in runs if run.find(f"./{HP}t") is not None]
    if not text_runs:
        return
    first = text_runs[0]
    original_charpr = first.attrib.get("charPrIDRef", "0")
    blue_charpr = ensure_blue_charpr(header_root, original_charpr, blue_cache)
    for run in text_runs:
        run.attrib["charPrIDRef"] = blue_charpr
        t_node = run.find(f"./{HP}t")
        if t_node is not None:
            set_t_text(t_node, "")
    set_t_text(first.find(f"./{HP}t"), text)


def serialize_xml(root: ET.Element) -> bytes:
    body = ET.tostring(root, encoding="utf-8", short_empty_elements=True)
    return b'<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>' + body


def main() -> None:
    source = next(path for path in WORKSPACE.glob("*.hwpx") if SOURCE_MARKER in path.name)
    output = WORKSPACE / OUTPUT_NAME

    with zipfile.ZipFile(source, "r") as zin:
        header_root = ET.fromstring(zin.read("Contents/header.xml"))
        section_root = ET.fromstring(zin.read("Contents/section0.xml"))
        infos = zin.infolist()
        payloads = {info.filename: zin.read(info.filename) for info in infos}

    p_nodes = section_root.findall(f".//{HP}p")
    parent = {child: node for node in section_root.iter() for child in list(node)}
    blue_cache: dict[str, str] = {}

    changed = 0
    missing: list[int] = []
    for idx, new_text in REPLACEMENTS.items():
        if idx >= len(p_nodes):
            missing.append(idx)
            continue
        if not direct_text(p_nodes[idx]):
            missing.append(idx)
            continue
        replace_paragraph(p_nodes[idx], new_text, header_root, blue_cache)
        changed += 1

    blanked = 0
    for idx in sorted(DELETE_INDICES, reverse=True):
        if idx >= len(p_nodes):
            missing.append(idx)
            continue
        node = p_nodes[idx]
        if not direct_text(node):
            continue
        replace_paragraph(node, "", header_root, blue_cache)
        blanked += 1

    payloads["Contents/header.xml"] = serialize_xml(header_root)
    payloads["Contents/section0.xml"] = serialize_xml(section_root)

    with zipfile.ZipFile(output, "w") as zout:
        for info in infos:
            data = payloads[info.filename]
            new_info = zipfile.ZipInfo(info.filename, date_time=info.date_time)
            new_info.comment = info.comment
            new_info.extra = info.extra
            new_info.internal_attr = info.internal_attr
            new_info.external_attr = info.external_attr
            new_info.create_system = info.create_system
            new_info.compress_type = info.compress_type
            zout.writestr(new_info, data)

    summary = f"""수정본: {output.name}
원본: {source.name}

수정 결과
- 파란색 표시 적용 문단/셀: {changed}개
- 중복 축약을 위해 빈 문단으로 처리한 본문 문단: {blanked}개
- 추가 생성한 파란색 글자속성: {len(blue_cache)}종
- 누락 또는 확인 필요 인덱스: {', '.join(map(str, missing)) if missing else '없음'}

수정한 목차 목록
- 제1장 제1절 추진체계 및 역할분담: 기관별 역할 분담 중 GS시스템 부분
- 제1장 제2절 컨소시엄 세부 역량: GS시스템 일반현황, 기술역량, 종합표 일부
- 제2장 제1절 세부사업 기획 및 설계: 추진전략, 참여기관 1 목표 및 내용, 주요 산출물/성과 기여내용
- 제2장 제2절 추진일정: GS시스템 추진내용 셀
- 제2장 제3절 세부 추진계획 및 방법: 계측 인프라, FEMS+ 구축·운영, MRV 연계, 보안, 데이터 품질관리, 유지보수 관련 GS시스템 문구
- 제6장 기대효과: 성과활용기간 유지보수 방안 중 GS시스템 반복 문구

중복 제거한 주요 표현
- 전력, LNG, 스팀, 용수 계측 반복 나열
- 계측기 설치, 배선·결선, 통신 설정 반복 설명
- PLC, HMI, Edge Gateway, 데이터 수집장치 연계 반복 설명
- RS-485, Modbus RTU/TCP, Ethernet 및 외부 연계 프로토콜 반복 나열
- FEMS+ 및 산업단지 MRV 플랫폼 연계 반복 문장
- 데이터 항목·단위·수집주기·태그 체계 반복 문장
- 시운전, 운영자 교육, 장애 대응, 정기점검, 유지보수 반복 문장

압축·재배치한 항목
- GS시스템 역할은 계측 인프라 구축, 데이터 수집·연계, 시운전·유지보수 중심으로 축약
- 기술역량은 계측 인프라, PLC·HMI·통신, DB 구성, FEMS+·MRV 연계, 섬유공정 특화, 보안·유지보수 항목으로 압축
- 실제 수행업무는 제2장 제1절 참여기관 1 목표 및 내용에 집중 배치
- 성과활용 부분은 구축단계 설명 대신 안정적 데이터 제공과 유지보수 체계 중심으로 정리

유지한 핵심 기술 키워드
- 전력, LNG, 스팀, 용수 계측
- 설비별·공정별 에너지 사용량
- 계측 포인트 선정
- PLC·HMI·Edge Gateway 연계
- RS-485, Modbus RTU/TCP, Ethernet
- Raw Data / Processed Data
- FEMS+ 대시보드
- 산업단지 MRV 플랫폼 연계
- 데이터 항목·단위·수집주기·태그 체계
- EnPI
- 제품 단위 탄소배출량 산정
- 시운전
- 운영자 교육
- 정기점검 및 유지보수

추가 검토가 필요한 부분
- 벽진 작성 요청, 벽진 확인 필요, 작성 예정 표시는 GS시스템 영역 외 문구이므로 유지
- 일부 표의 세부 수량·금액·참여율은 원자료 확인 필요
"""
    (WORKSPACE / SUMMARY_NAME).write_text(summary, encoding="utf-8")
    print(summary)


if __name__ == "__main__":
    main()
