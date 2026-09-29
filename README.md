# SmolVLA Bimanual Beverage Manipulation

2× SO-101 로봇팔과 3개 카메라를 활용하는 **2026 캡스톤 양팔 음료 조작 프로젝트**입니다.
음성인식으로 변환한 텍스트, 카메라 영상, 양팔 상태를 SmolVLA에 입력하는 시스템을 개발합니다.

> **현재 상태: 초기 프로젝트 골격.** 로봇 제어, 카메라 수집, 음성인식, 원격조작,
> 데이터셋 기록, 학습 및 실물 평가는 아직 구현하지 않았습니다. 아래 태스크와 연계는 개발 계획이며 성능 실적이 아닙니다.

## 프로젝트 개요

- **배경:** 음료 용기를 다루는 작업에는 시각 정보, 언어 지시, 양팔 협응이 필요합니다.
- **개발 과제:** 카메라 3대의 시간 정렬, 좌·우 로봇 상태/행동 정의, 개선형 그리퍼 검증,
  양팔 시연 데이터 수집 및 정책 적응을 단계적으로 수행합니다.
- **목표:** 언어 지시에 따른 음료 용기 이동과 양팔 협동 조작의 재현 가능한 실험 체계를 구축합니다.
- **설계 원칙:** LeRobot/SmolVLA 원본 코드를 복사하지 않고, 외부 의존성과 프로젝트별 어댑터로 연결합니다.

## 하드웨어

| 구성 | 수량 | 역할 및 확인 사항 |
| --- | ---: | --- |
| SO-101 로봇팔 | 2 | 좌·우 작업용 팔. 포트, 장착 위치, 캘리브레이션 확인 필요 |
| 개선형 그리퍼 | 2 | 용기 파지. 형상, 구동 방식, 개구 폭, 마찰·하중 시험 예정 |
| Wrist/gripper camera | 2 | 각 팔의 손목 또는 그리퍼 근접 시야. 장착 위치 확정 필요 |
| Top-view camera | 1 | 작업 공간 전체 시야. 내부·외부 파라미터 보정 예정 |

마이크, 연산 장치/GPU, 원격조작 입력 장치의 사양은 미정입니다.
작업용 로봇팔 2대에 원격조작용 leader arm이 추가로 포함된 것으로 가정하지 않습니다.

## 멀티모달 입력

```text
음성 → 별도 ASR → 작업 지시 텍스트 ─────────────┐
좌 wrist/gripper + 우 wrist/gripper + top RGB ─┼→ 입력 어댑터 → SmolVLA
좌·우 관절 및 그리퍼 상태 ─────────────────────┘                 ↓
                                                  양팔 행동 → 제어 어댑터 (구현 예정)
```

| 입력 | 프로젝트 내부 이름 | 규격 |
| --- | --- | --- |
| 음성인식 텍스트 | `instruction.text` | ASR 결과를 검토·정규화한 작업 지시. 원시 음성은 정책에 직접 입력하지 않음 |
| 좌 근접 영상 | `observation.images.left_wrist` | RGB, 해상도·FPS·시간 허용 오차 미정 |
| 우 근접 영상 | `observation.images.right_wrist` | RGB, 해상도·FPS·시간 허용 오차 미정 |
| 상부 영상 | `observation.images.top` | RGB, 해상도·FPS·시간 허용 오차 미정 |
| 양팔 상태 | `observation.state` | 좌→우 순서의 관절/그리퍼 상태. 차원·단위·정규화는 실측 후 확정 |

