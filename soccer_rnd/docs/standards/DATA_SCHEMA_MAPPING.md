# 데이터 스키마 매핑 및 전처리 가이드

> 작성: dataset-scout@soccer-rnd | 최종 갱신: 2026-02-10

## 1. 프로젝트 표준 스키마 정의

### 1.1 트랙 A 표준 스키마

| 표준 컬럼명 | 자료형 | 단위 | 설명 | 필수 여부 |
|---|---|---|---|---|
| `subject_id` | string | - | 피험자 익명 식별자 | 필수 |
| `session_id` | string | - | 세션 식별자 (예: pre/post, session_01) | 필수 |
| `timestamp` | float | seconds | 기록 시작부터 경과 시간 | 필수 |
| `rr_interval_ms` | float | milliseconds | beat-to-beat RR 간격 | 필수 |
| `power_watts` | float | watts (W) | 운동 부하 (자전거 에르고미터 등) | 필수 |
| `vo2_ml_min_kg` | float | mL/min/kg | 산소 소비량 (체중 보정) | 권장 |
| `heart_rate_bpm` | float | bpm | 순간 심박수 | 권장 |
| `stage_label` | string | - | 운동 부하 단계 (rest, warm-up, stage1, ..., recovery) | 권장 |
| `phase` | string | - | 훈련 기간 구분 (pre_training / post_training) | 권장 |

### 1.2 트랙 B 표준 스키마

| 표준 컬럼명 | 자료형 | 단위 | 설명 | 필수 여부 |
|---|---|---|---|---|
| `athlete_id` | string | - | 선수 익명 식별자 | 필수 |
| `date` | date | YYYY-MM-DD | 기록 날짜 | 필수 |
| `rpe` | integer | 1-10 (CR-10) | 자각 운동 강도 | 필수 |
| `duration_min` | float | minutes | 훈련/경기 시간 | 필수 |
| `srpe` | float | AU (arbitrary units) | sRPE = RPE x duration_min | 산출 |
| `fatigue` | integer | 1-7 | Hooper 피로도 | 필수 |
| `stress` | integer | 1-7 | Hooper 스트레스 | 필수 |
| `doms` | integer | 1-7 | Hooper 근육통 (DOMS) | 필수 |
| `sleep` | integer | 1-7 | Hooper 수면 질 | 필수 |
| `hooper_index` | float | AU | Hooper Index = fatigue + stress + doms + sleep | 산출 |
| `session_type` | string | - | 세션 유형 (training / match / rest) | 권장 |
| `match_day` | boolean | - | 경기일 여부 | 권장 |

---

## 2. 데이터셋별 컬럼 매핑

### 2.1 트랙 A: PhysioNet ACTES --> 프로젝트 표준 스키마

| 프로젝트 표준 컬럼 | ACTES 원본 컬럼 (추정) | 변환 방법 | 비고 |
|---|---|---|---|
| `subject_id` | `subject` / 파일명에서 추출 | 문자열 정규화 (예: `S01`, `S02`, ...) | PhysioNet 파일별 피험자 구분 |
| `session_id` | 파일명 또는 메타데이터에서 추출 | `pre` / `post` + 세션 번호 | 훈련 전후 2회 측정 |
| `timestamp` | `time` / `elapsed_time` | 초(seconds) 단위로 통일 | 원본 시간 단위 확인 필요 |
| `rr_interval_ms` | `RR` / `rr_interval` | ms 단위 확인, 필요 시 x1000 변환 | 일부 데이터셋은 초 단위로 제공 |
| `power_watts` | `power` / `Power` / `load_watts` | 직접 매핑 (단위 W 확인) | 점증 부하 단계별 값 |
| `vo2_ml_min_kg` | `VO2` / `vo2` | mL/min/kg 단위 확인 | 절대값(mL/min)인 경우 체중 보정 필요 |
| `heart_rate_bpm` | `HR` / `heart_rate` | 직접 매핑 | 또는 60000/RR(ms)로 산출 가능 |
| `stage_label` | `stage` / `protocol_step` | 문자열 정규화 | 원본 프로토콜 문서 참조 |
| `phase` | 파일명/메타데이터에서 추출 | `pre_training` / `post_training` | 디렉토리 구조로 구분될 수 있음 |

