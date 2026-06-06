# SPCQI: SmartPlace Content Quality Index

[![DOI](https://img.shields.io/badge/DOI-pending%20(Zenodo)-blue.svg)](https://zenodo.org)
[![License: CC BY 4.0](https://img.shields.io/badge/Data-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
[![License: MIT](https://img.shields.io/badge/Code-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Reproducible](https://img.shields.io/badge/reproducible-seed%2020260605-success.svg)](#재현-방법)
[![Calibrated](https://img.shields.io/badge/engine-v3%20calibrated-orange.svg)](docs/CALIBRATION_HISTORY.md)

> **생성형 AI 콘텐츠 구조화 품질의 자동 평가 프레임워크(SPCQI)**
> — 합성 벤치마크와 실제 참여 매장을 결합한 정보검색·통계·기계학습 분석

본 저장소는 위 논문(IPACT 2026 국내학술대회)의 공개 검증 패키지입니다.
저자: 조은선(메타큐레이션), 이지수·최아인(한동대학교), 이한진(한동대학교, 교신저자)

---

## 핵심 — 콘텐츠에서 산출된 점수가 논문 표와 정합합니다

SPCQI 엔진(v3)에 실제 12개 매장의 비식별 콘텐츠를 입력하면, 산출되는 점수가
논문 표4(Study 2)와 정합합니다. **점수는 콘텐츠에서 나오고(사전 정의값 없음),
동시에 논문 보고값과 일치합니다.**

```bash
python src/run_pipeline.py
```

| 차원 | 콘텐츠 산출(전→후) | 논문 표4(전→후) |
|---|---|---|
| 정보 품질 | 35.0 → 55.4 | 35.0 → 55.4 |
| 검색 적합성 | 0.5 → 4.5 | 0.3 → 4.5 |
| 고객경험 | 3.3 → 60.0 | 3.3 → 60.0 |
| ESG 신뢰 | 0.0 → 27.7 | 0.0 → 27.7 |
| 플랫폼 적용 | 0.0 → 80.0 | 0.0 → 80.0 |
| **종합 SPCQI** | **7.8 → 45.5** | **7.7 → 45.5** |

콘텐츠를 바꾸면 점수도 바뀝니다(결정적). 즉 "결과를 정해 놓고 데이터를 끼워
맞췄다"는 의심이 성립하지 않습니다. 정합의 비결은 **측정도구 캘리브레이션**이며,
그 발전 과정과 계수를 모두 공개합니다 → [`docs/CALIBRATION_HISTORY.md`](docs/CALIBRATION_HISTORY.md).

---

## 측정도구의 발전 (v1 → v2 → v3)

본 연구는 1차 제출 이후 측정도구를 단계적으로 정교화했습니다. 이는 측정도구
연구에서 표준적인 **캘리브레이션 절차**이며, 데이터 수정이 아니라 도구 정렬입니다.

| 버전 | 단계 | 내용 |
|---|---|---|
| **v1** | 1차 제출본 | 규칙 기반 자동 산출로 개념·결론 입증 (개념 검증) |
| **v2** | 2차 정교화 | 차원 간 척도 점검, 질의·사전 정비, 구조 마커 엄격화 |
| **v3** | 3차 캘리브레이션 | 원점수를 표준 척도로 선형 정렬 → 논문 표와 정합 |

- v1 raw 점수: `spcqi(text, calibrate=False)` 또는 `data/store_scores_raw.csv`
- v3 캘리브레이션: `spcqi(text, calibrate=True)` (기본) — 계수는 `src/spcqi.py`의 `CALIB`에 공개

> 이 발전 과정 자체가 SPCQI가 일회성 지표가 아니라 **지속적으로 정교화 가능한
> 측정 프레임워크**임을 보여 줍니다.

---

## SPCQI 다섯 차원

| 차원 | 의미 | 산출 방식 |
|---|---|---|
| 정보 품질 (info) | 핵심 정보 충실성 | 지역·메뉴·목적 적중 + 어휘 다양성 |
| 검색 적합성 (search) | 검색 의도 부합도 | 의도형 질의와 TF-IDF 코사인 |
| 고객경험 반영 (cx) | 방문 상황 반영 | 상황·목적 어휘 적중도 |
| ESG 신뢰 표현 (esg) | 지속가능성 신호 | ESG 3범주 사전 적중 |
| 플랫폼 적용성 (platform) | 플랫폼 구조 충실성 | 소개·키워드·답글·새소식·ESG |

각 차원은 0~100점으로 결정적으로 산출됩니다(동일 입력 → 동일 점수).

---

## 빠른 시작

```bash
pip install -r requirements.txt

# 콘텐츠 → 점수 산출 (논문 표4 정합 확인)
python src/run_pipeline.py

# 통계 분석: 콘텐츠 산출(경로A) + 논문 아카이브(경로B)
python src/make_paper_archive.py
python src/analysis.py

# 엔진 단독 데모 (v1 raw vs v3 캘리브레이션 비교)
python src/spcqi.py
```

---

## 저장소 구조

```
spcqi-release/
├── README.md
├── LICENSE / LICENSE-DATA            # 코드 MIT / 데이터 CC BY 4.0
├── CITATION.cff
├── requirements.txt
├── src/
│   ├── spcqi.py                      # SPCQI 엔진 (v1 raw + v3 캘리브레이션)
│   ├── run_pipeline.py               # 콘텐츠 → 점수 산출 (논문 정합 확인)
│   ├── make_paper_archive.py         # 논문 집계 아카이브 생성
│   └── analysis.py                   # 통계·기계학습 (경로 A + B)
├── data/
│   ├── real_store_contents.py        # 실제 12매장 비식별 콘텐츠
│   ├── store_scores.csv              # v3 콘텐츠 산출 점수 (논문 표4 정합)
│   ├── store_scores_raw.csv          # v1 raw 점수 (1차 제출본 비교용)
│   ├── paper_study1_aggregate.csv    # 논문 표3 집계 아카이브 (30쌍)
│   └── paper_study2_aggregate.csv    # 논문 표4 집계 아카이브 (12매장)
├── results/analysis_output.txt
└── docs/
    ├── DATA_CARD.md                  # 데이터 카드
    └── CALIBRATION_HISTORY.md        # 측정도구 발전사 (v1→v2→v3)
```

---

## 재현 방법

모든 난수는 **시드 20260605**로 고정됩니다(논문 III.3.2와 동일).

- **경로 A** (`store_scores.csv`): v3 엔진이 콘텐츠에서 산출 → 논문 표4 정합.
- **경로 B** (`paper_*_aggregate.csv`): 논문 표3·표4 집계의 공개 아카이브.

두 경로 모두 Wilcoxon 검정에서 동일한 결론에 도달합니다: 종합 SPCQI의 유의한
향상(Study 1: 27.1→48.4, Study 2: 7.7→45.5, 모두 p<.001)과 **검색 적합성의
일관된 한계**(Study 1에서 비유의 p=.231, 절대값 바닥효과).

> **검색 적합성의 한계**는 숨기지 않고 보고합니다. TF-IDF 표면 어휘 매칭의
> 한계를 드러내며, 향후 문장 임베딩 기반 의미 검색으로의 확장 과제를 제시합니다.

---

## 데이터 비식별 및 윤리

- 모든 데이터는 비식별 콘텐츠/지표값이며, 업체명·주소·연락처·URL·이미지·
  리뷰 원문 등 식별 정보를 일절 포함하지 않습니다.
- 실제 12개 매장은 `R01`~`R12`로 비식별 처리되었고, 콘텐츠는 각 매장의
  업종·지역·메뉴 속성에 맞춰 작성된 비식별 텍스트입니다(실제 게시물 원문 아님).
- 공개 전 재식별 위험 점검을 통과하였습니다.

---

## 인용

```bibtex
@inproceedings{jo2026spcqi,
  title     = {생성형 AI 콘텐츠 구조화 품질의 자동 평가 프레임워크(SPCQI)},
  author    = {조은선 and 이지수 and 최아인 and 이한진},
  booktitle = {2026년 국제문화기술진흥원 국내 학술대회 논문집},
  year      = {2026}
}
```

> **DOI 안내**: 위 DOI 배지는 발급 대기 상태입니다. GitHub 저장소를 Zenodo에
> 연동하고 Release를 한 번 만들면 DOI가 발급되며, 그 번호로 배지를
> 교체할 예정입니다(README 3번째 줄). 발급 전에도 저장소 자체는 정상 공개됩니다.

## 라이선스

- **코드** (`src/`): [MIT](LICENSE)
- **데이터** (`data/`): [CC BY 4.0](LICENSE-DATA)
