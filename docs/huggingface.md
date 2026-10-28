# GitHub와 Hugging Face 역할

2026-10-19 커피·아이스티·녹차라떼별 정상30개+복구5개 통합 저장소3개를 공개 생성하고 원격 해시를 확인했습니다. [저장소 링크·고정 revision·검증 결과](powder-merged35-20261019.md)를 참고합니다. 기존 원본6개는 보존했습니다.

GitHub 저장소는 코드·문서·공개 설정 예시를 관리합니다.
Hugging Face Dataset 저장소는 검토한 LeRobot 데이터 전체와 데이터 카드를 관리합니다.
학습된 모델은 별도 Model 저장소에 학습 환경·입출력 키·데이터 revision·성능 한계를 함께 기록합니다.

## 이름과 기존 데이터

2026-10-05 읽기 전용 조회로 로그인 계정 `lmsforAI`의 [기존 공개 저장소](https://huggingface.co/datasets/lmsforAI/bimanual-test-version)를 확인했습니다.
해당 `meta/info.json`에는 10개 에피소드, 41,160 프레임, 30 FPS, 영상 3개, LeRobot 형식 v3.0이 기재되어 있습니다.
이는 메타데이터 확인이며 영상 품질·학습 성능 검증 결과는 아닙니다.

새 기본 이름은 `lmsforAI/so101_bimanual_beverage_trajectories_v1`입니다.
로봇 종류·양팔 구성·작업·시연 데이터·수집 시리즈 버전을 표현한 프로젝트 명명안이며 Hub가 요구하는 표준 이름은 아닙니다.
`v1`은 새 이름으로 시작하는 수집 시리즈 버전이고 LeRobot 파일 형식 v3.0과 별개입니다.
계정의 이전 날짜 접미사 관례를 따라 실제 업로드 이름에는 한국 시간 `YYYYMMDD_HHMMSS_마이크로초`를 붙입니다.
매 실행은 별도 데이터셋이며 이전 버전을 덮어쓰거나 자동 병합하지 않습니다.

이름의 근거: [기존 날짜 포함 이름](https://huggingface.co/datasets/lmsforAI/so101_cube_pick_place_dualcam_v2_20260603_062943),
[다른 SO-101 양팔 작업 이름 예시](https://huggingface.co/datasets/lucasngoo/bimanual-so101-pick-and-place).

## 로그인과 실행

현재 PC에서는 `lmsforAI` 로그인 상태를 확인했습니다. 업로드에는 대상 계정의 쓰기 권한이 필요합니다.
토큰은 Git·JSON 설정·공유 명령에 저장하지 않습니다. 다른 환경이나 권한 오류 시 **CMD**에서 확인·로그인합니다.

```bat
C:\miniforge3\condabin\conda.bat activate cuk-robotics
cd /d E:\Desktop\smolvla-bimanual-manipulation
hf auth whoami
hf auth login
```

기존 공개 저장소와 동일한 공개 기록·업로드 명령:

```bat
python scripts/run_robot.py record --push-to-hub --episodes 10 --episode-seconds 180 --reset-seconds 30
```

비공개 저장소로 기록·업로드:

```bat
python scripts/run_robot.py record --push-to-hub --private
```

`python scripts/run_robot.py record`는 업로드 없이 로컬에만 기록합니다.
`--validate-only`는 업로드 옵션을 검사해도 장치·네트워크에 연결하거나 Hub 저장소를 만들지 않습니다.
실행 로그의 Hub destination은 업로드 예정 주소이며 실제 생성·업로드 성공을 의미하지 않습니다.

## 종료와 데이터 보존

오른쪽 방향키는 시연을 마치고 재배치로 이동하고, 왼쪽 방향키는 재기록, Esc는 기록 종료입니다.
목표 개수 완료 또는 Esc 종료 시 공식 LeRobot이 데이터·영상 정리와 장치 연결 해제 후 저장된 에피소드를 업로드합니다.
시연 도중 Esc로 끝내면 미완료 시연도 저장될 수 있으므로 완료 시연만 남기려면 오른쪽 방향키로 마친 뒤 재배치 구간에서 Esc로 종료합니다.
저장 에피소드가 없으면 업로드를 건너뜁니다. 프로세스 강제 종료·전원 종료에서는 업로드를 보장하지 않습니다.
Ctrl+C 시 진행 중인 에피소드 저장도 보장하지 않습니다. 업로드 성공·명령 종료까지 기다립니다.

`templates/dataset_card.md`는 실제 수집 정보로 채워 사용할 양식이며 실행기가 자동 반영하지 않습니다.
설치된 LeRobot의 `push_to_hub()`는 자동 생성 데이터 카드의 라이선스 기본값으로 `apache-2.0`을 사용합니다.
이는 프로젝트 코드의 MIT 라이선스와 별개이며, 데이터 사용권 결정은 별도 확인해야 합니다.
미확인 성공률·에피소드 수·사용권을 임의로 기입하지 않습니다.
로컬 `data/lerobot/<기본 repo_id>/<실행시각>/`의 한 실행 폴더 전체가 데이터셋 단위입니다.
네트워크·권한 오류 시 이 폴더는 보존됩니다. 자동 재업로드는 구현하지 않았습니다.
여러 실행 폴더를 수동으로 합치거나 내부 파일 이름을 변경하지 않습니다.
검증한 공식 병합 결과는 아래 가루 단계 통합본을 참고합니다.
실물 기록·종료 업로드의 전체 과정은 이번 코드 변경에서 실행하지 않았습니다.

근거: 설치된 LeRobot 0.6.1 `lerobot_record.py` 종료 절차,
[Hugging Face 데이터 카드](https://huggingface.co/docs/hub/datasets-cards),
[LeRobot Dataset v3](https://huggingface.co/docs/lerobot/lerobot-dataset-v3).

## 가루 단계 50개 병합 — 2026-10-06

사용자 요청에 따라 타임스탬프 없는 `lmsforAI/so101_bimanual_beverage_powder_v1`을 통합 ID로 지정했습니다.
[통합 데이터셋](https://huggingface.co/datasets/lmsforAI/so101_bimanual_beverage_powder_v1)의 공개 업로드를 완료했습니다.
업로드 revision은 `ea4d7d9c23434eb919db85c082dac21b1056eb3c`이며,
원격 README·data·meta·videos 전 파일의 해시를 로컬 통합본과 대조하여 일치 확인했습니다.

| 원본 수집 세션 | 원본 에피소드 | 통합 에피소드 | 프레임 |
| --- | --- | --- | --- |
| `20261006_042142_069934` | 0~4 | 0~4 | 8,076 |
| `20261006_054552_960003` | 0~44 | 5~49 | 81,695 |
| 합계 | 50개 | 0~49 | 89,771 |

두 원본의 data·meta·videos 모든 파일이 Hub revision과 일치하는 것을 해시로 확인한 후,
설치된 LeRobot 0.6.1의 공식 `aggregate_datasets`로 촬영 순서대로 병합했습니다.
영상은 재인코딩 없이 복사하고 에피소드 번호·전역 인덱스·경계·영상 파일 참조를 함께 갱신했습니다.
설치된 공식 병합기의 최종 전역 통계는 원본 통계를 합산하므로, 재인덱싱된 `index`·`episode_index`·`task_index`는 통합 데이터 기준으로 재계산했습니다.
장치 코드·보정·기록 실행기·기존 두 원본은 변경하지 않았습니다. 기록 실행의 타임스탬프 접미사 규칙은 유지하며 이번 통합본에만 접미사를 사용하지 않습니다.

README는 영문으로 정리했으며 사용자의 촬영 순서를 **제자리 → 왼팔로 가루통 잡아 들어올리기 → 컵으로 이동하여 손목을 돌려 가루 투입 → 손목 복귀 → 통이 있던 위치 근처에 내려놓기 → 팔 원상복구**로 기록했습니다.
원본 작업 지시의 `fixed central bowl`과 `task_index=0`은 보존하며, 컵 표현과의 차이를 카드에 명시했습니다. 프레임별 단계 라벨은 새로 만들지 않았습니다.
공개 카드에서는 두 세션 수집·병합 순서와 로컬 원본 보관 내용은 유지하고, 원본 저장소 링크·계정명·촬영시각·원본 revision 등 불필요한 식별 정보는 제외했습니다.
카드 수정 revision은 `aed8afb4bc681509a72a2a8eddb5761570b3e749`이며 README 외 원격 파일의 내용·크기는 변경 전과 일치합니다.

검증: 50개·89,771행, 연속 에피소드 번호·전역 인덱스·에피소드 내부 프레임·30 FPS 기준 저장 타임스탬프,
state/action 12차원 유한값과 원본 값 일치, 모든 영상 13개 전체 디코딩·원본 영상 해시 일치,
각 에피소드의 시작·끝 100개 프레임에 대한 실제 LeRobot PyAV 로더 읽기 확인.
원본 5개와 45개 세션 파일의 검사 전후 해시도 일치했습니다.
시연 성공·영상 정지·실제 센서 동기화·학습 성능은 이 구조 검사 범위에 포함하지 않습니다.

로컬 통합 경로: `data/lerobot/lmsforai/so101_bimanual_beverage_powder_v1/merged_v1/`.
출처: 통합본의 `meta/merge_provenance.json`. 재현 스크립트: Git 제외 `outputs/merge_powder_sessions_20261006.py`.
로컬 검증 결과: `outputs/powder_merge_validation_20261006.json`.
오프라인 설정 검사·기존 단위 검사 24개·practice/record --validate-only도 통과했습니다. 실제 장치 연결·구동은 수행하지 않았습니다.

학습용 전달 후속 확인: LeRobot 0.6.1·PyAV에서 SmolVLA 기본 50-step action chunk를 구성하여
episode 0·4·5·49의 종료 프레임을 PyTorch DataLoader 배치로 읽었습니다.
action `(4, 50, 12)`·state `(4, 1, 12)`·각 영상 `(4, 3, 480, 640)` 및 에피소드 종료 후 action padding 확인.
이는 학습 입력 로딩 확인이며 모델 forward/backward·팀원 PC 환경·학습 성능 검증은 아닙니다.
결과는 Git 제외 `outputs/powder_training_batch_check_20261006.json`에 보관했습니다.
