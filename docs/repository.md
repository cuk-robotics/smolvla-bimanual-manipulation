# 저장소 관리와 공유 범위

<a id="repositories"></a>
## 저장소 역할

| 저장소 | 담당 범위 |
| --- | --- |
| smolvla-bimanual-manipulation | 원격조작·연습·기록·수집 장치 설정과 품질 확인 |
| [beverage-autonomy](https://github.com/cuk-robotics/beverage-autonomy) | 학습·평가·최종 추론의 통합 대상 |
| 조직 `.github` | 조직 소개와 공통 GitHub 구성 |

2026-10-28 저장소 분리 기록 이후 이 저장소의 기존 학습 배치·추론 실행기는 유지되어 있습니다. 새 저장소로 실행 코드 이전과 실물 검증이 완료되었다고 간주하지 않습니다.

이전할 때는 출처 commit·로컬 변경·해시, 의존성, 정책/데이터 feature·정규화·task, Hub의 고정 revision을 기록합니다. 원본·파생본의 중복 시연과 평가 누수를 확인하고 장치 없는 검사→저장 관측 추론→승인된 실물 평가 순서로 검증합니다. 이전 완료 후 기능별 관리 저장소를 하나로 정합니다.

## 기존 공개 이력

| 커밋 | 작업 범위 |
| --- | --- |
| `a0203f2` | 초기 오프라인 골격·설정 예시·기본 검사 |
| `57af065` | 원격 저장소의 README 초기화 |
| `109d058` | 수집 환경 통합 기준점: 장치 설정, 조작·카메라, 시연 기록, 기존 추론·워밍업, 학습 보조, 공유·CI·문서 |
| `0b3b924` | 두 초기 이력을 연결한 병합; 파일 구성은 `109d058`과 동일 |

`109d058`은 여러 기능을 한 번에 도입한 통합 커밋입니다. 이후 변경은 독립적인 기능과 관련 테스트, CI, 문서 정리를 목적별 커밋으로 관리합니다. 코드 도입과 실물 성능 검증은 구분합니다.

## 폴더와 문서 역할

| 경로 | 역할 |
| --- | --- |
| `src/cuk_robotics/` | 공식 LeRobot 위임·장치 구성·표시·내보내기 구현 |
| `scripts/`, `tests/` | 실행 진입점과 장치 연결 없는 검사 |
| `configs/hardware/`, `configs/recording/` | 공유 가능한 예시와 기록 기본값 |
| `docs/operations.md` | 실행·종료·resume |
| `docs/recording.md` | 작업대·task·수집 및 채택 기준 |
| `docs/paired-top-recording.md` | 선택적 4영상 기록·3영상 변환 |
| `docs/data-contract.md`, `docs/huggingface.md` | 데이터 규격과 배포 절차 |
| `docs/datasets.md` | 공개 데이터 ID·회차 대응·revision·검증 범위 |
| `docs/*dataset-library.html` | 팀원용 데이터셋 조회·다운로드 화면 |
| `docs/local/` | **Git 제외** PC별 명령·과거 실험/날짜별 작업 기록 |

전체 문서 입구는 [README](../README.md)입니다. 공통 절차를 날짜별 문서에 복제하지 않고, 과거 실행 기록은 현재 기준과 분리합니다. 내부용 문서에서만 로컬 파일 경로를 연결합니다.

## Git 포함·제외 기준

공유 대상은 소스·테스트·의존성·공개 설정 예시·재현 가능한 운영 문서·검토한 다운로드 HTML입니다. Hugging Face 공개 ID와 revision은 재현성 정보이므로 포함합니다.

Git 제외 대상은 `configs/local/`, 보정, 데이터·영상, 모델·학습 출력, 로그·검증 증거, 인증정보, AI 작업 이력, `docs/local/`, `*.local.md`입니다. 이 PC의 사용자명·절대 경로·미완료 실행 메모는 로컬 문서에서 관리합니다. 마스크 PNG와 데이터 카드를 포함한 공개 배포 파일은 별도 검토하며 데이터셋 전체를 Git에 넣지 않습니다.

```text
git status --short
git diff --check
python scripts/check_git_hygiene.py
git ls-files -ci --exclude-standard
```

`.gitignore`는 이미 추적 중인 파일을 자동 제외하지 않습니다. 제외 대상이 이미 추적되어 있으면 원본을 백업·로컬 위치로 옮기고 삭제 변경을 검토해야 합니다. 인증정보가 과거 commit에 있다면 ignore만으로 제거되지 않으며 폐기·교체와 별도 이력 처리가 필요합니다.

검사 스크립트는 현재 추적·미추적 공개 후보의 일반 인증정보 패턴, 로컬 문서 링크, 큰 파일, ignore 분류와 추적 중인 제외 파일을 점검합니다. 과거 Git 이력 전체나 모든 비밀 형식을 검사하는 도구는 아닙니다.

## 로컬 보관과 복구

2026-10-31 정리 전 원문·변경분·해시 목록은 Git 제외 `outputs/docs_cleanup_20261031/`에 보관합니다. 날짜별 원문과 기존 archive는 `docs/local/history/`, `docs/local/archive/`에, PC 전용 추론 HTML은 `docs/local/inference-commands.html`에 남깁니다. 삭제 표시된 공개 문서는 이 로컬 사본과 백업으로 복구할 수 있습니다. 새 clone에는 로컬 보관물이 포함되지 않습니다.
