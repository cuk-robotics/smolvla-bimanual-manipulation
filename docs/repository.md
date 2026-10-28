# 저장소 구조와 공유 기준

현재 실행 경로를 기준으로 관리합니다. 로봇 제어 구현은 `src/`, 진입점은 `scripts/`, 안내는 `docs/`에 둡니다.
실행되지 않는 계획용 패키지나 빈 자료 폴더를 미리 만들지 않습니다.

## 디렉터리

```text
README.md                       # 프로젝트 개요·문서 진입점
src/cuk_robotics/                # 설정 로더·카메라·공식 LeRobot 실행기
scripts/                        # Python 진입점·검사
  windows/                      # 기존 Windows 실행 편의 파일
configs/
  hardware/                     # 포트·카메라 번호가 비어 있는 공개 예시
  recording/                    # 기록 기본 작업 문장·에피소드 설정
  local/                        # 실제 PC 설정, Git 제외
docs/                           # 현재 운영·수집·추론·환경·데이터 문서
  archive/                      # 과거 명령·특정 세션·연구 검토 기록
tests/                          # 장치 연결 없는 검사
requirements/                   # 주요 의존성 버전 제약
templates/                      # 데이터 카드 양식
.github/workflows/              # 오프라인 CI
```

로컬 `calibration/`, `data/`, `models/`, `outputs/`는 원래 경로에 유지합니다.
LeRobot 데이터셋의 data/meta/videos 내부 구조와 모델·보정 경로는 정리 목적으로 변경하지 않습니다.

## 공개와 로컬 보관

| 구분 | 대상 |
| --- | --- |
| 공개 | 소스, 실행·검사 스크립트, 테스트, CI, 의존성, 설정 예시, 기록 설정, 문서·HTML, 데이터 카드 양식 |
| 로컬 | configs/local, calibration, data·datasets·recordings, models·checkpoints·runs, outputs·logs·캐시·가상환경 |
| 로컬 | .env·인증정보·개인 키, AGENTS.md·PROJECT_CONTEXT.md, AI 도구 로컬 상태, 루트 다운로드 압축파일 |

공개 Hub 계정명·repo ID는 인증 토큰과 구분합니다. 문서에 사용한 PC 경로·COM 번호는 예시 또는 당시 조건이며 다른 PC에서 그대로 적용하지 않습니다.
`.env.example`은 비밀 값이 없는 예시만 허용합니다. 일반 JSON·Markdown·이미지라는 이유만으로 일괄 제외하지 않습니다.
AGENTS.md의 제외는 이 프로젝트의 로컬 협업 기록 분리 방침입니다.

`.gitignore`는 이미 추적한 파일이나 과거 커밋을 제거하지 않습니다. 다음 명령을 프로젝트 루트에서 실행합니다.

```text
git status --short
git ls-files -ci --exclude-standard
git diff --check
python scripts/check_git_hygiene.py
```

공유 검사는 현재 추적·미추적 공개 후보의 일반적인 인증정보 패턴·대용량 파일·문서 링크를 검사합니다.
과거 커밋 전체나 모든 비밀정보 유형의 부재를 보증하는 검사는 아닙니다.

## 2026-10-28 정리

- README의 과거 일지를 걷어내고 현재 목적·실행 모드·문서 진입점을 정리했습니다.
- 루트 RUN_GUIDE와 운영 문서의 중복 실행 설명은 operations로 통합하고 장애 점검은 troubleshooting으로 분리했습니다.
- 최신 수집·작업환경·추론·학습 안내는 날짜 없는 고정 문서명으로 모았습니다.
- 이전 모델·단계별 50개 계획·특정 이어쓰기 세션·연구 검토는 archive로 옮겼습니다.
- repository-layout·change-history·git-hygiene의 중복 구조·공유 안내는 이 문서로 통합했습니다.
- 실제 실행에 쓰이지 않는 configs/project.example.json과 이를 위한 옛 검사를 제거하고, check_config는 실제 공개 장치 예시·기록 설정 검사로 교체했습니다.
- 이미지가 없던 assets의 자리표시 README를 정리했습니다. 실제 공개 이미지가 생길 때 다시 추가할 수 있습니다.
- 모터 제어·장치 설정·보정·데이터·모델·배치 진입점과 기존 사용자 변경은 보존했습니다.

정리 전 공개 파일 전체와 로컬 인수인계는 Git 제외 `outputs/repository_cleanup_20261028/before/`에 바이트 그대로 백업했습니다.
파일별 SHA-256·이동 목록·보호 파일 검증·검사 로그는 같은 상위 폴더에 보관합니다.
과거 build/dist·빈 패키지 정리의 상세 기록도 이 백업의 이전 change-history에서 확인할 수 있습니다.
커밋·push는 변경 내용을 사용자에게 보여드린 후 진행합니다.

## 과거 기록

아래 문서는 당시 조건과 실험 근거입니다. 현재 실행 안내로 자동 적용하지 않습니다.

- [2026-10-07 추론·실물 관찰](archive/inference-20261007.md)
- [2026-10-08 모델 선택](archive/inference-models-20261008.md): 기존 infer_beverage.bat의 w6·tkpota 선택에 대응
- [과거 단계별 50개 수집](archive/subtask-recording-20261006.md)
- [특정 녹차 세션 이어쓰기](archive/resume-greentea-20261019.md)
- [카메라 FPS 실측](archive/camera-fps-20261020.md)
- [Matcha Bot 비교](archive/matcha-bot-comparison.md)
- [가루 데이터 개선 검토](archive/powder-data-improvement.md)
- [장기 작업 정책 검토](archive/long-horizon-strategy.md)

현재 작업은 [운영](operations.md)·[수집](recording.md)·[추론](inference.md)을 따릅니다.
