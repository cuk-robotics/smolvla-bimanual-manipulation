# top 원본·마스크 동시 수집

가상 카메라에서 읽은 한 RGB 프레임으로 원본과 PNG 합성본을 만들어 공식 LeRobot 기록기에 함께 전달합니다. 실제 카메라는 3개이며 수집 feature는 4개입니다.

| 수집 feature | 내용 |
| --- | --- |
| `observation.images.left_wrist` | 기존 왼손목 |
| `observation.images.right_wrist` | 기존 오른손목 |
| `observation.images.top` | PNG 마스크 적용 top |
| `observation.images.top_raw` | 같은 관측의 원본 top |

두 top은 같은 episode/frame/timestamp의 관측에 들어가며 state/action 정의와 공식 종료·재녹화 루프는 유지합니다. 센서 동기화·실측 30 FPS 달성을 보장하지 않습니다. 기존 3영상 데이터셋에 직접 이어쓰기·병합하지 않습니다.

## 입력과 마스크 조건

OBS 가상 카메라는 **마스크 없는 원본 장면**을 출력해야 합니다. 일반 미리보기와 가상 카메라 출력 장면은 다를 수 있습니다. [OBS 가상 카메라 안내](https://obsproject.com/kb/virtual-camera-guide)에 따라 출력 장면을 확인합니다. OBS 일반 녹화 버튼은 필요하지 않습니다.

`--raw-top-input`은 작업자의 원본 입력 확인이며 OBS를 자동 검사·전환하지 않습니다. 기존 마스크 조건의 기록/추론으로 돌아가면 가상 카메라 출력도 해당 조건으로 맞춥니다.

RGBA PNG 크기는 top 영상과 같아야 하며 자동 크기 조정·위치 이동은 없습니다. 정수 alpha blend를 사용하므로 이전 OBS 합성 출력과 바이트 동일성을 보장하지 않습니다. 고정 영역 가림은 물체 분할이나 전체 배경 제거와 다릅니다. 마스크가 도구·그리퍼·작업 대상을 가리지 않는지 전체 동작에서 확인합니다.

수집 폴더의 `top_overlay.png`와 `top_pair.json`에 정확한 PNG·해시·feature 대응을 보관합니다. 이어쓰기는 같은 마스크·옵션과 호환 스키마를 요구합니다.

<a id="record"></a>
## 수집 명령

**PowerShell**, Python 환경 활성화 후 저장소 루트에서 실행합니다. 아래 마스크 경로는 해당 PC의 실제 RGBA PNG로 바꿉니다. 먼저 장치 연결 없는 검사:

```powershell
$topMask = 'configs/local/top_overlay.png'
python scripts/run_robot.py record --repo-id local/stir_coffee_top_pair --task "Stir the mixture in the cup with the muddler." --episodes 25 --episode-seconds 180 --reset-seconds 30 --fps 30 --wrist-fourcc MJPG --top-overlay $topMask --raw-top-input --prepare-hub --validate-only
```

검사 통과 후 [실물 준비](safety.md)를 마치고 아래 전체 명령을 실행합니다. 실제 모터를 구동합니다.

```powershell
python scripts/run_robot.py record --repo-id local/stir_coffee_top_pair --task "Stir the mixture in the cup with the muddler." --episodes 25 --episode-seconds 180 --reset-seconds 30 --fps 30 --wrist-fourcc MJPG --top-overlay $topMask --raw-top-input --prepare-hub
```

`--prepare-hub`는 장치 해제 후 두 3영상 사본 생성·LeRobot 로딩까지 수행하고 `prepared`에서 멈춥니다. 원격 저장소 생성·전송은 없습니다. 이 옵션도 생략하면 4영상 수집본만 남습니다. `--push-to-hub`와 동시 사용은 불가능합니다. 종료 키와 재개 절차는 [운영 안내](operations.md)를 따릅니다.

## 종료된 수집본에서 내보내기

원본 수집 폴더는 보존합니다. `--source`에는 시작 로그의 정확한 경로를 사용하며 출력은 원본과 분리된 **존재하지 않는 새 폴더**여야 합니다. 최신 폴더를 자동 선택하지 않습니다.

**PowerShell 예시**의 설명용 경로를 실제 값으로 바꾼 뒤 실행합니다.

```powershell
$pairedSource = 'data/lerobot/local/stir_coffee_top_pair/SESSION_TIMESTAMP'
$exportRoot = 'data/top_variants/stir_coffee_export_01'
python scripts/publish_top_variants.py --source $pairedSource --repo-id local/stir_coffee_export_01 --output-dir $exportRoot
python scripts/publish_top_variants.py --source $pairedSource --repo-id local/stir_coffee_export_01 --output-dir $exportRoot --prepare-only
```

첫 명령은 읽기 전용 검사, 두 번째는 두 사본 생성·로딩만 수행합니다. 원격 전송은 없습니다. 한 조건만 만들려면 별도 출력 경로로 실행합니다.

```powershell
python scripts/export_top_variant.py --source $pairedSource --output 'data/top_variants/stir_raw_export_01' --variant raw --validate-only
python scripts/export_top_variant.py --source $pairedSource --output 'data/top_variants/stir_raw_export_01' --variant raw
```

masked를 선택하면 가림막 적용 top을 사용합니다. 두 출력은 모두 `left_wrist/right_wrist/top` 키를 가지며 raw는 `top_raw`의 영상·통계·회차별 영상 참조를 `top`으로 대응시킵니다. 데이터 parquet와 선택 영상은 재인코딩 없이 복사·해시 검증합니다. 설치된 LeRobot v3.0 영상 레이아웃만 지원합니다. 실패 후 `EXPORT_INCOMPLETE`가 남은 출력은 사용하지 않습니다.

## 비교와 배포

두 버전은 동일 시연이므로 학습/검증 분할을 같게 하고 중복 집계하지 않습니다. 실물 추론 영상에도 학습한 top 조건을 맞춥니다. 배포 옵션·부분 실패·재시도는 [Hub 안내](huggingface.md#paired)에 모았습니다.

저장 경로와 샘플 로딩의 기존 검증, 공개된 젓기 50개 결과는 [데이터셋 목록](datasets.md#stir)에 정리했습니다. 짧은 기술 시험의 성공은 장시간 수집 성능·혼합 품질·자율 성공률을 입증하지 않습니다.
