# 아키텍처 및 모듈 경계

## 현재 실행 경로

```text
scripts/run_robot.py 또는 Windows 배치 파일
  → cuk_robotics.teleoperation.cli
  → configs/local/hardware.json + configs/recording/beverage.json
  → operation: 공식 teleoperate → 리더 2대·팔로워 2대, 카메라·표시 없음
  → practice: 공식 teleoperate → 양팔 장치 + 카메라 3개 + Rerun
  → record: 공식 record → 양팔 + 카메라 3개 + Rerun + data/lerobot/<repo_id>/<실행시각>/
  → infer: 공식 rollout(base/sync) → 로컬 정책 + 팔로워 2대 + 카메라 3개 + Rerun
```

`config.py`는 장치 설정과 보정 파일 위치를 확인합니다.
프로젝트 실행기는 공식 CLI 설정과 화면 배치를 구성하고 로컬 Rerun 뷰어 포트를 준비합니다.
`teleoperation.rerun_display`는 기본 포트가 차단되면 사용 가능한 포트를 선택하고 공개 SDK로 뷰어를 시작합니다.
공식 LeRobot은 `display_ip`/`display_port`로 해당 뷰어에 연결합니다.
`rerun_display.install_display_logging()`은 공식 시각화 디스패처의 Rerun 콜백만 교체하여 비압축 전송과 표시 갱신 제한을 적용합니다.
기본 표시는 최대 30회/초이며 모터 루프·데이터셋 기록 주기는 바꾸지 않습니다.
모터 연결·명령·데이터 기록은 설치된 LeRobot이 담당합니다.
`cameras.preview`는 로봇 연결 없는 브라우저 미리보기입니다.
`operation`은 카메라 검증·표시 설정·뷰어 시작을 건너뛰고 기존 포트·보정·목표 차이 제한을 사용합니다.
2026-10-14 오른쪽 그리퍼 부품 교체 후에는 로컬 보정 파일의 `drive_mode`만 반전했으며 공식 LeRobot 변환을 사용합니다.
`teleoperation.inference`는 로컬 정책·원본 데이터셋의 feature 이름·순서·차원·영상 매핑을 검사한 뒤 공식 rollout에 위임합니다.
`scripts/windows/train_powder.bat`는 로컬 학습 설정을 읽어 공식 trainer를 실행합니다. 설치 패키지 소스를 복사하거나 수정하지 않습니다.

## 개발 예정

음성 → ASR → 검토한 작업 텍스트, 영상 3개, 양팔 상태 → SmolVLA → 양팔 행동이라는 구성을 목표로 합니다.
ASR, 자동 단계 전환·완료 판정, 충돌 감지·헛파지 판정, 정량 실물 평가 자동화는 아직 구현하지 않았습니다.
정책 feature 매핑 검사와 기존 데이터 표본·수치 검사는 준비됐지만 모든 시연의 성공 인증이나 실물 정책 성공률 검증을 뜻하지 않습니다.
관련 패키지는 실제 코드를 추가할 때 생성합니다. 카메라 프레임 간 정확한 시간 동기화도 아직 측정하지 않았습니다.

참고: [LeRobot](https://github.com/huggingface/lerobot), [SmolVLA](https://huggingface.co/docs/lerobot/smolvla).