**주의사항:**
- ACTES 데이터의 정확한 컬럼명은 다운로드 후 확인 필요 (위 매핑은 PhysioNet CPET 데이터셋의 일반적 관례 기반 추정)
- WFDB 형식인 경우 `wfdb` Python 패키지로 읽기: `wfdb.rdrecord()`, `wfdb.rdann()`
- CSV 형식인 경우 `pandas.read_csv()`로 직접 읽기

### 2.2 트랙 A: Autonomic Aging (보조) --> 프로젝트 표준 스키마

| 프로젝트 표준 컬럼 | Autonomic Aging 원본 컬럼 | 변환 방법 | 비고 |
|---|---|---|---|
| `subject_id` | `subject_id` / 파일명 | 직접 매핑 | 약 1,100명 |
| `session_id` | 단일 세션 | `session_01` 고정 | tilt test 단일 측정 |
| `timestamp` | `time` | 초 단위 통일 | - |
| `rr_interval_ms` | `RR` / `nn_interval` | ms 단위 확인 | - |
| `power_watts` | **없음** | - | 운동 부하 데이터 미포함 |
| `stage_label` | `position` (supine/tilt) | 매핑 정의 필요 | 운동 단계가 아닌 자세 변화 |

### 2.3 트랙 B: Carey et al. (1순위) --> 프로젝트 표준 스키마

| 프로젝트 표준 컬럼 | Carey 원본 컬럼 (추정) | 변환 방법 | 비고 |
|---|---|---|---|
| `athlete_id` | `PlayerID` / `player_id` | 문자열 정규화 (예: `P01`, `P02`, ...) | 익명화된 ID |
| `date` | `Date` / `date` | `pd.to_datetime()` 변환, YYYY-MM-DD 통일 | 원본 날짜 형식 확인 |
| `rpe` | `RPE` | 직접 매핑 (1-10 범위 확인) | CR-10 스케일 확인 |
| `duration_min` | `Duration` / `duration` | 분(minutes) 단위 확인 | 초 단위인 경우 /60 변환 |
| `srpe` | `sRPE` 또는 산출 | 직접 매핑 또는 RPE x duration_min | 원본에 sRPE가 있으면 직접 사용 |
| `fatigue` | `Fatigue` / `fatigue` | 직접 매핑 (1-7 범위 확인) | 스케일 범위 확인 필수 |
| `stress` | `Stress` / `stress` | 직접 매핑 | - |
| `doms` | `Muscle_Soreness` / `soreness` | **매핑 필요**: 원본 "muscle soreness" -> 표준 "doms" | 항목명 변환 기록 |
| `sleep` | `Sleep_Quality` / `sleep` | **매핑 필요**: 원본 "sleep quality" -> 표준 "sleep" | 스케일 방향 확인 (높을수록 좋은지/나쁜지) |
| `hooper_index` | 산출 | fatigue + stress + doms + sleep | "mood" 항목은 제외 (ADR 기록) |
| `session_type` | `Session_Type` / `type` | training/match/rest로 정규화 | 원본 라벨 확인 후 매핑 |

**주의사항:**
- "mood" 항목은 전통적 Hooper Index 4항목(fatigue, stress, DOMS, sleep)에 포함되지 않으므로 기본 산출에서 제외하고, 보조 분석에서만 활용 (ADR 기록 필요)
- 수면 질(sleep quality) 스케일의 방향성 확인 필수: Hooper 원본은 "1=very good, 7=very bad" 형태가 일반적이나, 데이터셋마다 다를 수 있음 -> 스케일 방향이 반대인 경우 역코딩(8 - x) 적용
- AFL 시즌 구조(프리시즌, 정규시즌, 파이널)에 따른 기간 구분 가능

