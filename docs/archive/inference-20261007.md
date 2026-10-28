> 과거 실험·계획 기록입니다. 현재 실행은 [운영 안내](../operations.md), [수집 명령](../recording.md), [추론 안내](../inference.md)를 우선합니다.

# 가루·물 SmolVLA 추론 안내 — 2026-10-07

2026-10-08 새로 요청받은 두 모델의 최신 명령은 [두 모델 추론 안내](inference-models-20261008.md)에 있습니다. 아래는 기존 `261007-01` 모델의 실행·진단 기록이며 새 모델의 실물 성능을 의미하지 않습니다.

## 최신 관찰: 접근 중 그리퍼가 가루통을 밀어냄

사용자의 자연어 명령 원인 질문에 대해, 현재 제공한 가루 명령과 원본 `meta/tasks.parquet`의 task가 정확히 일치함을 확인했습니다.
저장된 토크나이저로 문장과 전처리의 끝 개행을 검사한 결과 23토큰이며, 최대 48토큰 설정에서 잘리지 않았습니다.
공식 sync 엔진은 설정의 task를 관측에 넣고 전처리·토큰화 후 정책에 전달합니다.
이 확인은 문장 일치·길이·전달 코드 경로 검사이며, 언어 이해 성능이나 파지 성공 검증은 아닙니다.
문장에 파지 세부 지시를 추가하면 행동이 바뀔 수 있지만 그리퍼 각도가 교정된다고 보장할 근거는 없습니다.
근거: `outputs/inference_matcha_w6_preflight/task_token_check.json`, 설치된 `rollout/inference/sync.py` 및 `processor/tokenizer_processor.py`.

사용자는 그리퍼가 열린 상태로 가루통에 접근하지만 각도가 약간 틀어져 대부분 통을 밀어낸다고 보고했습니다.
이는 사용자 관찰이며, 현재 실행 영상·접촉 직전 관절값·실행 명령은 아직 확보하지 않았습니다.
실행 시간을 늘리거나 상대 목표 제한을 해제하는 것만으로 파지 정렬이 교정됐다고 판단할 수 없습니다.
통을 밀어내는 동작을 반복하기 전에 시작 위치·통의 회전 방향·베이스 위치·카메라 장착 각도를 원본과 대조합니다.

장치 연결 없이 원본 가루 검증 episode 4의 파지 구간을 추출했습니다.
frame 330(11초)에는 열린 두 손가락 사이에 통이 위치하고, frame 390(13초)에는 그리퍼가 닫혀 있습니다.
이 한 시연의 시점은 현재 추론의 고정 동작 시간이나 성공 판정 기준이 아닙니다.
근거 영상과 state/action은 `outputs/inference_matcha_w6_preflight/powder_grasp_reference/`에 있습니다.

- [접촉 전 탑뷰](../../outputs/inference_matcha_w6_preflight/powder_grasp_reference/frame_0330_top.png)
- [접촉 전 손목뷰](../../outputs/inference_matcha_w6_preflight/powder_grasp_reference/frame_0330_right_wrist.png)
- [파지 시 탑뷰](../../outputs/inference_matcha_w6_preflight/powder_grasp_reference/frame_0390_top.png)

이 원본 시연에서 통을 잡는 팔의 근접 영상은 `right_wrist`, 대기 팔의 근접 영상은 `left_wrist`입니다.
사용자는 현재 추론 화면에서도 움직이는 그리퍼가 `right_wrist`에 표시된다고 확인했습니다.
이 확인에서는 손목 영상의 역할이 뒤바뀐 근거가 없으므로 카메라 매핑을 변경하지 않습니다.
해상도·키 검사가 실제 카메라 위치·기울기까지 검증한 것은 아닙니다.
손목 각도 오프셋·보정 파일·강제 그리퍼 닫기는 적용하지 않았습니다. 실제 자세 오차의 원인은 확인 필요합니다.

## 현재 사용자 요청: 시작 자세 복귀·상대 목표 제한 해제·60초 시험

