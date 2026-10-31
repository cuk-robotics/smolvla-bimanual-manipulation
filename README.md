# SmolVLA Bimanual Beverage Manipulation

SO-101 팔로워 2대·리더 2대·카메라 3대로 음료 제조 시연을 수집합니다. 로봇 제어와 기록은 설치된 LeRobot에 위임합니다.

이 저장소는 원격조작·수집 환경을 관리합니다. 학습·평가·최종 추론의 통합 대상은 [beverage-autonomy](https://github.com/cuk-robotics/beverage-autonomy)이며, 이전 완료 전까지 기존 추론·학습 보조 코드를 유지합니다. [저장소 역할과 이전 기준](docs/repository.md#repositories).

## 시작하기

1. [환경 준비](docs/dependencies.md)에 따라 Python·LeRobot 환경을 준비합니다.
2. `configs/hardware/so101_bimanual.example.json`을 `configs/local/hardware.json`으로 복사하고 실제 포트·카메라 번호를 입력합니다.
3. 해당 장치의 보정 파일 4개를 `calibration/so101/`에 준비합니다. 다른 장치의 보정값을 재사용하지 않습니다.
4. 환경을 활성화하고 저장소 루트에서 아래 검사를 실행합니다. **CMD와 PowerShell 공통**이며 장치 연결은 없습니다.

```text
python scripts/check_config.py
python scripts/run_robot.py practice --validate-only
python scripts/run_robot.py record --validate-only
```

실제 실행은 [운영 안내](docs/operations.md)와 [시작 자세·종료 절차](docs/safety.md)를 따릅니다.

## 실행 모드

| 모드 | 역할 |
| --- | --- |
| `operation` | 카메라 없이 리더·팔로워 양팔 조작 |
| `practice` | 양팔 조작과 카메라 3개 표시; 손목 입력 기본 MJPG |
| `record` | 공식 LeRobot 기록; 선택적으로 같은 top 프레임의 원본·마스크 영상 동시 저장 |
| `preview` | 모터 연결 없이 카메라 표시 |
| `infer` | 기존 정책을 공식 rollout으로 실행 |

진입점은 `scripts/run_robot.py`, 구현은 `src/cuk_robotics/`입니다. `--validate-only` 없는 operation·practice·record·infer는 실제 모터를 구동합니다. 기본 기록은 로컬 전용이며 Hub 업로드는 명시적으로 요청할 때만 수행합니다.

## 문서 찾기

| 목적 | 기준 문서 |
| --- | --- |
| 실행·종료·중단 후 이어쓰기 | [운영 안내](docs/operations.md) |
| 작업대·가루·물·젓기 수집 기준과 task | [녹화 안내](docs/recording.md) |
| top 원본·마스크 동시 기록과 내보내기 | [동시 수집](docs/paired-top-recording.md) |
| 데이터 형식·배포 | [데이터 계약](docs/data-contract.md) · [Hugging Face](docs/huggingface.md) |
| 공개 데이터셋·회차 대응·고정 revision | [데이터셋 목록](docs/datasets.md) |
| 팀원용 다운로드 화면 | [가루](docs/dataset-library.html) · [물](docs/water-dataset-library.html) · [젓기](docs/stir-dataset-library.html) |
| 장치·카메라 문제 | [안전](docs/safety.md) · [문제 해결](docs/troubleshooting.md) |
| 기존 학습·추론·평가 | [학습](docs/training.md) · [추론](docs/inference.md) · [평가](docs/evaluation.md) |
| 구조·의존성·공유 범위 | [아키텍처](docs/architecture.md) · [의존성](docs/dependencies.md) · [저장소 관리](docs/repository.md) |

PC 전용 복사 명령과 과거 실험 기록은 Git 제외 `docs/local/`에 보관합니다. 새 clone에는 포함되지 않습니다.

## 구현 및 검증 범위

공개 데이터는 가루 35개씩 3종, 물 54개, 젓기 50개의 raw/masked 두 버전입니다. 젓기 두 버전은 같은 시연이므로 중복 집계하지 않습니다. 공개 이력과 검증 범위는 [데이터셋 목록](docs/datasets.md)에 모았습니다.

음성·키워드 라우팅, 가루→물→젓기 자동 전환, 완료 판정과 정량 실물 평가는 미완료입니다. 설정 검사·파일 무결성·저장 관측 추론을 실물 작업 성공률로 해석하지 않습니다.

```text
python scripts/check_config.py
python scripts/check_git_hygiene.py
python -m unittest discover -s tests -v
```

선택 의존성이 없는 환경에서는 해당 검사를 건너뜁니다. CI는 표준 라이브러리 환경 검사 후 고정된 데이터 검사 의존성을 설치해 영상 합성·내보내기·배포 제어를 검사합니다. LeRobot 통합 검사는 별도 장치 실행 환경이 필요하며, 테스트에서는 실제 장치·업로드 호출을 대체합니다. [검사 환경 구성](docs/dependencies.md).

데이터·모델·보정·로컬 설정·인증정보는 Git에서 제외합니다. 프로젝트 코드는 [MIT](LICENSE), 외부 모델·데이터·라이브러리의 사용권은 별도입니다.
