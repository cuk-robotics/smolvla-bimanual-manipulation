> 과거 실험·계획 기록입니다. 현재 실행은 [운영 안내](../operations.md), [수집 명령](../recording.md), [추론 안내](../inference.md)를 우선합니다.

# 녹차 가루 기록 이어쓰기 — 2026-10-19

Hub `main/meta/info.json`과 로컬 메타데이터가 동일함을 읽기 전용으로 확인했다. 저장분은 episode_index 0~21의22개·30,032프레임이다. 30 FPS·양팔 state/action 각12차원·영상3개이며 로컬 tasks.parquet의 작업 문장은 아래 명령과 같다. 회차 길이는1,204~1,471프레임이다. 영상 품질·작업 성공 전수 검증은 아니다.

기존30개 목표 기준8개를 추가한다. `--episodes`는 최종 합계가 아니라 **이번 추가 수**다. OBS 가상 카메라와 물체·리더/팔로워 시작 자세를 준비하고 다른 제어·미리보기를 종료한다. 오른쪽 키가 눌린 상태가 아닌지 확인한다. 베이스 고정·간섭·종료 시 토크 해제는 [안전 절차](../safety.md)를 따른다.

**CMD**:

```bat
C:\miniforge3\condabin\conda.bat activate cuk-robotics
cd /d E:\Desktop\smolvla-bimanual-manipulation
python scripts/run_robot.py record --resume --repo-id lmsforAI/so101_powder_greentea_v2_20261019_183148_147926 --dataset-root "E:\Desktop\smolvla-bimanual-manipulation\data\lerobot\lmsforAI\so101_powder_greentea_v2\20261019_183148_147926" --expected-episodes 22 --task "Pour green tea latte powder from the green-lidded container into the cup." --episodes 8 --episode-seconds 180 --reset-seconds 20 --fps 30 --display-fps 30 --wrist-fourcc MJPG --push-to-hub
```

정상 완료하면 episode_index22~29를 추가하고 같은 Hub 저장소에 업로드한다. 새 시각 접미사는 붙이지 않으며 시작 표시는 `Episode 23/30 (episode_index=22)`다. 기존 로컬 폴더가 필수다. Hub만 있는 경우의 자동 복구·다운로드 기능은 추가하지 않았다.

`--expected-episodes 22`는 추가 저장 후 같은 명령의 재실행을 장치 연결 전에 중단한다. 재중단 시 저장 회차와 남은 수를 확인하여 두 값을 함께 조정한다. `--resume` 없는 실행은 새 세션이며 자동 병합되지 않는다. 이어쓰기는 기존 폴더를 갱신하므로 원본 사본이 필요하면 실행 전에 전체 폴더를 별도 복사한다.

직접 오류는 빈 버퍼의 `save_episode()` 호출이다. 설치된 키 리스너는 key-down마다 `exit_early`를 설정하고, 기록 루프는 프레임 수집 전에 이를 검사한다. 반복 입력이 재배치와 다음 시연까지 건너뛰어 빈 버퍼를 저장하는 경로는 가능하다. 실제 반복 입력의 장치·드라이버·훅 원인은 확인 필요다. 공식 finally에서 정리·장치 해제·저장분 업로드를 수행하므로 업로드 완료와 traceback이 함께 나올 수 있다.

이번 변경은 이어쓰기 지원이며 키 반복 자체를 수정한 것은 아니다. 방향키를 짧게 한 번 누르고 떼며 단계 표시를 기다린다. 설치 버전은 `n`=다음 단계, `r`=재녹화, `q`=종료도 지원하지만 이 키들도 길게 누르면 반복될 수 있다. 반복이 지속되면 수집을 멈추고 입력 장치를 점검한다.

검증: 오프라인 설정·단위50개·위 명령의 `--validate-only` 통과. 설정 파싱·로컬 회차/FPS/작업문장·카메라 배치를 검사했다. 실제 장치 호환성은 실행 시 공식 LeRobot이 검사한다. 실물 녹화·모터 연결·추가 업로드·키 반복 재현은 수행하지 않았다. 로그: `outputs/resume_greentea_20261019/`.

근거: 로컬/Hub info.json, 로컬 tasks.parquet·meta/episodes, 설치된 LeRobot의 lerobot_record.py·lerobot_dataset.py::resume·keyboard_input.py.
