# 실행 파일

구현은 `src/cuk_robotics/`에 두고 이 폴더의 Python 파일은 진입점만 담당합니다.

| 파일 | 역할 |
| --- | --- |
| run_robot.py | 공식 양팔 operation(무카메라)·연습·기록·정책 추론; 카메라 모드 3영상, 선택적 paired 기록 4영상 표시 |
| preview_cameras.py | 카메라 전용 브라우저 미리보기 |
| check_config.py | 실제 공개 장치 예시·기록 설정의 장치 연결 없는 검사 |
| check_git_hygiene.py | Git 제외 규칙·추적 상태·공개 파일의 인증정보 패턴·문서 링크 검사 |
| export_top_variant.py | 종료된 4영상 수집본에서 raw 또는 masked 3영상 사본 생성·검사 |
| publish_top_variants.py | 두 3영상 사본 검사·준비 또는 명시적으로 요청한 Hub 업로드 |
| windows/practice.bat | 현재 Windows 환경의 연습 실행 |
| windows/operation.bat | 카메라·Rerun 없이 리더 2대·팔로워 2대 조작 |
| windows/record.bat | 현재 Windows 환경의 기록 실행 |
| windows/preview_cameras.bat | 현재 Windows 환경의 카메라 미리보기 |
| windows/train_powder.bat | 현재 PC의 로컬 가루 warm-start 설정으로 공식 LeRobot 학습 실행 |
| windows/infer_beverage.bat | 2026-10-08 전달받은 matcha/tkpota 모델과 가루/물 작업을 선택해 기존 infer 실행 |

프로젝트 루트에서 실행합니다. 자세한 방법은 [실행 안내](../docs/operations.md)에 정리했습니다.

가루 학습 설정·저장 위치는 [로컬 학습 안내](../docs/training.md)를 참고합니다. 설정 파일과 모델·데이터는 Git 제외 로컬 파일이므로 새 PC에서 별도 준비가 필요합니다.

기존 배치 파일과 직접 실행의 조건 차이는 [추론 안내](../docs/inference.md)를 참고합니다. PC별 모델 명령·과거 진단은 Git 제외 `docs/local/`에 보관합니다.
