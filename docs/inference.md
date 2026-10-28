# 두 모델 추론 방법 — 2026-10-21

모델2개 × 작업4개의 전체 CMD 명령은 [추론 명령 HTML](inference-commands.html)에 정리했다. 모델 선택 후 실행 명령 또는 장치 연결 없는 설정 검사 명령을 복사한다. 각 명령에 작업 폴더 이동과 환경 설정이 포함되며 기본100초·MJPG·자동 워밍업·상대 목표 제한 유지·복귀 없음이다. 물은 세 음료 공통 작업이다. 2chan 작업 학습 여부는 여전히 미확인이다.

## 현재 동작: 모터 연결 전 자동 워밍업

사용자는100초 명령으로 기다린 뒤 움직임이 이어짐을 확인했고, 후속 요청에 따라 `infer`에 자동 워밍업을 추가했다. 기존 실행 명령을 그대로 사용한다. `--validate-only`에서는 가중치 로딩·워밍업·장치 연결을 하지 않는다.

공식 LeRobot이 정책을 한 번 로딩한 직후, 동일 인스턴스를 장치 연결 전에 두 번 추론한다. 입력은 검증된 스키마 크기의 검은 uint8 영상·0 상태와 실제 실행 task이다. 생성 행동은 모두 버리며 매회 큐를 초기화하여 두 번째도 실제 묶음을 계산한다. 마지막에 정책·전후처리 상태를 초기화하고 CPU/CUDA 난수 상태를 복원한다. 실물 루프는 새 관측으로 행동을 다시 생성한다. 워밍업 출력을 모터에 보내거나 데이터로 저장하지 않는다.

실행 순서: Rerun 창 생성 → 모델 로딩 → `Inference warmup 1/2`, `2/2` → 워밍업 완료 → 공식 카메라/로봇 연결 → 공식 rollout 타이머 시작. 워밍업도 기다려야 하지만 모터 연결·실행 제한시간 이전에 수행한다. 실패나 공식 종료 이벤트(Ctrl+C)가 감지되면 장치 연결 전 중단한다. 공식 context 생성/정책 로더를 실행 세션에서만 감싸고 정상·예외 종료 시 복원한다. 설치 패키지 파일과 공식 제어 루프는 수정하지 않는다. LeRobot 버전 변경 시 이 연결 지점의 호환성을 다시 검사해야 한다.

워밍업은 초기 비용을 앞당기는 처리이며 이후 동기 묶음 추론 중 지연을 제거하지 않는다. Rerun도 워밍업 중에는 아직 카메라가 연결되지 않아 빈 화면이다. 영상은 장치 연결 후 첫 관측/추론/모터 명령 이후 표시된다. 독립적인 실시간 미리보기는 이번 범위에 포함하지 않는다.

장치 없는 검증은 `outputs/inference_20261021_inspect/warmup_verification.json` 및 `verify_warmup.log`에 저장한다. 실제 공식 context 경로에서 워밍업 후 로봇 생성 직전에 차단하여 연결 순서를 검증하고, 큐 비움·난수 보존·원래 함수 복원·저장된 녹차 관측의 유한한12차원 출력을 확인한다. 실물 동작 개선은 사용자 재확인이 필요하다.

아래16초 지연 진단은 자동 워밍업 도입 전 기록이다. 모터 연결 전 워밍업은 현재 구현됐으며 표시/추론 분리는 여전히 미구현이다.

최종 무장치 측정: 2chan 워밍업15.840/0.343초, 큐 초기화 후 저장 관측 첫 추론0.325초. Taem22n 워밍업0.571/0.328초, 첫 추론0.333초. 같은 프로세스에서 순서대로 측정했으므로 Taem22n의 새 프로세스 초기 지연 비교로 해석하지 않는다. 카메라/모터/Rerun 비용은 제외한다. check_config·단위54개·두 모델 infer validate-only 통과. 최초 단위 실행에서 sandbox 기본 임시폴더 권한 오류가 발생하여 프로젝트 내 TEMP/TMP로 재실행했으며 테스트/제품 코드를 바꾸어 우회하지 않았다.

