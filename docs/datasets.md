# 공개 데이터셋과 검증 기록

기존 가루·물·젓기 병합 결과를 한곳에 모았습니다. 아래는 각 기록일의 업로드·검증 결과이며, 이번 문서 정리에서 원격 상태를 새로 조회한 것은 아닙니다. 수집 기준은 [녹화 안내](recording.md), 배포 절차는 [Hub 안내](huggingface.md)를 따릅니다.

| 작업 | 실제 시연 수 | 통합본 구성 | 다운로드 화면 |
| --- | ---: | --- | --- |
| 가루 | 105 | 3종 × 35개, 총 146,004프레임 | [가루 라이브러리](dataset-library.html) |
| 물 | 54 | 3조건 × 18개, 60,630프레임 | [물 라이브러리](water-dataset-library.html) |
| 젓기 | 50 | 커피 25 + 말차라떼 25, 66,984프레임; raw/masked 두 버전 | [젓기 다운로드](stir-dataset-library.html) |

이 구성은 총 **209개 단계 시연**이며 연속 전체 제조 209회가 아닙니다. 원본·통합본·raw/masked를 중복 집계하지 않습니다. 젓기 아이스티는 포함되지 않습니다.

<a id="powder"></a>
## 가루 — 2026-10-19

각 종류의 정상 30개와 복구 5개를 병합했습니다. 아래 저장소는 모두 `lmsforAI/` 계정의 공개 Dataset입니다.

