# 환경 및 의존성

## 현재 확인한 환경

2026-09-30 로컬 `cuk-robotics` 환경의 설치 정보를 확인했습니다.

| 패키지 | 버전 |
| --- | --- |
| Python | 3.12.14 |
| LeRobot | 0.6.1 |
| PyTorch | 2.11.0+cu128 |
| rerun-sdk | 0.33.1 |
| draccus | 0.11.6 |
| PyYAML | 6.0.3 |

이 목록은 설치 정보이며 Windows GPU 학습이 검증됐다는 의미가 아닙니다.
`requirements/constraints-windows.txt`는 주요 버전 제약으로, 전체 환경 잠금 파일이 아닙니다.

## 설치 구분

기본 패키지와 오프라인 검사는 장치 의존성을 요구하지 않습니다.

```bat
python -m pip install -e .
python scripts/check_config.py
python -m unittest discover -s tests -v
```

영상 합성과 LeRobot v3 데이터 내보내기 검사는 NumPy·Pillow·PyArrow를 사용합니다. 장치 연결 없이 이 검사도 실행하려면 별도 검사 환경에 다음 고정 의존성을 설치합니다. CI의 Ubuntu/Windows·Python 3.12도 같은 파일을 사용합니다.

```text
python -m pip install --only-binary=:all: -r requirements/test-data.txt
python -m unittest discover -s tests -v
```

CI는 설치 전에 `python -S -m unittest discover -s tests -v`로 선택 의존성이 없는 경로도 확인합니다. 데이터 검사 환경에는 LeRobot을 설치하지 않으므로 공식 CLI 통합 검사는 건너뜁니다. 전체 LeRobot 환경에서는 해당 검사도 실행하며 모터·카메라·Hub 호출은 테스트에서 대체합니다. 이 검사는 실제 장치 구동 검증과 구분합니다.

새 장치 실행 환경에서는 아래 선택 의존성을 설치합니다. 현재 정상 환경에 다시 설치할 필요는 없습니다.

```bat
python -m pip install -e ".[robotics]" -c requirements/constraints-windows.txt
```

`robotics`는 LeRobot의 `core_scripts,feetech`, Rerun, YAML을 포함합니다.
학습 의존성은 `training`으로 분리했으며 SmolVLA 학습 전 PyTorch/CUDA/OS 호환성을 별도로 확인합니다.
현재 Rerun 화면 구성은 LeRobot 0.6.1의 비공개 `_build_blueprint`에 의존합니다. 업그레이드하면 `--validate-only`와 영상 표시를 다시 확인해야 합니다.
upstream 설치 파일을 수정하거나 LeRobot 소스를 프로젝트로 복사하지 않습니다.

설치 근거: [LeRobot 설치 문서](https://huggingface.co/docs/lerobot/installation).
