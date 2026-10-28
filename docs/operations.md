# 연습·기록 운영 안내

현재 명령의 기준 문서입니다. 과거 루트 RUN_GUIDE의 중복 내용은 이 문서로 통합했습니다.
음료별 task·수집 개수는 [수집 명령](recording.md), 작업대 배치는 [작업환경](workspace.md)을 따릅니다.
기록 설정의 기본 작업 문장은 과거 전체 과정이므로 단계별 수집은 반드시 해당 안내의 `--task`를 사용합니다.

## 실행 준비

- 실제 포트·카메라 번호는 `configs/local/hardware.json`, 장치 보정은 `calibration/so101/`에서 읽습니다.
- 리더·팔로워를 같은 시작 자세로 맞추고 베이스·주변 간섭을 확인합니다. [실물 주의사항](safety.md).
- 카메라를 쓰는 모드에서는 OBS 탑뷰와 가상 카메라를 켜고 다른 카메라 프로그램을 종료합니다.
- 여러 로봇 실행 프로그램을 동시에 실행하지 않습니다. 카메라 번호는 재연결 시 달라질 수 있습니다.

**CMD**, 현재 PC:

```bat
C:\miniforge3\condabin\conda.bat activate cuk-robotics
cd /d E:\Desktop\smolvla-bimanual-manipulation
```

이후 CMD 예시는 위 환경에서 한 번에 하나씩 실행합니다. 다른 PC는 경로를 바꿉니다.
새 환경 설치는 [의존성 안내](dependencies.md)를 참고합니다.

## 장치 연결 없는 검사

```bat
python scripts/check_config.py
python scripts/run_robot.py operation --validate-only
python scripts/run_robot.py practice --validate-only
python scripts/run_robot.py record --validate-only
```

첫 명령은 공개 장치 예시와 기록 설정을 검사합니다. 나머지는 설치된 LeRobot과 로컬 장치 설정이 필요하지만 모터·카메라를 연결하지 않습니다.

## 무카메라 조작과 연습

카메라 없이 리더 2대·팔로워 2대 조작:

```bat
python scripts/run_robot.py operation
```

카메라 3개를 표시하며 조작:

```bat
python scripts/run_robot.py practice
```

둘 다 기본 제어 목표 주기는 60 Hz이며 데이터 저장·업로드는 없습니다. 종료는 Ctrl+C입니다.
practice의 손목 입력 기본값은 MJPG이며 `--wrist-fourcc YUY2`를 명시하면 우선합니다.
현재 위치와 목표 위치의 차이는 기존 `max_relative_target` 설정으로 제한합니다. 초당 속도 제한이 아닙니다.

**PowerShell**, 환경 활성화 없이 연습:

```powershell
Set-Location 'E:\Desktop\smolvla-bimanual-manipulation'
& 'C:\miniforge3\envs\cuk-robotics\python.exe' scripts/run_robot.py practice
```

## 시연 기록

새 음료별 수집에는 [가루·물 수집 명령](recording.md)을 사용합니다.
다음은 **기본 전체 작업 문장을 사용하는 로컬 기록 예시**입니다.

```bat
python scripts/run_robot.py record --episodes 10 --episode-seconds 180 --reset-seconds 30 --fps 30 --wrist-fourcc MJPG
```

기본은 로컬 저장이며 업로드하지 않습니다. 공개 업로드를 요청하는 전체 명령 예시:

```bat
python scripts/run_robot.py record --episodes 10 --episode-seconds 180 --reset-seconds 30 --fps 30 --wrist-fourcc MJPG --push-to-hub
```

비공개 업로드는 위 명령에 `--private`를 추가합니다. 명시적 `--push-to-hub` 없이 `--private`만 사용할 수 없습니다.
record는 입력 형식을 생략하면 하드웨어 설정을 따르며 practice의 MJPG 기본값을 자동 적용하지 않습니다.
MJPG는 손실 압축 입력이므로 도구·용기 경계가 식별되는지 확인합니다.

| 키 | 동작 |
| --- | --- |
| 오른쪽 방향키 | 현재 시연 또는 재배치 구간 종료 |
| 왼쪽 방향키 | 현재 시연 재녹화 |
| Esc | 전체 기록 종료; 시연 도중이면 미완료 시연이 저장될 수 있음 |

완료된 시연만 남기려면 오른쪽 방향키로 시연을 마친 뒤 재배치 구간에서 Esc로 종료합니다.
Ctrl+C는 진행 중인 시연의 저장을 보장하지 않습니다. 종료·영상 정리·요청한 업로드가 끝날 때까지 터미널을 유지합니다.
종료 시 토크 해제와 처짐을 고려해 물체를 내려놓고 팔을 안정된 자세에 둡니다.

로컬 결과는 `data/lerobot/<repo_id>/<실행시각>/`에 저장합니다. 업로드 시에는 Hub 이름에도 한국 시간 실행시각을 붙입니다.
기본 실행은 새 세션입니다. `--resume`은 기존 데이터 폴더·정확한 repo ID·저장 개수를 확인하고 별도로 사용합니다.
저장·이어쓰기·업로드 세부 조건은 [데이터 계약](data-contract.md), [Hub 안내](huggingface.md)를 참고합니다.

## 카메라만 확인

모터 없이 Rerun에서 카메라를 확인합니다.

```bat
python scripts/run_robot.py preview --wrist-fourcc MJPG --preview-seconds 10
```

브라우저 미리보기는 별도 진입점 `scripts/preview_cameras.py`를 사용합니다. 두 표시 경로는 서로 다른 기능입니다.
Windows 실행 편의 파일은 [scripts 안내](../scripts/README.md), 기존 모델 실행은 [추론 안내](inference.md)를 참고합니다.
카메라 타임아웃·Rerun·반복 경고는 [문제 해결](troubleshooting.md)에 정리했습니다.
