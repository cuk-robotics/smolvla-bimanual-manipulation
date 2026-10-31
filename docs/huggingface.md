# 데이터셋 배포와 Hugging Face

GitHub에는 코드·문서·공개 설정 예시, Hugging Face Dataset에는 검토한 데이터·데이터 카드를 관리합니다. 모델은 별도 Model 저장소에서 학습 환경·입출력 키·데이터 revision·성능 한계를 기록합니다. 공개 데이터셋 ID와 검증 이력은 [데이터셋 목록](datasets.md)을 기준으로 합니다.

## 인증과 기본 동작

Python 환경을 활성화한 **CMD 또는 PowerShell**에서 실행합니다. 대상 계정의 쓰기 권한을 확인하고 로그인은 필요한 경우에만 수행합니다.

```text
hf auth whoami
hf auth login
```

토큰을 명령 인자·Git·공유 설정에 넣지 않습니다. 기본 `record`는 로컬 전용입니다. `--validate-only`는 장치·네트워크 연결과 Hub 저장소 생성 없이 설정만 검사합니다. 시작 로그의 Hub destination은 예정 주소이며 업로드 성공 증거가 아닙니다.

새 업로드/paired 준비 실행은 기본 repo ID에 한국 시간 `YYYYMMDD_HHMMSS_마이크로초`를 붙입니다. 수집 시리즈 이름의 v1/v2는 LeRobot 파일 형식 v3.0과 별개입니다. 재개는 시각 접미사를 새로 붙이지 않고 정확한 기존 ID를 사용합니다.

## 일반 3영상 기록 업로드

아래는 **CMD/PowerShell 공통** 전체 명령 예시입니다. `YOUR_ACCOUNT`는 쓰기 권한이 있는 계정으로 변경합니다. 실제 로봇 기록 후 공개 업로드를 수행합니다.

```text
python scripts/run_robot.py record --repo-id YOUR_ACCOUNT/stir_coffee --task "Stir the mixture in the cup with the muddler." --episodes 25 --episode-seconds 180 --reset-seconds 30 --fps 30 --wrist-fourcc MJPG --push-to-hub
```

비공개 요청은 같은 전체 명령에 `--private`를 추가합니다. 해당 플래그는 `--push-to-hub` 또는 paired의 `--prepare-hub`와 함께 사용합니다. 종료 키·저장 시점은 [운영 안내](operations.md)를 따릅니다. 0회차 또는 강제 종료에서는 업로드를 보장하지 않습니다. 네트워크 오류가 나더라도 로컬 원본은 보존하며 자동 재업로드는 구현하지 않았습니다.

<a id="paired"></a>
## paired 수집의 두 저장소 배포

[동시 수집](paired-top-recording.md)에서 업로드를 요청하면 공식 기록기의 4영상 직접 업로드는 비활성화하고, 장치 해제 후 두 3영상 사본을 준비해 순차 전송합니다.

| 옵션 | 결과 |
| --- | --- |
| 두 옵션 모두 생략 | 로컬 4영상 수집 원본 |
| `record --prepare-hub` | 원본 + raw/masked 로컬 사본, `prepared`에서 종료 |
| `record --push-to-hub` | 원본 보존 + raw/masked 두 Hub 저장소 업로드 |
| `publish_top_variants.py` 옵션 없음 | 읽기 전용 검사 |
| 같은 스크립트의 `--prepare-only` | 로컬 사본·로딩 검사까지만 수행 |
| 같은 스크립트의 `--push-to-hub` | 새 로컬 사본 준비 후 두 저장소 업로드 |

준비 전용과 업로드 옵션은 서로 배타적입니다. 두 저장소 이름은 `<실제 기본 ID>_raw`와 `_masked`이며 모두 `left_wrist/right_wrist/top` 키를 사용합니다. `--private`는 두 업로드에 전달됩니다.

종료된 수집본의 **PowerShell 공개 업로드 예시**입니다. 계정·원본 경로·새 출력 경로를 실제 값으로 바꾸고, [준비 전용 검사](paired-top-recording.md)를 먼저 수행합니다.

```powershell
python scripts/publish_top_variants.py --source 'data/lerobot/YOUR_ACCOUNT/stir_coffee_top_pair/SESSION_TIMESTAMP' --repo-id YOUR_ACCOUNT/stir_coffee_pair_SESSION_TIMESTAMP --output-dir 'data/top_variants/stir_publish_02' --push-to-hub
```

두 사본의 생성·LeRobot 로딩을 모두 마친 뒤 순차 전송합니다. 두 저장소 업로드는 원자적 작업이 아니므로 부분 실패할 수 있습니다. `hub_publish.json`의 `prepared/uploaded/failed`와 원격 파일을 각각 확인합니다. 재시도는 같은 기본 ID와 **새 출력 폴더**를 사용하며 원본·기존 사본을 덮어쓰지 않습니다.

전송 대상은 `data/`, `meta/`, `videos/`와 공식 데이터 카드입니다. 로컬 절대 경로가 담긴 루트 `top_variant.json`은 제외하고 공개 `meta/top_variant.json`에는 조건·대응 ID·마스크 해시를 기록합니다.

## 카드·검증·원본 보존

[데이터 카드 양식](../templates/dataset_card.md)은 실제 정보로 채워 사용하며 실행기가 자동 반영하지 않습니다. 설치된 LeRobot의 자동 카드 라이선스 기본값 `apache-2.0`과 프로젝트 코드 MIT는 별개입니다. 권리·수집량·성공률을 확인한 범위에서 작성합니다.

업로드 후 공개 범위, 고정 revision, 파일 목록·크기·해시, 필요한 v3.0 태그를 확인하고 기록합니다. 원본과 통합본의 대응은 `episode_mapping.csv`·provenance로 보존합니다. 폴더나 영상 이름을 수동으로 합치지 않습니다. 배포 완료는 작업 성공·학습 성능 인증이 아닙니다.

참고: [데이터 카드](https://huggingface.co/docs/hub/datasets-cards), [LeRobot Dataset v3](https://huggingface.co/docs/lerobot/lerobot-dataset-v3).