### 2.4 트랙 B: Nobari et al. (3순위) --> 프로젝트 표준 스키마

| 프로젝트 표준 컬럼 | Nobari 원본 컬럼 (추정) | 변환 방법 | 비고 |
|---|---|---|---|
| `athlete_id` | `player_id` | 직접 매핑 | - |
| `date` | `date` / `week` | 주 단위인 경우 일별 확장 불가 | **확인 필요** |
| `rpe` | `RPE` | 직접 매핑 | - |
| `duration_min` | `duration` | 분 단위 확인 | - |
| `fatigue` | `fatigue` | 직접 매핑 | - |
| `stress` | `stress` | 직접 매핑 | - |
| `doms` | `DOMS` / `muscle_soreness` | 직접 매핑 또는 항목명 변환 | - |
| `sleep` | `sleep` / `sleep_quality` | 직접 매핑 | 스케일 방향 확인 |

---

## 3. 전처리 체크리스트

### 3.1 공통 전처리

- [ ] **원본 파일 무결성 확인**: 다운로드 후 파일 크기, 행 수, SHA-256 해시 기록
- [ ] **컬럼명 정규화**: 원본 컬럼명 -> 프로젝트 표준 컬럼명 매핑 적용
- [ ] **자료형 변환**: 날짜(datetime), 숫자(float/int), 문자열(string) 자료형 통일
- [ ] **결측값 패턴 분석**: 컬럼별 결측 비율 산출, 결측 패턴 시각화 (MCAR/MAR/MNAR 판단)
- [ ] **이상치 탐지**: 생리적으로 불가능한 값 필터링 (예: RR < 200ms 또는 > 2000ms, RPE < 1 또는 > 10)
- [ ] **중복 행 확인 및 제거**: (subject_id, timestamp) 또는 (athlete_id, date) 기준 중복 확인
- [ ] **시간 순서 정렬**: timestamp 또는 date 기준 오름차순 정렬 확인
- [ ] **출처 메타데이터 기록**: 데이터셋명, DOI, 다운로드 일시, 원본 파일명을 `data/raw/README.md`에 기록

### 3.2 트랙 A 전용 전처리

- [ ] **RR 간격 단위 확인**: ms 단위로 통일 (초 단위인 경우 x1000)
- [ ] **RR 아티팩트 필터링**: 연속 RR 간격 차이가 전 구간 평균의 20% 이상인 beat 제거 (Malik et al., 1996 기준) 또는 Kubios 방식 적용
- [ ] **NN 간격 변환**: 정상 동성 박동(normal-to-normal)만 추출하여 NN 간격 생성
- [ ] **세그먼트 분할**: 운동 단계(stage)별로 데이터 분할하여 단계별 HRV 산출 가능하도록 구조화
- [ ] **HRV 지표 산출 준비**: rMSSD, SDNN 산출을 위한 최소 데이터 길이 확인 (최소 5분, 권장 5분 안정 구간)
- [ ] **power(W) 단위 및 범위 확인**: 0~500W 범위 내 확인, 이상값 플래깅
- [ ] **VO2 단위 확인**: mL/min/kg 또는 mL/min -- 체중 보정 여부 확인

### 3.3 트랙 B 전용 전처리

- [ ] **RPE 스케일 확인**: CR-10 (1-10) 또는 CR-100 (1-100) 또는 Borg 6-20 -- 프로젝트 표준은 CR-10
- [ ] **sRPE 산출**: `srpe = rpe * duration_min` (원본에 sRPE가 없는 경우)
- [ ] **Hooper 항목 스케일 방향 확인**: 높은 값 = 나쁜 상태인지 확인, 역코딩 필요 여부 판단
- [ ] **Hooper Index 산출**: `hooper_index = fatigue + stress + doms + sleep`
- [ ] **휴식일 처리**: 훈련/경기가 없는 날의 sRPE를 0으로 처리할지, NA로 유지할지 결정 (ADR 기록)
- [ ] **연속 일자 확인**: 날짜 간 갭(gap) 탐지, 누락된 날짜 식별
- [ ] **시즌 구간 태깅**: 프리시즌/정규시즌/파이널 구분 (가능한 경우)
- [ ] **ACWR 산출 준비**: 최소 28일 연속 데이터 확보 여부 확인

