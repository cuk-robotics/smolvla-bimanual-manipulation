# 기존 정책 추론

현재 `infer`는 로컬 정책을 검사한 뒤 공식 LeRobot 동기 rollout으로 실행합니다. 가루→물→젓기 자동 연결·완료 판정은 없습니다. 학습·최종 추론의 이전 대상과 기준은 [저장소 관리](repository.md#repositories)를 따릅니다.

## 입력과 실행

실행에는 로컬 정책 폴더, 호환 데이터셋, 정확한 task가 필요합니다. 데이터셋은 실행기의 feature 검사에 사용하며 기존 행동을 재생하지 않습니다. 정책의 영상 키 매핑·state/action 순서·단위·정규화·task와 실제 입력을 확인합니다. 키 크기 일치만으로 학습 조건의 일치를 보장하지 않습니다.

**PowerShell**, 준비된 Python 환경·저장소 루트에서 실행하는 예시입니다. 설명용 두 경로는 준비한 모델과 데이터로 바꿉니다. 이 명령은 장치 연결 없는 검사입니다.

```powershell
$env:HF_HUB_OFFLINE = '1'
$env:TRANSFORMERS_OFFLINE = '1'
$policyPath = 'models/YOUR_PRETRAINED_MODEL'
$datasetRoot = 'data/lerobot/YOUR_DATASET'
$taskText = 'Pour water into the cup.'
python scripts/run_robot.py infer --policy-path $policyPath --dataset-root $datasetRoot --task $taskText --wrist-fourcc MJPG --duration-s 100 --validate-only
```

설정 검사·저장 관측 추론을 확인하고 [실물 절차](safety.md)를 준비한 뒤 아래 전체 명령을 실행합니다. 실제 양팔 구동이며 기록·업로드는 없습니다.

```powershell
python scripts/run_robot.py infer --policy-path $policyPath --dataset-root $datasetRoot --task $taskText --wrist-fourcc MJPG --duration-s 100
```

100초는 예시 상한이며 작업 완료·즉시 중단을 뜻하지 않습니다. 공식 루프는 반복 경계에서 시간을 검사하므로 처리 중인 추론이 상한을 넘을 수 있습니다. 기본 상대 목표 차이 제한과 자동 복귀 없는 구성을 유지합니다. 필요할 경우의 `--no-target-limit`은 속도 제한이 아닌 목표 차이 제한을 해제하며, `--return-to-initial-position`은 Ctrl+C 후에도 복귀를 시도합니다. 복귀는 충돌 회피·물체 반납 기능이 아닙니다.

## 장치 연결 전 워밍업

정책을 한 번 로딩한 뒤 같은 인스턴스로 검은 영상·0 상태·실행 task를 사용해 두 번 추론합니다. 행동은 버리고 매회 큐를 비웁니다. 이후 정책·전후처리 상태와 CPU/CUDA 난수 상태를 복원한 뒤 장치를 연결합니다. 워밍업 행동을 모터에 보내거나 저장하지 않습니다.

순서는 Rerun 창 → 모델 로딩 → `Inference warmup 1/2`, `2/2` → 장치 연결 → rollout입니다. 실패·종료 이벤트가 감지되면 연결 전에 중단합니다. `--validate-only`에서는 가중치 로딩·워밍업·장치 연결을 하지 않습니다.

워밍업은 초기 비용을 앞당길 뿐 이후 동기 묶음 추론의 지연을 제거하지 않습니다. Rerun 영상 전송도 첫 관측/추론/명령 후 이루어지므로 독립적인 실시간 미리보기로 해석하지 않습니다. LeRobot의 세션 내 연결 지점에 의존하므로 업그레이드 때 재검증합니다.

## 기존 모델·배치 파일의 한계

2026-10-21 기록에는 2chan 및 Taem22n 두 모델의 설정 검사·전체 가중치 로딩·저장 관측의 유한한 12차원 출력 검사가 있습니다. 실물 성공률 검증은 아닙니다. 특히 2chan의 학습 데이터·task·관절 단위/순서는 전달 정보만으로 확인되지 않았습니다. 모델별 카메라 매핑을 서로 복사하지 않습니다.

해당 모델 경로·revision·측정 로그와 PC별 복사 명령은 Git 제외 `docs/local/inference.md`, `docs/local/inference-commands.html`에 보관합니다. 새 clone에서 모델이 준비되어 있다고 가정하지 않습니다.

`scripts/windows/infer_beverage.bat`는 과거 matcha/tkpota와 powder/water를 선택하는 별도 편의 파일입니다. **현재 코드상 `--no-target-limit --return-to-initial-position`을 기본 전달**하므로 위 직접 명령과 조건이 다릅니다. 새 젓기 정책 선택기나 전체 제조 실행기가 아닙니다.
