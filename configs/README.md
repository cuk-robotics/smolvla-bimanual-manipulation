# 설정 파일

- `hardware/so101_bimanual.example.json`: 공개 구조 예시. 포트·카메라 인덱스가 비어 있어 그대로는 실행되지 않습니다.
- `local/hardware.json`: 현재 PC의 실제 설정. Git 제외. 보정 경로는 프로젝트 루트 기준으로 해석합니다.
- `recording/beverage.json`: 데이터셋 ID, 작업 문장, 에피소드 수와 시간.
- `scripts/check_config.py`는 위 공개 장치 예시와 기록 설정을 검사합니다. 실제 장치를 연결하지 않습니다.

실행 안내는 [operations](../docs/operations.md), 버전은 [dependencies](../docs/dependencies.md)를 참고하세요.
실제 calibration JSON은 `calibration/so101/`에 두며 Git에 추가하지 않습니다.