---

## 4. data/raw/ 배치 전략

### 4.1 디렉토리 구조

```
data/
  raw/
    README.md                          # 데이터 출처, DOI, 다운로드 일시, SHA-256
    track_A/
      actes/                           # PhysioNet ACTES 원본
        subject_01_pre.csv             # (예시 파일명, 실제 구조는 다운로드 후 확인)
        subject_01_post.csv
        ...
        RECORDS                        # PhysioNet 표준 레코드 목록
        LICENSE                        # PhysioNet 라이선스 파일
      autonomic_aging/                 # 보조 데이터 (선택)
        ...
    track_B/
      carey_et_al/                     # Carey et al. Zenodo 원본
        daily_load_wellness.csv        # (예시 파일명)
        ...
        LICENSE                        # CC BY 4.0
      rossi_et_al/                     # 보조 데이터 (선택)
        ...
      nobari_et_al/                    # 보조 데이터 (선택)
        ...
  processed/
    track_A/
      hrv_features.parquet             # 표준 스키마로 변환된 HRV 특성 데이터
      load_daily.parquet               # 일별 부하 지표
    track_B/
      load_wellness_daily.parquet      # 표준 스키마로 변환된 일별 부하+웰니스 데이터
      acwr_monotony.parquet            # ACWR, Monotony, Strain 산출 결과
```

### 4.2 배치 원칙

1. **원본 불변 원칙**: `data/raw/` 내 파일은 다운로드 상태 그대로 보존, 절대 수정하지 않음
2. **데이터셋별 하위 디렉토리**: 각 데이터셋은 독립된 하위 디렉토리에 배치하여 출처 혼동 방지
3. **라이선스 파일 동봉**: 각 데이터셋 디렉토리에 해당 라이선스 파일 또는 라이선스 요약 텍스트 포함
4. **git 제외**: `data/raw/`는 `.gitignore`에 등록하여 버전 관리에서 제외 (개인정보 보호 및 파일 크기 관리)
5. **재현 가능한 다운로드 스크립트**: `src/data/download.py`에 자동 다운로드 스크립트 작성 (PhysioNet API, Zenodo API 활용)
6. **메타데이터 기록**: `data/raw/README.md`에 다음 정보 기록:

```markdown
# data/raw/ 메타데이터

## Track A: PhysioNet ACTES
- 출처: https://physionet.org/content/actes/1.0.0/
- DOI: [PhysioNet DOI]
- 다운로드 일시: YYYY-MM-DD HH:MM
- SHA-256: [해시값]
- 라이선스: PhysioNet Credentialed Health Data License 1.5.0

## Track B: Carey et al.
- 출처: https://zenodo.org/record/3566191
- DOI: 10.5281/zenodo.3566191
- 다운로드 일시: YYYY-MM-DD HH:MM
- SHA-256: [해시값]
- 라이선스: CC BY 4.0
```

### 4.3 전처리 파이프라인 실행 순서

```
1. data/raw/ 에 원본 배치 (수동 다운로드 또는 download.py)
     |
2. src/data/preprocess_track_a.py 실행
   - WFDB/CSV 읽기 -> 표준 스키마 변환 -> RR 아티팩트 필터링
   - 출력: data/processed/track_A/hrv_features.parquet
     |
3. src/data/preprocess_track_b.py 실행
   - CSV 읽기 -> 표준 스키마 변환 -> 스케일 확인/역코딩 -> 결측 패턴 기록
   - 출력: data/processed/track_B/load_wellness_daily.parquet
     |
4. src/metrics/ 모듈로 지표 산출
   - ACWR (rolling/EWMA), Monotony, Strain, sRPE, Hooper Index
   - 출력: data/processed/track_*/acwr_monotony.parquet
     |
5. notebooks/ 에서 EDA 및 통계 분석 실행
```

