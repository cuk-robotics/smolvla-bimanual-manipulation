> 과거 실험·계획 기록입니다. 현재 실행은 [운영 안내](../operations.md), [수집 명령](../recording.md), [추론 안내](../inference.md)를 우선합니다.

# 손목 카메라 FPS 측정 — 2026-10-20

후속 사용자 확인: 명시적 `practice --wrist-fourcc MJPG`는 정상 작동하지만 CMD의 `python scripts/run_robot.py practice`에서는 끊김이 재발했습니다. 이에 CLI에서 **practice에만 기본 MJPG**를 적용했습니다. 아래의 기본 YUY2 측정은 변경 전 상태입니다. 이제 옵션 없는 practice와 명시적 MJPG practice는 같은 손목 입력 형식을 전달하며, 명시적 YUY2는 우선 적용됩니다. record·preview·infer 기본값은 변경하지 않았습니다. 변경 후 옵션 없는 명령의 실물 재확인은 아직 수행하지 않았습니다.

기본값 수정 후 check_config·단위50개 및 practice 기본/명시적MJPG/명시적YUY2, record·operation·preview의 validate-only가 통과했습니다. 기본 practice와 명시적MJPG의 공식 카메라 설정 일치, 명시적YUY2 우선, top·record 기본 auto, hardware.json 해시 일치를 확인했습니다. 로그는 `outputs/practice_mjpg_default_20261020/`입니다.

사용자는 practice에서 로봇을 마주 보고 왼쪽 그리퍼 카메라가 더 느리다고 보고했습니다. record는 아직 시험하지 않았습니다. 물리적 좌우와 설정 이름의 대응은 미확정이므로 아래 결과는 현재 장치 인덱스로 구분합니다.

## 측정 결과

현재 설정은 `left_wrist=0`, `right_wrist=1`, `top=4`입니다. 손목 2대는 USB Camera, top은 OBS Virtual Camera로 조회됐습니다. 모두 640×480·목표 30 FPS·DSHOW이며, 기본 손목 입력 형식은 이번 연결에서 YUY2였습니다.

| 조건 | 측정 시간 | 0번 / left_wrist | 1번 / right_wrist | top |
| --- | ---: | ---: | ---: | ---: |
| 손목 2대, 기본 YUY2 | 30초 | 30.00 FPS | 7.03 FPS | 미연결 |
| 손목 2대, MJPG | 30초 | 30.00 FPS | 30.00 FPS | 미연결 |
| 손목 MJPG + top NV12 | 60초 | 30.00 FPS | 30.00 FPS | 수신 30.00 FPS |
| 손목 YUY2, 1번→0번 역순 연결 | 30초 | 30.00 FPS | 7.87 FPS | 미연결 |

- YUY2에서 1번의 최대 프레임 수신 간격은 첫 검사 272.3ms, 역순 검사 336.1ms였습니다. 0번은 두 검사 모두 최대 48.4ms 미만이었습니다.
- MJPG 손목은 30초·60초 검사 모두 각 10초 구간에서 30.0 FPS였고, 연속 동일 프레임 및 66.7ms 초과 간격은 0회였습니다. 두 검사를 합친 최대 간격은 48.9ms였습니다.
- 60초 검사에서 OBS top은 1,800프레임을 수신했지만 연속 동일 영상이 276쌍이었습니다. 최초 프레임을 포함한 영상 변경률은 25.4회/초입니다. 이는 휴대폰 센서 FPS의 직접 측정이 아니며 손목 결과와 구분합니다.
- 모든 검사에서 `read_latest()` 오류 0회, 검사 후 연결 해제, 하드웨어 설정 파일 바이트 일치를 확인했습니다.
- 읽기 전용 DirectShow 조회에서 손목 두 대 모두 자동 노출 상태, 값 -6을 보고했습니다. 자동 상태의 이 값을 실제 고정 노출 시간으로 해석하지 않습니다. 노출·게인은 변경하지 않았습니다.

## 해석과 적용

이번 조건에서는 1번 장치의 낮은 수신률이 YUY2에서 재현되고 MJPG에서 해소됐습니다. 연결 순서만으로 설명되지는 않습니다. USB 경로·케이블·드라이버 중 세부 원인은 확정하지 않았습니다. 사용자가 말한 물리적 왼팔이 1번인지도 영상 대조가 필요합니다.

practice에서 아래 기존 옵션을 사용할 수 있습니다. 이는 실제 모터를 구동하는 명령으로, 이번 점검에서는 `--validate-only`를 붙인 설정 검사만 실행했습니다. 실물 실행은 [안전 절차](../safety.md)에 따라 리더·팔로워 시작 자세와 고정 상태를 확인한 뒤 수행합니다.

**PowerShell**:

```powershell
& 'C:\miniforge3\envs\cuk-robotics\python.exe' 'E:\Desktop\smolvla-bimanual-manipulation\scripts\run_robot.py' practice --wrist-fourcc MJPG
```

카메라 전용 시험은 모터 통신·Rerun 렌더링·데이터 저장 부하를 포함하지 않습니다. 이 시험만으로 실제 practice 화면 개선 및 장시간 record 안정성을 입증한 것은 아닙니다. 이후 사용자가 명시적 MJPG practice 정상 작동을 확인했습니다. 카메라 측정 당시에는 로봇 소스도 변경하지 않았으며, 후속 수정은 문서 상단에 기록한 practice 기본 입력 형식입니다. 장치 설정·보정·기존 데이터는 계속 보존합니다.

## 측정 방법과 근거

설치된 LeRobot `OpenCVCamera`로 연결하고, 해당 인스턴스의 영상 후처리 직후 `perf_counter()` 시각을 수집했습니다. 연결 및 추가 2초 준비 후 공통 측정 구간 안의 프레임 수를 시간으로 나눴습니다. 드라이버의 FPS 보고값과 실제 수신률을 구분합니다. SHA-256으로 연속 영상의 완전 동일 여부를 비교했으며 해시 계산 오버헤드 p95는 각 검사·카메라 모두 0.54ms 미만입니다. 영상이 달라도 움직임의 선명도나 지연이 정상이라는 뜻은 아닙니다.

Git 제외 로컬 근거는 `outputs/camera_fps_20261020/`의 `measure.py`, `pair_default.json`, `pair_mjpg.json`, `triple_mjpg.json`, `pair_yuy2_reverse.json`, `controls.json`, 조건별 PNG입니다. 기존 출력 파일을 덮어쓰지 않았습니다.

장치 없는 검증은 `scripts/check_config.py`, 단위검사 50개, `practice --wrist-fourcc MJPG --validate-only`가 통과했습니다. 단위검사는 기존 프로젝트 동작 검사이며 카메라 FPS의 근거는 위 실측 JSON입니다. 검사 로그는 같은 출력 폴더의 `unit_tests.log`, `practice_validate.log`입니다.

프로젝트 담당자 관점의 후속 질문:

1. 1번 장치의 영상은 마주 보고 왼쪽 그리퍼와 일치하는가?
2. MJPG를 적용한 실제 practice에서도 움직임이 부드럽게 표시되는가?
3. 장시간 record에서도 손목의 수신률과 저장 영상 품질이 유지되는가?