## 과거 진단: 워밍업 적용 전 2chan 5초 시험

이 절은 자동 워밍업을 추가하기 전의 진단 기록입니다. 현재 구현은 위 자동 워밍업 절을 따릅니다.

사용자 로그에서 18:20:46에 제어 루프를 시작하고 첫 반복이 18:21:02에 끝났다. 약16초 첫 반복 후 다음 반복 시작에서 5초 제한을 확인하고 종료했다. 그 이전 모델 로딩 약23초·장치 연결 시간은 이 duration 타이머에 포함되지 않는다.

설치된 LeRobot 0.6.1의 `rollout/strategies/base.py`는 관측→동기 추론/모터 명령→Rerun 전송 순서다. Rerun 창은 모델 로딩 전에 생성되지만 첫 관측 전송은 첫 추론·모터 명령 후에 이루어진다. 따라서 사용자 관찰처럼 종료 무렵 첫 영상이 보일 수 있다. duration은 반복 경계에서 검사하므로 처리 중인 추론을 5초에 취소하지 않으며, 이번 로그에서는 시간 초과 후에도 첫 모터 명령이 전달됐다.

장치 없는 저장 관측101회 측정으로 2chan 첫 행동 생성15.936초, 다음 묶음 생성0.340/0.348초, 캐시 행동 반환 중앙값0.00363초를 확인했다. 모델 로딩22.694초는 별도다. `outputs/inference_20261021_inspect/latency_profile.json`과 `profile_latency.log` 참조. 최초 실행 비용의 정확한 내부 원인(CUDA 초기화/커널 등)은 분리 계측하지 않았다. 입력은 저장된 float 영상이며 실제 uint8 카메라 전처리·모터·Rerun 부하는 제외한다.

앞서 안내한5초는 이 모델의 초기 지연을 반영하지 못했다. 아래 실물 명령은100초로 정정한다. 시간 증가는 첫5초만 쓰고 종료하는 문제의 우회이며 초기 지연·후속 동기 추론 중 영상 정지를 제거하지 않는다. 정책의50개 행동 캐시가 소진될 때 묶음을 새로 생성하므로 지속30Hz 제어를 보장하지 않는다. 근본 개선은 모터 연결 전 워밍업 및 추론/표시 분리 경로의 별도 구현·검증이 필요하다. 이번에는 제어 코드·제한·패키지를 변경하거나 장치를 구동하지 않았다.

출력 `Cameras: {}`는 카메라가 없다는 뜻이 아니라 키 이름 변경표가 비어 있다는 뜻이다. 2chan은 저장 키를 그대로 사용한다. shoulder_lift 상대 목표 제한 경고는 한 번의 목표가 제한됐음을 뜻하며 이번16초 추론 지연·시간 종료의 원인이 아니다. 제한 해제를 해결책으로 적용하지 않는다.

## 확인한 모델과 준비 상태

