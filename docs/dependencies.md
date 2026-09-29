# 외부 의존성 및 재현성

기본 프로젝트는 Python 3.12 이상과 표준 라이브러리만 사용합니다.
선택 의존성 `robotics = ["lerobot[smolvla]"]`는 설치 연결점이며 통합 검증 완료 표시가 아닙니다.
2026-09-29 확인한 upstream `main`의 Python 요구 조건은 `>=3.12`입니다.

통합 환경을 마련할 때 다음 순서로 진행합니다.
1. [LeRobot 설치 안내](https://huggingface.co/docs/lerobot/installation)와 대상 release의 요구 조건 확인.
2. 별도 환경에서 OS, Python, GPU 드라이버, PyTorch/CUDA 조합 결정.
3. `python -m pip install -e ".[robotics]"`로 선택 의존성 설치. 대용량 의존성이 포함될 수 있음.
4. 선택한 버전의 데이터 수집·하드웨어·학습 추가 의존성 확인. `smolvla` extra만으로 모든 하드웨어 기능이 설치된다고 가정하지 않음.
5. 입출력 매핑, 기본 모델 revision, 전처리와 장치 인터페이스 검증.
6. 검증한 LeRobot 버전을 정확히 고정하고 OS별 잠금 파일·환경 정보를 기록.

현재 잠금 파일과 검증된 GPU/장치 조합은 없습니다. 기본 모델은 별도로 획득하며 자동 다운로드 코드는 없습니다.
upstream 소스를 vendoring하거나 이 저장소로 복사하지 않습니다.

근거: [upstream pyproject.toml](https://github.com/huggingface/lerobot/blob/main/pyproject.toml),
[SmolVLA 안내](https://huggingface.co/docs/lerobot/smolvla).
