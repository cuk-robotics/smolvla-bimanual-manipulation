# 연습·기록 운영 안내

실행·종료·이어쓰기의 기준 문서입니다. 음료별 task와 수집 기준은 [녹화 안내](recording.md), 동시 top 수집은 [paired 안내](paired-top-recording.md)를 사용합니다.

## 준비와 설정 검사

- [의존성](dependencies.md)을 준비한 Python 환경을 활성화하고 저장소 루트에서 실행합니다. 아래 `python` 명령은 **CMD와 PowerShell 공통**입니다. PC별 경로는 Git 제외 `docs/local/commands.md`에 보관합니다.
- 실제 포트·카메라는 `configs/local/hardware.json`, 보정은 `calibration/so101/`에서 읽습니다. 여러 장치 사용 프로그램을 동시에 실행하지 않습니다.
- 리더·팔로워 시작 자세, 베이스 고정, 주변 간섭과 종료 시 토크 해제를 확인합니다. [실물 절차](safety.md).
- 카메라 모드는 OBS 가상 카메라를 켜고 실제 프레임 갱신을 확인합니다. 재연결 후 번호가 달라질 수 있습니다. 일반 기록·추론의 top 입력도 의도한 마스크 상태인지 확인합니다.

```text
python scripts/check_config.py
python scripts/run_robot.py operation --validate-only
python scripts/run_robot.py practice --validate-only
python scripts/run_robot.py record --validate-only
```

첫 명령은 공개 예시와 기록 설정을 검사합니다. 나머지는 로컬 설정과 설치된 LeRobot이 필요하지만 모터·카메라에 연결하지 않습니다. 기록 기본 설정은 과거 전체 제조 작업 문장이므로 단계별 수집은 `--task`를 명시합니다.

## 조작·연습·미리보기

아래 명령은 한 번에 하나씩 실행합니다. operation/practice는 실제 모터를 구동합니다.

```text
python scripts/run_robot.py operation
python scripts/run_robot.py practice
```

operation은 카메라 없이 조작하고, practice는 카메라 3개를 표시합니다. 기본 제어 목표 주기 60 Hz, 저장·업로드 없음, 종료 Ctrl+C입니다. practice의 손목 입력은 기본 MJPG이며 명시한 `--wrist-fourcc`가 우선합니다. `max_relative_target`은 현재 위치와 목표 위치의 차이 제한이며 초당 속도 제한이 아닙니다.

모터 없이 카메라만 확인:

```text
python scripts/run_robot.py preview --wrist-fourcc MJPG --preview-seconds 10
```

브라우저 미리보기는 별도 진입점 `scripts/preview_cameras.py`입니다.

## 기록과 종료

다음은 일반 3영상 로컬 젓기 기록 예시입니다. 원본·마스크를 함께 남기려면 [4영상 수집 명령](paired-top-recording.md#record)을 사용합니다.

```text
python scripts/run_robot.py record --repo-id local/stir_coffee --task "Stir the mixture in the cup with the muddler." --episodes 25 --episode-seconds 180 --reset-seconds 30 --fps 30 --wrist-fourcc MJPG
```

record는 입력 형식 생략 시 하드웨어 설정을 따릅니다. practice의 MJPG 기본값을 자동 적용하지 않습니다. `--episode-seconds`는 회차 상한, `--reset-seconds`는 재배치 시간입니다. 재배치 중에도 원격조작이 계속됩니다.

| 키 | 동작 |
| --- | --- |
| 오른쪽 방향키 | 현재 시연 또는 재배치 구간 종료 |
| 왼쪽 방향키 | 현재 시연 재녹화 |
| Esc | 전체 기록 종료; 시연 도중이면 미완료 시연이 저장될 수 있음 |

완료한 시연을 오른쪽 키로 마친 뒤 재배치 구간에서 Esc로 종료합니다. Ctrl+C·강제 종료·전원 분리에서는 진행 중 회차의 저장을 보장하지 않습니다. 물체를 내려놓고 팔을 안정된 자세에 둔 뒤, 영상 정리·장치 해제·요청한 내보내기/업로드가 끝날 때까지 기다립니다.

새 실행의 로컬 출력은 `data/lerobot/<기본 repo_id>/<실행시각>/`입니다. 업로드나 paired 준비를 요청하면 실제 대상 ID에 실행시각을 붙입니다. 시작 로그의 출력 경로와 정확한 대상 ID를 보관합니다. 업로드 옵션의 의미와 실패 처리는 [Hub 안내](huggingface.md)에서 확인합니다.

<a id="resume"></a>
## 중단 후 이어쓰기

1. 중단된 프로그램을 종료하고 **기존 세션 폴더 전체를 백업**합니다. `meta/info.json`의 저장 개수뿐 아니라 회차 메타데이터·데이터 행·영상 참조가 일치하는지 확인합니다. 파일이 있다고 저장 완료로 단정하지 않습니다.
2. 기존 task·정확한 repo ID·스키마·FPS·보정·입력 조건을 유지합니다. paired는 원래 `top_pair.json`과 동일한 PNG 및 옵션이 필요합니다. 3영상과 4영상 사이의 이어쓰기는 허용하지 않습니다.
3. `--episodes`는 **추가 개수**, `--expected-episodes`는 재개 전 저장 개수입니다. 예: 저장 4개에서 총 25개를 목표로 하면 추가 21개입니다. 이미 25개라면 이 예시를 재실행하지 않습니다.
4. `--validate-only` 검사 후 전원·입력·시작 자세를 복원하고 새 시연부터 기록합니다. 미저장 회차의 중간 동작은 이어지지 않습니다.

**PowerShell 예시**: 아래 값은 설명용이므로 실제 로그의 경로·ID·개수로 바꿉니다. 일반 3영상 세션의 설정 검사이며 실제 녹화는 하지 않습니다.

```powershell
$resumeRoot = 'data/lerobot/local/stir_coffee/SESSION_TIMESTAMP'
$resumeRepo = 'local/stir_coffee'
python scripts/run_robot.py record --resume --dataset-root $resumeRoot --repo-id $resumeRepo --expected-episodes 4 --task "Stir the mixture in the cup with the muddler." --episodes 21 --episode-seconds 180 --reset-seconds 30 --fps 30 --wrist-fourcc MJPG --validate-only
```

이 예시의 ID는 업로드 없는 일반 로컬 수집 기준입니다. Hub/paired 준비 세션은 시각 접미사가 붙은 **실제 ID**를 사용합니다. 검사 통과 후 실제 이어쓰기는 동일 전체 명령에서 `--validate-only`만 제거합니다. 자동 업로드 재시도나 미완성 파일 복구 기능으로 해석하지 않습니다.

반복 경고·카메라 문제는 [문제 해결](troubleshooting.md), 실행 파일 목록은 [scripts 안내](../scripts/README.md)를 참고합니다.
