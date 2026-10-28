> 과거 실험·계획 기록입니다. 현재 실행은 [운영 안내](../operations.md), [수집 명령](../recording.md), [추론 안내](../inference.md)를 우선합니다.

# 두 전달 모델의 추론 실행 — 2026-10-08

## 개요

다음 두 모델을 현재 PC의 공식 LeRobot `rollout` 기반 `infer` 실행 경로에 준비했습니다.
실행기는 `scripts/run_robot.py`, 실제 구현은 `src/cuk_robotics/teleoperation/cli.py`와 `inference.py`입니다.

| 배치 선택값 | 원본 저장소 | 준비한 로컬 모델 | 고정 revision |
| --- | --- | --- | --- |
| `matcha` | [Taem22n/matcha-shaker-w6-261008-01](https://huggingface.co/Taem22n/matcha-shaker-w6-261008-01/tree/main) | `models/matcha-shaker-w6-261008-01` | `991ef3d63f37f54337ab5281b2624880663a53f9` |
| `tkpota` | [tkpota/smolvla_so101_beverage_multitask](https://huggingface.co/tkpota/smolvla_so101_beverage_multitask/tree/main) | `models/smolvla_so101_beverage_multitask` | `72bb0a2918213496436c24aefa022d1c05b20b5c` |

첫 번째 저장소는 7z만 제공하므로 Hub ID를 정책 경로로 바로 사용할 수 없습니다.
압축파일 638,661,558바이트의 SHA-256은 `74a41a14762cbf6c4c4658b6c2f1d05d22d25e9c063a278f5a0743ad29498b0b`이며 Hub 값과 일치합니다.
두 번째 모델 가중치 906,712,520바이트의 SHA-256은 `97d41bdfaaa670014e74d64255d29aa6e05243574a22929f48ff14fe0d02941e`이며 Hub 값과 일치합니다.

다운로드·압축 해제 원본은 각 모델명의 `-original` 폴더에 보존했습니다.
실행용 사본에서 기반 모델·토크나이저·정책 경로를 현재 PC의 로컬 경로로 바꾸고, 전체 정책 가중치를 로딩하도록 `load_vlm_weights=false`를 적용했습니다.
`push_to_hub=false`이며 추론은 기록·업로드를 수행하지 않습니다.
두 모델 각각의 가중치와 정규화 통계 파일은 원본과 실행용 사본의 SHA-256이 일치합니다.
기존 2026-10-07 모델, 학습 출력, 원본 데이터, 장치·보정 설정은 보존했습니다.

## 실행 조건

[infer_beverage.bat](../../scripts/windows/infer_beverage.bat)은 모델 선택값과 작업 선택값을 받아 기존 실행기를 호출합니다.
현재 PC의 Python 실행 파일을 직접 사용하므로 별도 `conda activate`가 필요하지 않습니다.
다른 PC에서는 모델·데이터·장치 설정을 별도 준비하고 `CUK_ROBOTICS_PYTHON`을 실제 환경 경로로 지정해야 합니다.

- 작업: `powder`(가루) 또는 `water`(물). 각각 원본 메타데이터의 작업 문장과 데이터 경로를 사용합니다.
- 공통: CUDA, 공식 `base/sync`, 목표 30 FPS, 최대 100초, 손목 MJPG 입력.
- 이전 사용자 요청 조건: 양팔 상대 목표 차이 제한 해제(`--no-target-limit`), 종료 후 시작 관절 위치 복귀 요청(`--return-to-initial-position`).
- 기반 모델·토크나이저는 준비된 로컬 파일을 사용하며 배치 내부에서 Hub/Transformers 오프라인 모드를 설정합니다.

공통 카메라 매핑은 `top→camera1`, `left_wrist→camera2`, `right_wrist→camera3`입니다.
모델 설정 내부 영상 feature 순서는 matcha가 `camera1, camera2, camera3`, tkpota가 `camera2, camera3, camera1`입니다.
각 모델의 저장된 순서를 유지하며 서로 같은 순서로 다시 작성하지 않습니다.
관절은 원본 가루·물 메타데이터와 설치된 `bi_so_follower` 코드의 state/action 12차원 순서를 대조합니다.
현재 장치의 팔 관절은 degree, 그리퍼는 RANGE_0_100입니다. 다른 학습 PC의 병합 데이터·보정·실제 물리 배치를 독립 검증한 것은 아닙니다.

OBS 가상 카메라를 시작하고 다른 연습·기록·미리보기를 종료합니다.
시연에 맞춰 시작 자세·물체 배치를 준비하고 양팔 베이스와 이동 공간을 확인합니다.
두 모델은 한 번에 하나씩 실행합니다.
복귀는 양팔·그리퍼를 연결 직후 관절 위치로 움직이는 처리이며 물체 반납·충돌 회피 기능은 아닙니다.
Ctrl+C 후에도 복귀를 시도하므로 즉시 모터 정지로 해석하지 않습니다. [실물 주의사항](../safety.md)을 참고합니다.

## CMD 명령

먼저 프로젝트로 이동합니다.

```bat
cd /d E:\Desktop\smolvla-bimanual-manipulation
```

가루 작업으로 두 모델을 각각 실행합니다. 첫 실행이 종료된 뒤 물체·시작 자세를 다시 준비하고 다음 모델을 실행합니다.

```bat
scripts\windows\infer_beverage.bat matcha powder
```

```bat
scripts\windows\infer_beverage.bat tkpota powder
```

물 작업은 다음 명령을 각각 실행합니다.

```bat
scripts\windows\infer_beverage.bat matcha water
```

```bat
scripts\windows\infer_beverage.bat tkpota water
```

장치 연결 없는 설정 검사는 동일 명령 뒤에 `--validate-only`를 붙입니다.

```bat
scripts\windows\infer_beverage.bat matcha powder --validate-only
scripts\windows\infer_beverage.bat tkpota powder --validate-only
scripts\windows\infer_beverage.bat matcha water --validate-only
scripts\windows\infer_beverage.bat tkpota water --validate-only
```

시간을 바꾸려면 뒤에 지정합니다. 예를 들어 matcha 가루 설정만 100초로 검사합니다.

```bat
scripts\windows\infer_beverage.bat matcha powder --duration-s 100 --validate-only
```

배치는 모델·작업 뒤에 최대 7개 인자 토큰을 추가 전달합니다.
상대 목표 제한을 유지하거나 자동 복귀를 끄려면 아래 직접 명령에서 해당 플래그를 생략합니다.

```bat
C:\miniforge3\envs\cuk-robotics\python.exe scripts/run_robot.py infer --policy-path models/matcha-shaker-w6-261008-01 --dataset-root data/lerobot/lmsforai/so101_bimanual_beverage_powder_v1/merged_v1 --task "With the left arm, pour powder into the fixed central bowl and return the powder container to its starting position." --wrist-fourcc MJPG --duration-s 100 --no-target-limit --return-to-initial-position
```

tkpota 직접 실행은 같은 전체 명령의 `--policy-path`를 `models/smolvla_so101_beverage_multitask`로 변경합니다.

## PowerShell 명령

```powershell
Set-Location 'E:\Desktop\smolvla-bimanual-manipulation'
```

아래 중 하나씩 실행합니다.

```powershell
.\scripts\windows\infer_beverage.bat matcha powder
```

```powershell
.\scripts\windows\infer_beverage.bat tkpota powder
```

```powershell
.\scripts\windows\infer_beverage.bat matcha water
```

```powershell
.\scripts\windows\infer_beverage.bat tkpota water
```

PowerShell에서도 배치 뒤의 `--validate-only`와 `--duration-s`를 동일하게 사용합니다.

## 검증 결과와 미확인 사항

후속 실물 실행에 대해 사용자는 tkpota 모델로는 대체로 성공한다고 보고했습니다. 작업 종류·시도/성공 횟수·영상은 미제공이므로 측정된 성공률로 해석하지 않습니다.
원본 및 최신 Hub의 tkpota 학습 설정은 batch24·목표32000step·lr1e-4입니다. 사용자에게 전달된 20000step이 실제 체크포인트 완료 시점인지는 학습 로그 확인이 필요합니다.
기존 261007 모델은 batch2·10000step·lr5e-5, 261008 모델은 batch8·19160step·lr5e-5 설정이며 둘 다 episode 80개를 지정합니다. tkpota는 episodes=null·eval_split=0.0이고 초기 정책 경로·정규화 통계도 다릅니다. 세 모델의 이미지 증강 설정은 같습니다.
학습량 증가가 개선의 유력한 설명이지만 배치만의 효과나 원인을 확정할 수 없습니다. 비교 근거는 `outputs/inference_models_20261008_preflight/training_comparison.json`에 저장했습니다.

후속 사용자 요청으로 기본 시간을 100초로 변경하고 모델×작업 4가지 배치의 `--validate-only`에서 `duration: 100.0s`를 확인했습니다.

두 모델 모두 `strict=True`로 전체 가중치 로딩을 통과했습니다.
원본 가루·물 episode 4의 시작·중간·끝 관측 각 3개를 공식 `SyncInferenceEngine`에 넣어 모델당 6개, 총 12개의 유한한 12차원 행동을 확인했습니다.
이 표본을 두 모델 공통의 학습 제외 데이터라고 단정하지 않습니다.
각 모델의 가루·물 설정 4가지, 오프라인 설정 검사, 기존 practice/record 설정 검사와 단위 검사 32개가 통과했습니다.
최초 단위 검사에는 sandbox 임시폴더 정리 권한 오류 1개가 있었고, 프로젝트 내부 임시폴더로 지정해 재실행하여 통과했습니다. 제품 코드를 바꿔 해결한 것은 아닙니다.
실제 모터·카메라는 연결하지 않았으며 패키지도 업그레이드하지 않았습니다.

검증 산출물은 Git 제외 `outputs/inference_models_20261008_preflight/`에 저장합니다.
`downloads.json`은 파일 크기·해시, `runtime_preparation.json`은 변경 필드·원본 보존 해시, `offline_smoke.json`은 저장된 관측의 정책 출력 근거입니다.
`--validate-only`는 장치 설정·feature 계약 검사이며 가중치 로딩 또는 실물 성공 검사가 아닙니다.
실물 작업 성공률, 실제 제어율, 시작 배치 일치, 파지·붓기·반납·복귀 성공은 별도 실험이 필요합니다.
가루→물 자동 전환·완료 판정·젓기 실행은 포함하지 않습니다.

## 실험 담당자 관점의 핵심 질문

1. 두 모델 비교 시 시작 자세·물체 배치·카메라·조명을 동일하게 재현할 수 있는가?
2. 파지·붓기·반납의 성공 기준과 모델별 반복 횟수는 무엇인가?
3. 실패 시 동작 영상과 추론 지연을 함께 기록하여 모델 출력과 실물 추종 문제를 구분할 수 있는가?
