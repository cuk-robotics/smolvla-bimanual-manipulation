# 학습 준비와 기존 로컬 실행기

학습·평가의 통합 대상은 [beverage-autonomy](https://github.com/cuk-robotics/beverage-autonomy)입니다. 이전 전까지 기존 `scripts/windows/train_powder.bat`를 유지합니다. 이 파일의 존재나 짧은 학습 검사가 새 가루·물·젓기 모델의 학습 완료를 뜻하지 않습니다.

## 학습 전 확인

- [데이터셋 목록](datasets.md)의 정확한 ID·revision과 [데이터 계약](data-contract.md)을 사용합니다. 원본/통합본, raw/masked의 중복을 제거하고 에피소드 단위로 분할합니다.
- 모델의 state/action 순서·단위·정규화, 영상 키/해상도·task를 실제 메타데이터와 대조합니다. 다른 모델의 카메라 매핑을 그대로 복사하지 않습니다.
- 학습 설정·기반 모델·데이터 revision·시드·분할·라이브러리 버전·출력 경로를 기록합니다. 수치 손실과 [실물 평가](evaluation.md)를 구분합니다.

## 기존 배치 파일

**CMD**, 준비된 현재 PC 환경의 저장소 루트에서 실행:

```bat
scripts\windows\train_powder.bat
```

설치된 공식 `lerobot.scripts.lerobot_train`과 Git 제외 `configs/local/powder_train_5070ti/train_config.json`을 사용합니다. 모델·데이터·토크나이저도 별도 로컬 파일입니다. 새 clone에는 실행에 필요한 자산이 포함되지 않습니다. 자동 Hub 업로드·WandB는 비활성화한 기존 로컬 구성입니다.

이 실행기는 기존 가루 데이터와 전달받은 체크포인트에서 새 warm-start 실험을 시작합니다. optimizer/scheduler 상태까지 이어지는 resume와 다릅니다. 다른 작업 성능 보존을 보장하지 않습니다. 실제 재개에는 해당 실행의 설정과 training state가 필요합니다. 진행 중 설정 파일 수정은 이미 로드된 객체에 반영되지 않습니다.

2026-10-07의 GPU·배치·학습률·분할·처리량 측정은 Git 제외 `docs/local/training.md`에 보관합니다. 당시 2회/8회 업데이트 검사는 유한한 loss/gradient와 실행 경로를 확인한 것으로 장기 수렴·새 데이터 학습·실물 성공률의 근거가 아닙니다.