`--return-to-initial-position`을 추가하면 추론 종료 후 공식 LeRobot이 연결 직후 저장한 양팔·그리퍼 관절 위치로 복귀를 시도한 다음 연결을 해제합니다.
현재 설치된 공식 구현은 기본 3초·50 Hz 관절값 선형 보간이며, `Ctrl+C`로 루프를 종료한 경우에도 이 복귀를 시도합니다.
물체 반납이나 충돌 회피 경로를 계획하는 기능이 아니므로 복귀 이동 공간을 확보합니다. 그리퍼도 시작 위치로 돌아가므로 파지 물체의 낙하 가능성을 고려합니다.
옵션을 생략하면 기존대로 자동 복귀하지 않습니다. 복귀 옵션은 `infer` 전용이며 실제 복귀 성공은 별도 실물 확인이 필요합니다.

사용자는 원본 시연의 대상 팔이 맞다고 확인하고, 5초가 짧다는 의견과 함께 목표값 제한 해제를 요청했습니다.
`infer --no-target-limit`은 이번 추론 세션의 양팔 `max_relative_target`을 `None`으로 설정합니다.
이는 목표와 현재 위치의 차이를 제한하는 처리를 해제하는 것이며, 모델의 목표값이 상대 차이 제한 없이 공식 모터 쓰기 경로에 전달됩니다.
보정·좌우 대응·단위·하드웨어 파일·연습·기록 기본 제한은 유지합니다. 이 옵션은 `infer`에서만 지원합니다.

가루 데이터 89,771프레임·50개·30 FPS 기준 에피소드 평균은 약 59.8초입니다.
다음 명령의 60초는 이를 참고한 시험 시간이며 전체 작업 완료 또는 흔들림 해소를 보장하지 않습니다.
장치 연결 없는 검증에서 `Target difference limits: {'left': None, 'right': None}`을 확인했습니다.
실물 실행 전 모델 목표가 더 크게 변할 수 있음을 고려하고, 이상 동작 시 중단합니다.

**CMD**, 현재 환경 활성화와 프로젝트 이동부터:

```bat
C:\miniforge3\condabin\conda.bat activate cuk-robotics
cd /d E:\Desktop\smolvla-bimanual-manipulation
python scripts/run_robot.py infer --policy-path models/matcha-shaker-w6-261007-01 --dataset-root data/lerobot/lmsforai/so101_bimanual_beverage_powder_v1/merged_v1 --task "With the left arm, pour powder into the fixed central bowl and return the powder container to its starting position." --wrist-fourcc MJPG --duration-s 60 --no-target-limit --return-to-initial-position
```

**PowerShell**:

```powershell
Set-Location 'E:\Desktop\smolvla-bimanual-manipulation'
& 'C:\miniforge3\envs\cuk-robotics\python.exe' scripts/run_robot.py infer --policy-path models/matcha-shaker-w6-261007-01 --dataset-root data/lerobot/lmsforai/so101_bimanual_beverage_powder_v1/merged_v1 --task 'With the left arm, pour powder into the fixed central bowl and return the powder container to its starting position.' --wrist-fourcc MJPG --duration-s 60 --no-target-limit --return-to-initial-position
```

위 명령은 실제 모터를 구동합니다. 설정만 다시 확인하려면 다음 전체 명령을 사용합니다(CMD, 활성화된 프로젝트 위치 기준).

```bat
python scripts/run_robot.py infer --policy-path models/matcha-shaker-w6-261007-01 --dataset-root data/lerobot/lmsforai/so101_bimanual_beverage_powder_v1/merged_v1 --task "With the left arm, pour powder into the fixed central bowl and return the powder container to its starting position." --wrist-fourcc MJPG --duration-s 60 --no-target-limit --return-to-initial-position --validate-only
```

기본 5초·기존 제한은 옵션을 지정하지 않은 경우 그대로입니다. 아래 최초 5초 안내와 첫 시험 결과는 이전 조건의 기록입니다.

