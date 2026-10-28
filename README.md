# SmolVLA Bimanual Beverage Manipulation

SO-101 팔로워 2대·리더 2대·카메라 3대로 음료 제조 시연 데이터를 수집합니다.
실행기는 설치된 LeRobot에 로봇 제어와 기록을 위임합니다.

이 저장소는 **원격조작·수집 환경**을 관리합니다. 학습·평가·최종 추론 통합 대상은
[beverage-autonomy](https://github.com/cuk-robotics/beverage-autonomy)입니다.
기존 추론·학습 보조 코드는 이전이 완료될 때까지 유지합니다. [역할 분담](docs/repository-split-20261028.md).

## 시작하기

1. [환경 준비](docs/dependencies.md)에 따라 Python·LeRobot 환경을 준비합니다.
2. `configs/hardware/so101_bimanual.example.json`을 `configs/local/hardware.json`으로 복사하고 실제 포트·카메라 번호를 입력합니다.
3. 해당 장치의 보정 파일 4개를 `calibration/so101/`에 준비합니다. 다른 장치의 보정값을 재사용하지 않습니다.
4. [운영 안내](docs/operations.md)의 설정 검사 후 연습·기록을 실행합니다.

현재 PC의 **PowerShell**, 장치 연결 없는 검사:

```powershell
Set-Location 'E:\Desktop\smolvla-bimanual-manipulation'
& 'C:\miniforge3\envs\cuk-robotics\python.exe' scripts/check_config.py
& 'C:\miniforge3\envs\cuk-robotics\python.exe' scripts/run_robot.py practice --validate-only
& 'C:\miniforge3\envs\cuk-robotics\python.exe' scripts/run_robot.py record --validate-only
```

## 실행 모드

| 모드 | 역할 |
| --- | --- |
| `operation` | 카메라 없이 리더·팔로워 양팔 조작 |
| `practice` | 양팔 조작과 카메라 3개 표시; 손목 입력 기본 MJPG |
| `record` | 공식 LeRobot 시연 기록; Hub 업로드는 명시적으로 요청할 때만 수행 |
| `preview` | 모터 연결 없이 카메라 3개 Rerun 표시 |
| `infer` | 기존 정책을 공식 rollout으로 실행; 새 저장소 이전 전 유지 |

`scripts/run_robot.py`가 공통 진입점이며 구현은 `src/cuk_robotics/`에 있습니다.
`--validate-only` 없는 operation·practice·record·infer는 실제 모터를 구동합니다.
실행 전 [시작 자세·종료 절차](docs/safety.md)를 확인합니다.

## 문서 찾기

| 목적 | 문서 |
| --- | --- |
| 연습·기록·종료 | [운영 안내](docs/operations.md) |
| 음료별 수집 명령 | [가루·물 수집](docs/recording.md) · [작업대·도구 배치](docs/workspace.md) |
| 카메라·Rerun·경고 점검 | [문제 해결](docs/troubleshooting.md) |
| 기존 모델 추론·학습 | [추론](docs/inference.md) · [명령 복사 HTML](docs/inference-commands.html) · [로컬 학습](docs/training.md) |
| 데이터 규격·업로드 | [데이터 계약](docs/data-contract.md) · [Hugging Face](docs/huggingface.md) |
| 데이터셋 조회 | [가루 라이브러리](docs/dataset-library.html) · [물 라이브러리](docs/water-dataset-library.html) |
| 구조·공유 기준 | [저장소 관리](docs/repository.md) · [아키텍처](docs/architecture.md) |
| 평가·과거 근거 | [평가 계획](docs/evaluation.md) · [과거 문서 목록](docs/repository.md#과거-기록) |

## 구현 범위

연습·시연 기록·정책 추론 실행기와 장치 연결 없는 검사가 있습니다.
공개 가루 통합본은 35개씩 3종, 물 통합본은 54개이며 상세 근거는
[가루 결과](docs/powder-merged35-20261019.md)와 [물 결과](docs/water-merged54-20261020.md)에 있습니다.
음성·키워드 라우팅, 가루→물→젓기 자동 전환, 완료 판정과 정량 실물 평가는 미완료입니다.
설정 검사나 저장 관측 추론 성공을 실물 작업 성공률로 해석하지 않습니다.

## 검증 및 공유

활성화된 Python 환경에서 프로젝트 루트 기준으로 실행합니다.

```text
python scripts/check_config.py
python scripts/check_git_hygiene.py
python -m unittest discover -s tests -v
```

기본 검사는 표준 라이브러리로 실행하며, LeRobot 통합 검사는 해당 환경이 없으면 건너뜁니다.
데이터·모델·보정·로컬 설정·인증정보·작업 기록은 Git에서 제외합니다.
프로젝트 코드는 [MIT](LICENSE), 외부 모델·데이터·라이브러리의 사용권은 별도입니다.
