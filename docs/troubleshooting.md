# 카메라·표시·기록 문제 해결

실행 명령의 기준은 [운영 안내](operations.md)입니다. 아래 설명은 현재 코드와 기존 점검 기록을 바탕으로 정리했습니다.

## 카메라 열기 실패·느린 영상

실제 번호는 `configs/local/hardware.json`에서 확인합니다. 번호는 재연결에 따라 달라질 수 있으며 과거 문서의 번호를 그대로 복사하지 않습니다.
OBS에서 탑뷰 장면과 가상 카메라 출력을 확인하고 다른 카메라 프로그램을 종료합니다.
설치된 양팔 구현은 공통 카메라를 내부 left_arm에 등록하므로 traceback의 left_arm만으로 물리적 왼손목 오류라고 판단하지 않습니다.

2026-10-20 카메라 전용 측정에서 손목 하나의 YUY2 수신은 약 7~8 FPS, MJPG에서는 두 대 모두 약 30 FPS였습니다.
practice는 MJPG를 기본 사용합니다. record·preview에서는 필요할 때 명시적으로 선택합니다.
실측 조건과 한계는 [카메라 측정 기록](archive/camera-fps-20261020.md)에 보존합니다.

현재 PC의 **PowerShell**, 모터 없이 10초 확인:

```powershell
Set-Location 'E:\Desktop\smolvla-bimanual-manipulation'
& 'C:\miniforge3\envs\cuk-robotics\python.exe' scripts/run_robot.py preview --wrist-fourcc MJPG --preview-seconds 10
```

`latest frame is too old`는 최신 프레임 수신이 허용 시간보다 늦었다는 뜻입니다.
재배치 중에도 프레임을 읽으므로 팔이 정지해 있어도 발생할 수 있습니다. 재배치 시간을 줄이는 것이 수신 지연 해결책은 아닙니다.
케이블·USB 연결·CPU/디스크 부하를 확인합니다. 장시간 모터·기록 부하에서 해결됐다고 단정하지 않습니다.
공식 기록은 시연→재배치→save_episode 순서이므로 재배치 예외가 직전 시연의 저장 이전에 발생할 수 있습니다.
Exiting이나 업로드 완료 문구만으로 목표 시연 수집 완료를 판단하지 말고 실제 메타데이터를 확인합니다.

## Rerun 연결·창 응답

기본 포트 9876이 예약되거나 사용 중이면 실행기가 사용 가능한 포트를 고릅니다.
로컬 화면은 비압축 영상이며 표시 목표는 기본 30회/초입니다. `--display-fps`는 표시 주기만 바꾸며 기록 FPS와 별개입니다.
카메라 미리보기로 입력을 먼저 분리 점검하고, CLI의 Rerun 주소와 실제 뷰어 연결을 확인합니다.

`Exceeded gRPC proxy server memory limit` 및 `Dropping old static log messages`는 Rerun 프록시의 보관 한도에 따른 표시 로그 삭제입니다.
이 메시지 자체가 LeRobot 데이터셋 삭제나 모터 통신 실패를 뜻하지 않습니다.
장시간 표시에서 과거 영상이 사라질 수 있으며 기록 결과는 별도로 확인합니다.

## 상대 목표 제한 경고와 기록 단계

`Relative goal position magnitude had to be clamped to be safe`는 현재 위치와 리더 목표 차이가 `max_relative_target`을 넘어 목표가 제한됐다는 뜻입니다.
절대 관절 범위나 초당 속도 초과를 뜻하지 않습니다. 경고를 없애려고 제한부터 높이지 않습니다.
정지 상태에서도 반복되거나 실물 움직임이 이상하면 시작 자세·보정·간섭·부하를 점검합니다.

operation·practice·record는 첫 경고와 이후 최대 30초마다 한 번 콘솔에 표시하고 생략 개수를 요약합니다.
record는 녹화·재배치·재녹화·종료 단계를 표시합니다. 모터 목표 보호와 action 저장 경로는 공식 LeRobot에 위임합니다.
카메라·통신 오류와 traceback은 이 필터로 숨기지 않습니다. 전체 경고 출력 설정을 장치 없이 확인하는 **PowerShell** 명령:

```powershell
& 'C:\miniforge3\envs\cuk-robotics\python.exe' 'E:\Desktop\smolvla-bimanual-manipulation\scripts\run_robot.py' record --verbose-target-warnings --validate-only
```

## 밝은 조명에서 영상 포화

조명·반사·노출 조건을 비교하고 파지 대상과 도구의 경계가 유지되는지 확인합니다.
이미 포화된 영상의 세부 정보는 화면 밝기나 감마 조절만으로 복원할 수 없습니다.
현재 실행기에는 노출·게인 설정 옵션이 없으므로 하드웨어 JSON에 임의 필드를 넣지 않습니다.
드라이버가 보고한 노출값만으로 실제 자동·수동 적용 상태나 화질 개선을 확정하지 않습니다.

## 추론 시작 지연

infer는 모델 로딩 후 장치 연결 전에 두 번 자동 워밍업하고 생성 행동을 버립니다.
워밍업 동안 Rerun이 비어 있을 수 있으며 동기 정책 묶음 추론 중 영상 지연은 남을 수 있습니다.
duration은 반복 경계에서 검사하므로 첫 추론이 제한시간을 넘겨도 목표가 전달될 수 있습니다.
[추론 안내](inference.md)의 현재 명령·검증 범위를 따릅니다.