## 1. 개요 및 확인 결과

대상은 [Taem22n/matcha-shaker-w6-261007-01](https://huggingface.co/Taem22n/matcha-shaker-w6-261007-01)입니다.
Hub revision `0faf6f558b1d6279d915d04557544de6850fffbb`에는 `tm_w6_261007_01.7z`만 있어 Hub ID를 `policy.path`로 직접 사용할 수 없습니다.
압축파일 638,974,169바이트를 내려받아 SHA256 `996a467b10489f44430f6a867d3d92137f63e5f8496b98531f990b90f5ce7442`를 확인했습니다.

전달받은 HTML 대시보드는 가루 50개·물 50개 에피소드 중 학습 80개, 검증 20개 및 10,000스텝 완료를 보고합니다.
젓기 데이터는 이 학습 목록에 없습니다. 표시된 78.6%는 정규화 행동 요소의 허용 오차 비율이며 실물 성공률이 아닙니다.
이 문서는 학습 실행 자체를 재검증한 보고서가 아닙니다.

현재 PC에 다음을 준비했습니다. 모두 `.gitignore` 적용 대상입니다.

| 경로 | 내용 |
| --- | --- |
| `models/matcha-shaker-w6-261007-01-original/` | 압축 해제 원본 7개 파일 |
| `models/matcha-shaker-w6-261007-01/` | 이 PC의 추론용 사본 |
| `models/SmolVLM2-500M-Video-Instruct/` | 공식 기반 모델의 구성·토크나이저 파일, 기반 가중치는 별도 다운로드하지 않음 |
| `outputs/inference_matcha_w6_preflight/` | 다운로드·준비 스크립트 및 검사 결과 |

추론용 사본에서 기반 모델 경로·토크나이저 경로·정책 경로를 이 PC의 경로로 변경하고 `load_vlm_weights=false`를 적용했습니다.
전체 정책 가중치를 `strict=True`로 로딩하여 기반 가중치 포함 여부와 누락·불일치가 없음을 검사했습니다.
정책 가중치와 전처리·후처리 정규화 통계의 SHA256은 원본과 같습니다. 학습 설정 원본·로컬 장치·보정·관절 제한값은 변경하지 않았습니다.
기반 구성·토크나이저의 출처 revision은 `models/SmolVLM2-500M-Video-Instruct/source_revision.json`에 기록했습니다.

## 2. 추론 조건

설치된 LeRobot 0.6.1은 `lerobot-record`를 데이터 수집에, `lerobot-rollout`을 정책 실행에 사용합니다.
프로젝트의 `scripts/run_robot.py infer`는 공식 rollout에 제어를 위임합니다.
기존 `practice`, `record`, `preview`는 유지합니다.

- 카메라: `top → camera1`, `left_wrist → camera2`, `right_wrist → camera3`. 학습 체크포인트의 매핑을 그대로 전달합니다.
- 입력 영상: 카메라 3개, 원본 640×480 RGB. 모델 내부에서는 설정된 512×512 패딩 리사이즈를 사용합니다.
- 상태·행동: 각 12차원. 원본 데이터 메타데이터와 설치된 장치의 관절 순서를 비교합니다.
- 단위: 현재 수집 조건의 `use_degrees=True` 유지. 팔 관절은 degree, 그리퍼는 `RANGE_0_100`입니다.
- 제어 목표: 30 FPS, sync 추론, 행동 묶음 50개. 첫 시험은 5초로 설정했습니다. 5초는 작업 완료 시간을 의미하지 않습니다.
- `base` 전략: 기록·Hub 업로드·리더 연결 없이 팔로워 두 대를 정책으로 제어합니다. 지시가 한쪽 팔 작업이어도 모델 출력은 양팔입니다.
- 종료: 기본 자동 시작 자세 복귀 없음. `--return-to-initial-position` 지정 시 양팔·그리퍼의 실행 시작 관절 위치로 복귀를 시도한 다음 공식 연결 해제를 수행합니다. 기존 토크 해제 설정이 적용됩니다.

현재 PC의 팔로워는 COM13·COM12, 카메라는 left_wrist 0·right_wrist 1·top 3입니다.
재연결 후 실제 장치 대응은 다시 확인합니다. 자세한 주의사항은 [실물 실험 안내](../safety.md)를 참고합니다.

## 3. 실행 순서

1. 다른 연습·기록·미리보기 프로그램을 종료합니다. OBS에 휴대폰 전체 시야가 보이고 가상 카메라가 실행 중인지 확인합니다.
2. 아래 카메라 미리보기에서 좌·우·탑뷰가 올바르게 표시되는지 확인합니다. 미리보기는 종료한 뒤 추론합니다.
3. 원본 시연과 같은 물체 배치·팔 시작 자세를 준비하고 베이스를 고정합니다. 가루 작업은 가루통·중앙 컵, 물 작업은 가루 투입 후 상태의 중앙 컵·비커를 준비합니다.
4. `--validate-only` 검사 후 해당 작업의 5초 시험을 실행합니다. 이 옵션을 빼면 실제 모터가 연결되고 구동됩니다.
5. 이상 동작 시 Ctrl+C로 중단합니다. 종료 시 팔이 중력으로 처질 수 있으며, 소프트웨어 종료는 물리적 비상정지가 아닙니다.

### CMD

환경과 작업 위치를 먼저 설정하고 카메라만 확인합니다.

```bat
C:\miniforge3\condabin\conda.bat activate cuk-robotics
cd /d E:\Desktop\smolvla-bimanual-manipulation
python scripts/run_robot.py preview --wrist-fourcc MJPG --preview-seconds 10
```

가루 작업 설정 검사. 모터·카메라를 연결하지 않습니다.

```bat
python scripts/run_robot.py infer --policy-path models/matcha-shaker-w6-261007-01 --dataset-root data/lerobot/lmsforai/so101_bimanual_beverage_powder_v1/merged_v1 --task "With the left arm, pour powder into the fixed central bowl and return the powder container to its starting position." --wrist-fourcc MJPG --duration-s 5 --validate-only
```

가루 작업 **실물 5초 시험**:

```bat
python scripts/run_robot.py infer --policy-path models/matcha-shaker-w6-261007-01 --dataset-root data/lerobot/lmsforai/so101_bimanual_beverage_powder_v1/merged_v1 --task "With the left arm, pour powder into the fixed central bowl and return the powder container to its starting position." --wrist-fourcc MJPG --duration-s 5
```

물 작업 설정 검사:

```bat
python scripts/run_robot.py infer --policy-path models/matcha-shaker-w6-261007-01 --dataset-root data/lerobot/lmsforai/so101_bimanual_beverage_water_v1/20261006_202550_457396 --task "With the right arm, pick up the beaker, pour water into the fixed central cup, and return the beaker to its starting position." --wrist-fourcc MJPG --duration-s 5 --validate-only
```

물 작업 **실물 5초 시험**:

```bat
python scripts/run_robot.py infer --policy-path models/matcha-shaker-w6-261007-01 --dataset-root data/lerobot/lmsforai/so101_bimanual_beverage_water_v1/20261006_202550_457396 --task "With the right arm, pick up the beaker, pour water into the fixed central cup, and return the beaker to its starting position." --wrist-fourcc MJPG --duration-s 5
```

### PowerShell

현재 환경의 Python을 직접 지정합니다. CMD 환경 활성화 명령은 사용하지 않습니다.

```powershell
Set-Location 'E:\Desktop\smolvla-bimanual-manipulation'
& 'C:\miniforge3\envs\cuk-robotics\python.exe' scripts/run_robot.py preview --wrist-fourcc MJPG --preview-seconds 10
```

가루 작업 설정 검사:

```powershell
& 'C:\miniforge3\envs\cuk-robotics\python.exe' scripts/run_robot.py infer --policy-path models/matcha-shaker-w6-261007-01 --dataset-root data/lerobot/lmsforai/so101_bimanual_beverage_powder_v1/merged_v1 --task 'With the left arm, pour powder into the fixed central bowl and return the powder container to its starting position.' --wrist-fourcc MJPG --duration-s 5 --validate-only
```

가루 작업 **실물 5초 시험**:

```powershell
& 'C:\miniforge3\envs\cuk-robotics\python.exe' scripts/run_robot.py infer --policy-path models/matcha-shaker-w6-261007-01 --dataset-root data/lerobot/lmsforai/so101_bimanual_beverage_powder_v1/merged_v1 --task 'With the left arm, pour powder into the fixed central bowl and return the powder container to its starting position.' --wrist-fourcc MJPG --duration-s 5
```

물 작업 설정 검사:

```powershell
& 'C:\miniforge3\envs\cuk-robotics\python.exe' scripts/run_robot.py infer --policy-path models/matcha-shaker-w6-261007-01 --dataset-root data/lerobot/lmsforai/so101_bimanual_beverage_water_v1/20261006_202550_457396 --task 'With the right arm, pick up the beaker, pour water into the fixed central cup, and return the beaker to its starting position.' --wrist-fourcc MJPG --duration-s 5 --validate-only
```

물 작업 **실물 5초 시험**:

```powershell
& 'C:\miniforge3\envs\cuk-robotics\python.exe' scripts/run_robot.py infer --policy-path models/matcha-shaker-w6-261007-01 --dataset-root data/lerobot/lmsforai/so101_bimanual_beverage_water_v1/20261006_202550_457396 --task 'With the right arm, pick up the beaker, pour water into the fixed central cup, and return the beaker to its starting position.' --wrist-fourcc MJPG --duration-s 5
```

물·가루 작업을 자동으로 연결하거나 젓기 단계로 전환하는 기능은 없습니다.
첫 시험의 동작·종료 자세·카메라 상태를 확인한 뒤 시험 시간을 조정합니다. 작업 완료 판정과 성공률 측정은 별도 실험입니다.
실행기에 자동 준비 자세 이동은 없으므로 학습 시연의 시작 자세를 사람이 준비해야 합니다.

## 4. 수행한 검증과 미확인 사항

- 전체 가중치 `strict=True` 로딩 및 원본/사본 가중치·통계 해시 일치.
- 원본 학습 작업 문장과 로컬 `meta/tasks.parquet` 일치. 가루 원본의 `bowl` 문구는 학습 조건을 보존하기 위해 그대로 사용합니다.
- 검증 에피소드 4의 시작·중간·끝 3개씩, 가루·물 총 6개 관측으로 공식 `SyncInferenceEngine` 행동 생성. 모두 유한한 12차원 출력.
- 첫 행동 묶음 생성 1.375초, 이후 0.437–0.457초. 저장 영상 기반 검사이며 실물 30 FPS 달성이나 지연 없는 제어를 입증하지 않습니다.
- 설정 검사, 단위 검사 30개, 기존 practice/record 및 두 작업 infer의 `--validate-only` 통과.
- 준비 검증에서는 실제 모터·카메라를 연결하지 않았습니다. 이후 사용자의 첫 5초 시험 결과는 아래에 구분하여 기록합니다. 실물 작업 성공·장시간 제어·종료 시 토크 해제의 물리 동작은 미검증입니다.

검사 근거는 `outputs/inference_matcha_w6_preflight/offline_smoke.json`, `runtime_preparation.json` 및 설치된 LeRobot 소스입니다.
`--validate-only`는 설정·feature 계약을 확인하며 가중치 로딩 검사를 수행하지 않습니다. 가중치·영상 기반 검사는 별도의 `offline_smoke.py`로 수행했습니다.

## 5. 사용자의 첫 5초 시험 결과

2026-10-07 15:27 사용자 제공 로그에서 5초 추론 루프 완료와 카메라 3대·양팔의 연결 해제를 확인했습니다.
사용자는 양팔이 흔들리고, 로봇을 마주 봤을 때 오른쪽에 보이는 팔이 가루통으로 이동하려다 종료됐다고 보고했습니다.
사용자 시야의 오른쪽은 설정의 오른팔과 동일하다고 확정할 수 없습니다. 논리 왼팔은 현재 COM13이고, 평소 가루 시연에서 사용하던 리더·팔로워의 대응으로 식별합니다.

원본 가루 검증 episode 4의 시작(frame 0)과 중간(frame 789)을 대조하면, 탑뷰 화면 오른쪽 팔이 가루통을 집어 붓습니다.
해당 두 프레임의 right_* 상태 6개는 같고 left_* 상태만 바뀌므로, 이 원본 화면의 오른쪽 팔은 논리 왼팔입니다.
사용자가 본 팔이 이 팔과 같다면 가루 작업에서 접근할 팔은 맞습니다. 화면 좌우만 보고 매핑을 교체하지 않습니다.
현재 배치 비교용으로 [시연 시작 탑뷰](../../outputs/inference_matcha_w6_preflight/powder_start_reference/top.png)와
[가루 붓기 중간 장면](../../outputs/inference_matcha_w6_preflight/powder_start_reference/top_mid.png)을 원본에서 추출했습니다.

로그의 1.2/3.1/3.0 Hz는 지연된 개별 루프의 dt 역수입니다. 전체 시험 평균 주파수로 해석하지 않습니다.
저장된 가루 시작 관측을 고정하여 101회 측정한 공식 동기 추론에서 새 묶음 생성은 첫 0.782초·이후 약 0.35초,
큐에 있는 행동 처리 98개는 중앙값 약 4ms였습니다. 모델은 50개 행동을 소진할 때 동기 재계산하므로 주기적인 정체가 발생할 수 있습니다.
이 검사는 카메라/모터 I/O·영상 표시·경고 출력 시간을 포함하지 않으며 실물 제어율 측정이 아닙니다.

shoulder_lift 상대 목표 제한 경고는 31회입니다. `max_relative_target=10`은 현재 위치와 목표 위치의 차이를 제한합니다.
로그만으로 어느 팔의 shoulder_lift인지, 물체 간섭·시작 자세 불일치·추종 문제·모델 오차 중 무엇이 원인인지 확정할 수 없습니다.
가루 단계 중간의 저장 관측에서는 모델이 논리 왼팔의 행동을 출력하는 사례도 확인했으나, 작은 샘플 검사로 실물 성공이나 좌우 매핑을 인증할 수 없습니다.

다음 시험 전에 평소 가루 시연에 사용한 팔과 모델의 논리 왼팔(COM13)이 같은지, 시작 배치와 주변 간섭이 같은지 확인합니다.
첫 로그 검토에서는 흔들림·접촉 여부 확인을 우선 권고했습니다. 이후 사용자가 제한 해제를 명시적으로 요청하여 위 세션 옵션과 60초 시험 명령을 추가했습니다. 제한 해제로 흔들림이 해결됐다는 실물 근거는 아직 없습니다.
추론 지연 완화는 공식 RTC 경로 등을 검토할 수 있지만 아직 이 실행기에 적용하거나 실물 검증하지 않았습니다.
결과 근거는 `outputs/inference_matcha_w6_preflight/user_rollout_log_analysis.json`과 `sync_profile.json`입니다.

## 6. 프로젝트 수행자 관점의 검토 질문

1. 가루통·비커·중앙 컵과 양팔 시작 자세를 학습 시연과 같은 조건으로 준비할 수 있는가?
2. 각 작업의 성공·실패 및 종료 기준을 어떤 관측과 허용 오차로 기록할 것인가?
3. 각 단계의 단독 성공을 확인한 뒤, 가루 종료 상태에서 물 단계로 전환하는 조건을 어떻게 검증할 것인가?