---

## 5. 데이터셋 간 비교 요약

### 5.1 트랙 A 후보 요약

| 평가 항목 | ACTES (1순위) | Autonomic Aging (2순위) | Ephnogram (3순위) |
|---|---|---|---|
| RR 간격 직접 제공 | O | O | X (ECG에서 추출) |
| 운동 부하 데이터 | O (power, VO2) | X | O (power, VO2) |
| 피험자 수 | ~38 | ~1,100 | ~25 |
| 다중 세션 | O (pre/post) | X | X |
| 라이선스 접근성 | 중 (Credentialed) | 상 (Open) | 하 (Restricted) |
| 전처리 난이도 | 낮음 | 낮음 | 높음 |
| **종합 적합도** | **상** | **중하** | **중** |

### 5.2 트랙 B 후보 요약

| 평가 항목 | Carey et al. (1순위) | Rossi et al. (2순위) | Nobari et al. (3순위) |
|---|---|---|---|
| sRPE / RPE+duration | O | O | O |
| Hooper 호환 설문 | O (4+1항목) | X | O (4항목) |
| 일별 기록 | O | O | 확인 필요 |
| 선수 수 | ~45 | ~20-30 | ~15-25 |
| 시즌 길이 | ~6개월 | 1-2시즌 | 1시즌 |
| 라이선스 접근성 | 상 (CC BY 4.0) | 상 (CC BY 4.0) | 상 (CC BY 4.0) |
| 종목 | AFL | 축구 | 축구 |
| **종합 적합도** | **상** | **중하** | **중** |

---

## 6. 다운로드 후 즉시 확인 사항 (Quick Validation)

다운로드 직후 아래 Python 코드로 기본 검증을 수행한다:

```python
import pandas as pd

# === Track A (ACTES) ===
# df_a = pd.read_csv("data/raw/track_A/actes/[파일명].csv")
# print(f"행 수: {len(df_a)}, 컬럼: {df_a.columns.tolist()}")
# print(f"피험자 수: {df_a['subject'].nunique()}")
# print(f"RR 범위: {df_a['rr_interval'].min():.1f} ~ {df_a['rr_interval'].max():.1f} ms")
# print(f"결측 비율:\n{df_a.isnull().mean()}")

# === Track B (Carey et al.) ===
# df_b = pd.read_csv("data/raw/track_B/carey_et_al/[파일명].csv")
# print(f"행 수: {len(df_b)}, 컬럼: {df_b.columns.tolist()}")
# print(f"선수 수: {df_b['player_id'].nunique()}")
# print(f"날짜 범위: {df_b['date'].min()} ~ {df_b['date'].max()}")
# print(f"RPE 범위: {df_b['RPE'].min()} ~ {df_b['RPE'].max()}")
# print(f"결측 비율:\n{df_b.isnull().mean()}")
```

---

## 7. 참고문헌

- Malik, M., et al. (1996). Heart rate variability: Standards of measurement, physiological interpretation, and clinical use. *European Heart Journal*, 17(3), 354-381.
- Hooper, S. L., et al. (1995). Markers for monitoring overtraining and recovery. *Medicine & Science in Sports & Exercise*, 27(1), 106-112.
- Foster, C. (1998). Monitoring training in athletes with reference to overtraining syndrome. *Medicine & Science in Sports & Exercise*, 30(7), 1164-1168.
- Carey, D. L., et al. (2018). Modelling training loads and injuries. *Medicine & Science in Sports & Exercise*, 50(11), 2267-2276.
- Goldberger, A. L., et al. (2000). PhysioBank, PhysioToolkit, and PhysioNet. *Circulation*, 101(23), e215-e220.