- [2chan/smolvla-capstone-40k](https://huggingface.co/2chan/smolvla-capstone-40k/tree/2dc86905ed72c83aa3cafb46774ef157cbb0e06e): 모델 저장소, revision `2dc86905ed72c83aa3cafb46774ef157cbb0e06e`. 실행 사본은 `models/smolvla-capstone-40k`.
- [Taem22n/matcha-shaker-w8-261021-01](https://huggingface.co/datasets/Taem22n/matcha-shaker-w8-261021-01/tree/60c665d066cab89a96553f6857bcf2dbb710e8df): **데이터셋 저장소에 체크포인트 7z를 배포**. revision `60c665d066cab89a96553f6857bcf2dbb710e8df`. 압축 내부 `pretrained_model`을 확인했고 실행 사본은 `models/matcha-shaker-w8-261021-01`.

원본은 각각 `models/<모델명>-original`에 보존했다. 실행 사본만 기반 모델·토크나이저·정책 경로를 현재 PC에 맞추고 `load_vlm_weights=false`, `push_to_hub=false`로 설정했다. 전체 정책 가중치를 읽는 구성이다. 가중치 및 정규화 safetensors의 원본/사본 SHA-256 일치를 확인했다. 설치 패키지·장치 설정·보정·제어 코드는 변경하지 않았다.

두 모델 모두 state/action 12차원, 영상 3개·640×480이다. 2chan은 `left_wrist/right_wrist/top` 키를 그대로 사용하고 Taem22n은 저장된 `top→camera1`, `left_wrist→camera2`, `right_wrist→camera3` 매핑을 사용한다. 서로 매핑이나 영상 feature 순서를 복사하지 않는다.

2chan 공개 저장소에는 학습 설정·원본 데이터 ID·task 목록·관절 이름이 제공되지 않는다. 아래 녹차 명령은 로컬 데이터와의 실행 호환성 확인용 예시이며, 2chan이 해당 문장·단위·관절 순서로 학습됐다는 증거는 아니다. 실물 실행 전 학습 담당자에게 확인한다. 이름의 `40k`만으로 완료 스텝을 확정하지 않는다.

## CMD 실행

이 PC에는 모델 준비가 끝나 있으므로 다음 공통 설정부터 실행한다. `infer_beverage.bat matcha`는 과거 w6 모델을 가리키므로 이번에는 아래 직접 명령을 사용한다.

```bat
cd /d E:\Desktop\smolvla-bimanual-manipulation
set "PY=C:\miniforge3\envs\cuk-robotics\python.exe"
set "HF_HUB_OFFLINE=1"
set "TRANSFORMERS_OFFLINE=1"
set "DATA=data/lerobot/lmsforAI/so101_powder_greentea_v2_merged35_20261019/merged"
set "TASK=Pour green tea latte powder from the green-lidded container into the cup."
```

장치 연결 없는 설정 검사:

```bat
"%PY%" scripts/run_robot.py infer --policy-path models/smolvla-capstone-40k --dataset-root "%DATA%" --task "%TASK%" --wrist-fourcc MJPG --duration-s 5 --validate-only
"%PY%" scripts/run_robot.py infer --policy-path models/matcha-shaker-w8-261021-01 --dataset-root "%DATA%" --task "%TASK%" --wrist-fourcc MJPG --duration-s 5 --validate-only
```

OBS 가상 카메라를 시작하고 practice·record·preview 등 장치 사용 프로그램을 종료한다. 현재 설정은 팔로워 COM13/COM12, 카메라 left_wrist=0/right_wrist=1/top=4이나 실제 장치 번호·방향·시연 배치 일치는 현장에서 확인한다. 베이스·이동 공간을 확보하고 학습 시 시작 자세와 물체 배치를 맞춘다. 아래는 **실제 양팔을 구동**한다. 한 모델씩 실행한다.

```bat
"%PY%" scripts/run_robot.py infer --policy-path models/smolvla-capstone-40k --dataset-root "%DATA%" --task "%TASK%" --wrist-fourcc MJPG --duration-s 100
```

```bat
"%PY%" scripts/run_robot.py infer --policy-path models/matcha-shaker-w8-261021-01 --dataset-root "%DATA%" --task "%TASK%" --wrist-fourcc MJPG --duration-s 100
```

100초는 최대 실행 시간이며 완료 판정이나 즉시 중단을 보장하지 않는다. 현재 명령은 기존 상대 목표 차이 제한 유지·자동 복귀 없음·기록/업로드 없음이다. 과거 실험 조건인 제한 해제·시작 자세 복귀가 필요하면 해당 위험과 공간을 확인한 뒤 다음처럼 실행한다.

```bat
"%PY%" scripts/run_robot.py infer --policy-path models/matcha-shaker-w8-261021-01 --dataset-root "%DATA%" --task "%TASK%" --wrist-fourcc MJPG --duration-s 100 --no-target-limit --return-to-initial-position
```

`--no-target-limit`은 현재 위치와 목표 위치 사이 차이 제한을 해제한다. 초당 속도나 절대 관절 범위 설정이 아니다. 복귀 옵션은 Ctrl+C 후에도 양팔·그리퍼 복귀를 시도하며 충돌 회피·물체 반납 기능이 아니다. 종료 시 토크 해제와 처짐을 고려한다. [실물 주의사항](safety.md)을 참고한다.

## Taem22n 작업 선택

HTML 대시보드의 작업 문장과 로컬 `meta/tasks.parquet`가 일치한다. 공통 설정의 DATA/TASK를 다음 쌍으로 바꾼 후 동일한 Taem22n 명령을 사용한다. 모델 재학습·정규화 교체는 필요하지 않으며 `--dataset-root`는 현재 실행기의 스키마 확인용이다.

| 작업 | DATA: `data/lerobot/lmsforAI/` 아래 | TASK |
| --- | --- | --- |
| 커피 | `so101_powder_coffee_v2_merged35_20261019/merged` | `Pour coffee powder from the red-lidded container into the cup.` |
| 아이스티 | `so101_powder_icetea_v2_merged35_20261019/merged` | `Pour iced tea powder from the blue-lidded container into the cup.` |
| 녹차 | `so101_powder_greentea_v2_merged35_20261019/merged` | `Pour green tea latte powder from the green-lidded container into the cup.` |
| 물 | `so101_water_v2_merged54_20261020/merged` | `Pour water into the cup.` |

물 작업 예시(CMD, 위 공통 설정 후):

```bat
set "DATA=data/lerobot/lmsforAI/so101_water_v2_merged54_20261020/merged"
set "TASK=Pour water into the cup."
"%PY%" scripts/run_robot.py infer --policy-path models/matcha-shaker-w8-261021-01 --dataset-root "%DATA%" --task "%TASK%" --wrist-fourcc MJPG --duration-s 100
```

가루→물 자동 전환·완료 판정·젓기는 이 명령에 포함되지 않는다.

## 대시보드와 검증 범위

제공 HTML은 10,380스텝·2 epoch·batch32, 학습127/검증32 에피소드, 정규화 행동 MAE 약0.09749를 보고한다. 79.8%는 정규화 허용오차 0.1 안에 든 행동 요소 비율이며 실물 작업 성공률이 아니다. 최종 검증은 관측128개에 대한 기록이며 검증 프레임40,578개 전수 평가로 해석하지 않는다. HTML의 best step과 Hub 가중치가 같은 산출물인지는 별도 해시/내보내기 기록이 필요하다.

두 모델의 녹차 예시 `infer --validate-only`를 장치 연결 없이 통과했다. 이는 로컬 데이터 스키마와 설정을 대조하며 모델의 학습 단위·실물 배치·작업 성공을 입증하지 않는다. 검사·준비 근거는 `outputs/inference_20261021_inspect/`에 있다. 실물 모터·카메라 실행은 수행하지 않았다.

두 모델 모두 `strict=True` 전체 가중치 로딩과 저장된 녹차 episode0/frame0 관측에서 유한한 12차원 행동 생성을 통과했다(`offline_smoke.json`, `offline_smoke.log`). 이는 모델당 관측1개 실행 검사이며 성능 평가나 학습 제외 표본 검증이 아니다. 제어 코드 변경이 없어 프로젝트 단위검사는 재실행하지 않았다.

## 실험 담당자 관점의 질문

1. 2chan 학습의 task 문장·관절 순서·단위·카메라 배치가 현재 실물과 일치하는가?
2. 두 모델에 동일한 시작 배치와 성공 기준을 적용하고 반복 실험할 수 있는가?
3. 접근·파지·붓기·반납 중 실패 단계와 추론 지연을 구분해서 기록할 수 있는가?
