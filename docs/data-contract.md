# 수집 데이터 계약

## 현재 설정

| 항목 | 구성 |
| --- | --- |
| 장치 | bi_so_follower / bi_so_leader, 각 팔 6개 모터 |
| 영상 | observation.images.left_wrist / right_wrist / top |
| 영상 규격 | RGB, 설정상 640×480, 30 FPS |
| 상태·행동 | 공식 장치 feature 정의와 LeRobot 기록 형식 사용 |
| 작업 | 단계별 `--task` 지정; 기본 설정에는 과거 전체 작업 문장이 남아 있음 |
| 출력 | data/lerobot/<repo_id>/<실행시각>/ |

SO follower의 팔 관절 표현은 `use_degrees` 등 실제 장치 설정에 따라 달라지며 그리퍼는 범위 정규화를 사용합니다.
실제 저장 파일의 state/action 이름·순서·단위·차원은 해당 데이터셋의 `meta/info.json`과 설치된 장치 코드로 확인합니다.
프로젝트에서 임의의 12차원 배열 순서를 가정하거나 그리퍼를 degree로 해석하지 않습니다.
현재 작업 문장은 공식 `dataset.single_task`에 전달합니다. `instruction.text`라는 별도 기록 feature는 구현하지 않았습니다.

현재 실행기는 공식 기본 action processor와 기록 루프를 사용하며, 콘솔 경고 빈도와 진행 표시만 조정합니다.
선택적인 `record --top-overlay ... --raw-top-input`은 한 top 관측에서 원본 `top_raw`와
가림막 적용 `top`을 생성해 공식 기록 루프에 함께 전달합니다. 이 경우만 영상 feature가 4개이며
state/action 정의는 유지합니다. 기존 3영상 수집본과 스키마가 다르므로 직접 이어쓰기·병합하지 않습니다.
학습에는 [동시 수집 안내](paired-top-recording.md)의 내보내기로 원본/가림막 조건별 3영상 사본을 만듭니다.
두 학습본의 `top` 키는 같으며 선택 영상만 달라집니다. 원본 보존·준비 전용·업로드 조건은 [Hub 안내](huggingface.md)를 따릅니다.
설치된 공식 기록 루프는 teleop action processor의 결과를 action으로 저장하며,
`send_action()`의 `max_relative_target`으로 제한된 최종 모터 명령과 저장 action이 항상 같지는 않습니다.
과거에 추가 범위 제한이나 다른 action 처리를 적용한 세션이 있다면 원본을 보존하고 구분합니다.
현재 표시 방식은 [녹화 진행 표시 안내](troubleshooting.md#상대-목표-제한-경고와-기록-단계)를 참고합니다.

`record --wrist-fourcc MJPG`는 손목 카메라 두 대의 USB 입력을 JPEG 압축 전송으로 선택합니다.
LeRobot은 이를 디코딩한 RGB 영상을 기존 영상 기록 경로에 전달하므로 카메라 키·state/action 차원·기록 FPS는 이 옵션으로 바뀌지 않습니다.
USB 입력 형식과 저장 영상의 코덱은 별개입니다. 입력 MJPG의 손실 압축은 이미 디코딩된 영상 품질에도 영향을 줄 수 있습니다.
`meta/info.json`의 저장 영상 코덱만으로 USB 입력 형식을 알 수 없으므로 실행 명령·시작 로그와 세션 조건을 별도로 보관합니다.
YUY2와 MJPG 세션은 대상·도구의 식별성 및 실제 영상 갱신을 확인한 뒤 병합 여부를 결정합니다.

## 데이터셋·에피소드·subtask 구분

현재 실행기는 기록 실행마다 새 로컬 폴더를 만들고, 업로드 시 새 세션 저장소 이름을 붙입니다.
`--episodes 10`은 한 데이터셋 안에 에피소드 10개를 저장하는 뜻이며 subtask를 자동으로 분할하지 않습니다.
기본 작업 문장은 전체 음료 제조 과정입니다. 전체 시연이라면 가루→물→젓기를 한 에피소드에 연속 기록합니다.
단계별 수집을 선택한다면 각 실행의 `--task`를 해당 단계와 복귀 동작에 맞춰 지정해야 합니다.
현재 task·수집 기준은 [가루·물·젓기 안내](recording.md)를 사용합니다.
실행별 작업 문장을 지정하며 자동 단계 전환은 구현하지 않았습니다. 단일 모델·단계별 모델의 학습 방식은 별도 결정 대상입니다.

별도 세션·단계 데이터는 원본을 보존하고 공식 `lerobot-edit-dataset`의 merge 작업으로 새 학습 데이터셋에 합칠 수 있습니다.
설치된 LeRobot 0.6.1의 병합 구현은 FPS·robot_type·feature 구성을 검증하고 task 인덱스·에피소드 인덱스 등을 재정렬합니다.
예를 들어 단계별 10개씩 병합하면 단계 에피소드 30개가 되며, 연속 전체 시연 10개가 만들어지는 것은 아닙니다.
연속성이 확인되지 않은 서로 다른 촬영의 state/action과 영상을 하나의 긴 에피소드로 이어 붙이지 않습니다.
카메라 이름·규격·장착 위치, state/action 이름·순서·단위, 기록 FPS와 보정·조작 환경도 일관되게 유지하고 확인합니다.

학습 구조는 별도 선택입니다. 단계별 모델 3개를 학습해 상위 제어기가 선택할 수도 있고,
단계 문장을 유지한 통합 데이터로 SmolVLA 하나를 다중 작업 학습할 수도 있습니다.
후자의 경우에도 단계 완료 판정·지시 전환·이전 action queue 정리는 별도 구현·평가가 필요합니다.
설치된 학습 진입점은 복수 dataset.repo_id 목록을 지원하지 않으므로 하나의 통합 데이터셋을 사용하는 경로를 우선 검토합니다.
물 단계는 해당 음료의 가루만 든 컵, 젓기는 가루와 물이 든 컵 등 이전 단계의 종료 상태를 반영합니다. 매 시연의 내용물·비커 수위·배치·팔 자세를 복원하고 초기 상태를 수동 준비해 독립 에피소드로 기록할 수 있습니다. 실제 수위·목표량은 세션 조건에 기록하며 작업 문장만으로 정량을 보장하지 않습니다.

근거: [공식 Dataset Tools](https://huggingface.co/docs/lerobot/v0.6.1/using_dataset_tools),
[SmolVLA의 언어·영상·상태 입력](https://huggingface.co/docs/lerobot/v0.6.1/smolvla), 설치된 aggregate.py·configs/train.py.

## 수집 후 확인

에피소드 수·길이, state/action 키, 카메라 키·해상도, 빈/정지 영상, 프레임 간 시간 차이,
비정상 움직임·실패·사람 개입 여부를 확인합니다. 영상 설정 30 FPS가 실측 달성을 보장하지 않습니다.
학습용 feature 매핑은 실제 데이터와 SmolVLA 정책 설정을 함께 확인한 후 확정합니다.
데이터 내부 파일은 생성된 형식을 유지합니다.

형식 근거: [LeRobot Dataset v3](https://huggingface.co/docs/lerobot/lerobot-dataset-v3).