이름은 프로젝트 내부 계약이며 upstream API와 동일함을 보장하지 않습니다.
SmolVLA는 다중 영상·로봇 상태·언어 지시를 받는 모델입니다.
본 장치의 양팔 동작은 별도 데이터와 입출력 매핑, 적응 및 검증이 필요합니다.
공식 설명: [SmolVLA](https://huggingface.co/docs/lerobot/smolvla).

## 태스크 (개발 후보)

1. **기초:** 빈 컵/용기 집기, 목표 위치에 놓기.
2. **양팔 협동:** 한 팔로 용기를 지지하고 다른 팔로 접근·조작하기, 양팔 간 용기 전달.
3. **확장:** 실물 시험을 통과한 용기와 액체 조건에서 따르기 및 정리하기.

최종 태스크·성공 기준은 미정입니다. 우선 빈 용기로 검증하고,
액체 태스크는 전자부품 보호, 충돌·낙하 대응, 정지 수단 검증 후 진행합니다.
성공률, 완료 시간, 유출/낙하, 사람 개입 횟수, 명령 이해 실패를 기록할 계획입니다.

## 기술스택

| 영역 | 선택 / 계획 |
| --- | --- |
| 프로젝트 언어 | Python 3.12 이상, `src` 패키지 구조 |
| 로봇·데이터 파이프라인 | 외부 [LeRobot](https://github.com/huggingface/lerobot) 의존성 + 프로젝트 어댑터 |
| 정책 | LeRobot의 SmolVLA 구현, [기본 모델](https://huggingface.co/lerobot/smolvla_base) 활용 예정 |
| 학습 | PyTorch 기반 upstream 학습 기능 활용 예정. CUDA/OS 조합 미검증 |
| 영상 | LeRobot 카메라 계층 연결 예정. 장치 백엔드 미정 |
| 음성인식 | ASR 엔진 미정. 음성→텍스트와 정책 입력을 분리 |
| 설정 / 기본 검사 | JSON / Python 표준 라이브러리 `unittest` |

`pyproject.toml`의 `robotics` 선택 의존성은 `lerobot[smolvla]`를 참조합니다.
기본 설치는 로봇·학습 패키지를 내려받지 않습니다. 통합 버전은 아직 고정하지 않았으며,
호환성 확인 후 정확한 버전과 환경 잠금 파일을 기록합니다. 자세한 절차는 [의존성 문서](docs/dependencies.md)를 참고하세요.

## 저장소 구조

```text
.
├── README.md
├── LICENSE
├── .gitignore
├── pyproject.toml
├── configs/                     # 장치·입력·실험 설정 예시
├── src/cuk_robotics/
│   ├── robot/                   # 양팔·그리퍼 제어 어댑터 예정
│   ├── cameras/                 # 세 카메라 및 동기화 계층 예정
│   ├── teleoperation/           # 양팔 시연 수집 인터페이스 예정
│   ├── speech/                  # ASR 및 지시 텍스트 처리 예정
│   ├── dataset/                 # LeRobotDataset 변환·검증 예정
│   ├── policies/                # SmolVLA 입력/출력 적응 예정
│   └── evaluation/              # 실험 지표·평가 예정
├── scripts/                     # 하드웨어 없이 설정 점검
├── hardware/gripper/            # 그리퍼 설계·BOM·시험 기록 예정
├── docs/                        # 아키텍처·데이터 계약·개발 계획
├── assets/                      # 검토된 그림·사진
└── tests/                       # 오프라인 설정 점검 테스트
```

## 시작하기 (오프라인 골격 점검)

Python 3.12 이상 환경에서 저장소 루트 기준으로 실행합니다.

```bash
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -e .
python scripts/check_config.py
python -m unittest discover -s tests -v
```

패키지 설치에는 빌드 도구 다운로드가 필요할 수 있습니다. 설정 검사와 테스트는
패키지 설치 없이 표준 라이브러리만으로도 실행할 수 있습니다.
예시 설정은 `mode=dry_run`, `hardware_enabled=false`입니다.
검사 스크립트는 파일만 읽으며, 모터·카메라·마이크에 연결하거나 모델을 내려받지 않습니다.
이 검사는 **실물 로봇의 안전성 인증이나 런타임 안전 제어가 아닙니다.**

## Hugging Face 연계 예정

- **Datasets:** 시연을 LeRobotDataset 형식으로 구성하고, 동의·개인정보·사용권 검토 후 Hub 게시 여부를 결정합니다.
- **Models:** SmolVLA 적응 모델과 모델 카드에 학습 데이터, 체크포인트 revision, 환경 및 한계를 기록합니다.
- **Spaces:** 검토된 데모와 평가 결과를 게시하는 공간을 고려합니다.
- Hugging Face 조직/계정 및 저장소 ID는 **미정**입니다. GitHub 조직명과 동일한 Hub 조직의 존재를 가정하지 않습니다.
- 자동 업로드는 비활성화되어 있습니다. 데이터·모델 파일·토큰은 Git에 커밋하지 않습니다.

## 개발 순서 및 문서

1. 하드웨어·그리퍼 사양, 원격조작 방식, 태스크와 평가 기준 확정.
2. 포트/장치 ID 확인, 보정, 정지·충돌 대응 시험.
3. 세 카메라와 양팔 상태/행동의 시간 정렬 및 데이터 계약 확정.
4. 양팔 시연 수집과 데이터 품질 검토.
5. SmolVLA 적응, 오프라인 평가, 제한된 조건의 실물 평가.

- [아키텍처](docs/architecture.md) · [데이터 계약](docs/data-contract.md)
- [안전 및 실험 준비](docs/safety.md) · [평가 계획](docs/evaluation.md)
- [그리퍼 개발 기록](hardware/gripper/README.md)

## 라이선스와 출처

이 저장소의 신규 프로젝트 코드는 [MIT License](LICENSE)를 적용합니다.
외부 라이브러리, 모델 가중치, 데이터, 외부 CAD에는 각자의 라이선스가 적용됩니다.
LeRobot/SmolVLA 구현 코드는 이 저장소에 포함하지 않았습니다.

- [LeRobot 공식 저장소](https://github.com/huggingface/lerobot)
- [SO-101 공식 가이드](https://huggingface.co/docs/lerobot/so101)
- [SmolVLA 공식 문서](https://huggingface.co/docs/lerobot/smolvla)
- [SmolVLA 모델 카드](https://huggingface.co/lerobot/smolvla_base)

공식 문서 확인일: 2026-09-29. 프로젝트 장치에 대한 통합·성능 검증은 아직 수행하지 않았습니다.