| 종류 | 통합 저장소 | 회차 | 프레임 | 고정 revision |
| --- | --- | ---: | ---: | --- |
| 커피 | [so101_powder_coffee_v2_merged35_20261019](https://huggingface.co/datasets/lmsforAI/so101_powder_coffee_v2_merged35_20261019) | 35 | 47,675 | `d044f10904c094370add1abdbc0eb5ae2b0ab502` |
| 아이스티 | [so101_powder_icetea_v2_merged35_20261019](https://huggingface.co/datasets/lmsforAI/so101_powder_icetea_v2_merged35_20261019) | 35 | 50,399 | `9ca948438dce3c0c322a12a7b0ab7a7ecabe067e` |
| 녹차라떼 | [so101_powder_greentea_v2_merged35_20261019](https://huggingface.co/datasets/lmsforAI/so101_powder_greentea_v2_merged35_20261019) | 35 | 47,930 | `f63e0b1d70f93df3a5eea6ac4c18a62e643a5fcc` |

정상 원본 0–29 → 통합 0–29, 복구 원본 0–4 → 통합 30–34입니다. 원본 ID에도 `lmsforAI/`를 붙입니다.

| 종류 | 정상 원본 | 복구 원본 |
| --- | --- | --- |
| 커피 | `so101_powder_coffee_v2_20261019_151631_424392` | `so101_powder_coffee_recovery_v2_20261019_161107_490583` |
| 아이스티 | `so101_powder_icetea_v2_20261019_164413_756570` | `so101_powder_icetea_recovery_v2_20261019_180052_322503` |
| 녹차라떼 | `so101_powder_greentea_v2_20261019_183148_147926` | `so101_powder_greentea_recovery_v2_20261019_200223_760168` |

원본 고정 revision·회차·분류·해시는 각 통합본의 `episode_mapping.csv`와 `meta/provenance.json`에 보관합니다. 당시 원본 6개 payload 58파일, 통합본 3개 payload 54파일을 원격 해시와 대조하고 원본 revision 유지 및 통합본 v3.0 태그를 확인했습니다. 105회차의 처음·마지막 210시점을 LeRobot/PyAV로 로드했습니다.

일부 원본 수치 통계와 실제 프레임의 불일치를 확인해 통합본의 수치 통계를 다시 계산했습니다. 원본 통계는 변경하지 않았습니다. 정상/복구 구분은 수집 그룹 기준이며 복구 품질·정책 향상을 전수 검증한 분류가 아닙니다.

<a id="water"></a>
## 물 — 2026-10-20

공개 통합본: [lmsforAI/so101_water_v2_merged54_20261020](https://huggingface.co/datasets/lmsforAI/so101_water_v2_merged54_20261020). **54회차·60,630프레임**, 고정 revision `fe4c0855ef99785b3b89567828b520b6833b3bb0`. 당시 v3.0 태그도 같은 commit이었습니다.

| 컵 조건 | 원본 (`lmsforAI/` 아래) | 프레임 | 원본 → 통합 회차 | 원본 revision |
| --- | --- | ---: | --- | --- |
| 커피 | `so101_water_coffee_v2_20261020_050444_130331` | 22,931 | 0–17 → 0–17 | `44c0e097c9acc3b0e5a3ae98db1de350bafe73c1` |
| 아이스티 | `so101_water_icetea_v2_20261020_070918_386791` | 17,889 | 0–17 → 18–35 | `c4766e7acf5cf46e0619426ea568931c4634409b` |
| 녹차라떼 | `so101_water_greentea_v2_20261020_061300_265602` | 19,810 | 0–17 → 36–53 | `fd6c1a253441fdcb9f61c2a0f9372c314d21bfbb` |

작업 문장은 모두 `Pour water into the cup.`입니다. 0회차 실패 세션과 과거 water_v1은 제외했습니다. 원본 payload 25파일·통합본 20파일을 원격 크기/해시와 대조하고 원본 revision 유지, 영상 10파일의 원본 SHA-256 일치를 확인했습니다. 54회차의 처음·마지막 108시점을 LeRobot/PyAV로 읽었습니다. 물 양·시연 성공률은 별도 평가 대상입니다.

<a id="stir"></a>
## 젓기 — 2026-10-31

| top 조건 | 공개 저장소 | 회차 / 프레임 | 고정 revision |
| --- | --- | --- | --- |
| 원본 | [so101_stir_merged50_20261031_raw](https://huggingface.co/datasets/lmsforAI/so101_stir_merged50_20261031_raw) | 50 / 66,984 | `796a9348ee9fc16addb260882a2f82acf4038b91` |
| 마스크 | [so101_stir_merged50_20261031_masked](https://huggingface.co/datasets/lmsforAI/so101_stir_merged50_20261031_masked) | 50 / 66,984 | `9c797baa761d6ebc2798b251e38032425b996f5e` |

각 22개 업로드 파일 기준 raw 1,431,943,567바이트, masked 1,301,273,614바이트입니다. Hub 기본 `.gitattributes`는 제외한 수치입니다. 당시 공개 상태(`private=false`)와 main/v3.0의 revision 일치, 두 저장소의 파일 목록·크기·해시를 모두 확인했습니다.

| 음료 | 로컬 수집 세션 식별자 | 원본 → 통합 회차 | 프레임 |
| --- | --- | --- | ---: |
| 커피 | `so101_stir_coffee_top_pair/20261031_050416_868075` | 0–24 → 0–24 | 34,191 |
| 말차라떼 | `so101_stir_matcha_latte_top_pair/20261031_155223_757066` | 0–24 → 25–49 | 32,793 |

말차는 전원 중단 후 이어쓰기를 포함한 최종 25개입니다. 과거 저장 4개에서 추가 21개를 안내한 명령은 현재 실행 기준이 아닙니다. 두 음료의 작업 문장은 정확히 `Stir the mixture in the cup with the muddler.`입니다.

두 통합본은 데이터 열·손목 영상·회차 대응이 동일하고 top 조건만 다릅니다. 동일한 고정 바닥 마스크 해시를 확인했습니다. 수집 원본 2개는 4영상이며, 음료별 raw/masked 사본 4개와 함께 보존됩니다. 로컬 prepared 사본의 ID가 원격 게시를 뜻하지는 않습니다. 공개 전송은 위 통합본 두 개에 수행했습니다.

통합본별 영상 12개를 재인코딩 없이 복사하고 원본 SHA-256 일치를 확인했습니다. 각 50회차의 처음·마지막, 두 통합본 합계 200관측을 실제 LeRobot/PyAV로 읽어 영상 shape/유한값·state/action·회차/task를 확인했습니다. 원본 6폴더·로컬 설정·보정의 보존도 당시 검사했습니다.

공개 `episode_mapping.csv`와 `meta/provenance.json`에 원본 ID·회차·해시·병합 방법을 기록하며 로컬 절대 경로는 제외했습니다. 당시 `train: 0:50`이고 별도 평가 분할은 없었습니다. raw/masked 비교에는 같은 분할을 적용합니다.

## 공통 병합 방법과 검증 한계

- 설치된 공식 `lerobot.datasets.aggregate.aggregate_datasets`로 새 통합본을 만들었습니다. `concatenate_videos=False`, `concatenate_data=False`로 원본 파일을 분리 유지하고 영상 재인코딩을 하지 않았습니다.
- LeRobot v3.0, 명목 30 FPS, 3영상 `left_wrist/right_wrist/top` 각 640×480 RGB, state/action 각 12차원입니다. 실제 feature 이름·순서를 보존했으며 모든 값을 degree로 단정하지 않습니다. 보정·정규화·물리적 좌우 대응은 메타데이터만으로 확정할 수 없습니다.
- 작업/schema 일치, 모든 프레임 열의 값 보존(전역 index/episode_index 재배치 제외), 회차 길이·경계·timestamp·파일 참조를 확인했습니다.
- 통합본의 전역·회차별 수치 통계는 실제 프레임에서 float64·모집단 표준편차·선형 분위수로 계산했습니다. 영상 통계는 공식 원본 표본 통계 집계를 유지했습니다.
- 원격 대조는 LFS의 SHA-256과 일반 파일의 Git blob SHA-1을 사용했습니다. 고정 revision을 재현 기준으로 삼으며 이후 main/tag 변경 여부는 재사용 시 확인합니다.

이는 구조·값 보존·표본 로딩·배포 검증입니다. 모든 영상의 의미적 성공, 혼합 품질, 센서 실측 FPS, 학습·실물 성능을 입증하지 않습니다. [평가 계획](evaluation.md)을 별도로 적용합니다.

## 로컬 근거와 이전 데이터

검사 코드·로그·manifest·수치 통계는 Git 제외 `outputs/powder_merge_20261019/`, `outputs/water_merge_20261020/`, `outputs/stir_merge_20261031/`에 보관합니다. 젓기 업로드 최종 상태는 `publication.json`이 기준이며 병합 직후 `verification.json`의 업로드 대기는 과거 상태입니다. 상세 원문은 `docs/local/history/`에 남깁니다.

이전 가루 v1 공개본 [so101_bimanual_beverage_powder_v1](https://huggingface.co/datasets/lmsforAI/so101_bimanual_beverage_powder_v1)은 2026-10-06의 50회차·89,771프레임 별도 데이터입니다. 업로드 revision `ea4d7d9c23434eb919db85c082dac21b1056eb3c`, 카드 수정 revision `aed8afb4bc681509a72a2a8eddb5761570b3e749`이며 위 v2 수량에 포함하지 않습니다. 당시 작업 문장의 `fixed central bowl`과 팔 방향 조건도 달라 호환성을 검증 없이 가정하지 않습니다. 전체 이력은 정리 전 Hub 문서의 로컬 백업에 보관합니다.
