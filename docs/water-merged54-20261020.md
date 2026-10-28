# 물 붓기 3조건 통합 결과 — 2026-10-20

원본 3개의 Hub 업로드와 로컬 일치를 확인하고 **54개·60,630프레임**의 통합본을 생성·검증했다. 사용자의 명시적 승인 후 [새 공개 통합본](https://huggingface.co/datasets/lmsforAI/so101_water_v2_merged54_20261020) 업로드와 원격20파일 해시 검증을 완료했다. 업로드 revision은 `fe4c0855ef99785b3b89567828b520b6833b3bb0`이며 v3.0 태그도 같은 commit을 가리킨다. 원본3개 revision은 유지됐다.

[물 붓기 HTML](water-dataset-library.html)은 통합 버전을 상단, 조건별 원본 3개를 기본 접힘 토글 아래 배치한다. 기존 [가루 HTML](dataset-library.html)은 보존했다.

## 원본 및 회차 대응

| 컵 조건 | 원본 저장소 | 에피소드 | 프레임 | 통합 회차 |
| --- | --- | ---: | ---: | --- |
| 커피 | [so101_water_coffee_v2_20261020_050444_130331](https://huggingface.co/datasets/lmsforAI/so101_water_coffee_v2_20261020_050444_130331) | 18 | 22,931 | 0–17 |
| 아이스티 | [so101_water_icetea_v2_20261020_070918_386791](https://huggingface.co/datasets/lmsforAI/so101_water_icetea_v2_20261020_070918_386791) | 18 | 17,889 | 18–35 |
| 녹차 | [so101_water_greentea_v2_20261020_061300_265602](https://huggingface.co/datasets/lmsforAI/so101_water_greentea_v2_20261020_061300_265602) | 18 | 19,810 | 36–53 |

원본 회차는 각각 0–17이다. 고정 revision은 순서대로 다음과 같다.

- 커피: `44c0e097c9acc3b0e5a3ae98db1de350bafe73c1`
- 아이스티: `c4766e7acf5cf46e0619426ea568931c4634409b`
- 녹차: `fd6c1a253441fdcb9f61c2a0f9372c314d21bfbb`

로컬 녹차 `20261020_061231_132721`은 0개·0프레임 세션으로 제외했다. 과거 water_v1 데이터도 이번 통합에 포함하지 않았다.

## 방법과 검증

- 원본 Hub의 meta/data/videos 전25파일과 로컬 파일 목록·크기·해시가 일치했다. LFS는 SHA-256, 일반 파일은 Git blob SHA-1을 대조했다.
- 작업 문장은 모두 `Pour water into the cup.`이다. feature schema·30 FPS·robot_type·v3.0 형식·공개 여부·Apache-2.0 라이선스가 일치했다.
- state/action 각12차원, 좌측6개 다음 우측6개다. 팔별 순서는 shoulder_pan, shoulder_lift, elbow_flex, wrist_flex, wrist_roll, gripper다. 영상은 left_wrist/right_wrist/top, 각각640×480 RGB다.
- 설치된 공식 `lerobot.datasets.aggregate.aggregate_datasets`를 `concatenate_videos=False`, `concatenate_data=False`로 실행했다. 모든 프레임 열에서 전역 index/episode_index 변경 이외의 값 보존, 영상10파일의 원본 SHA-256 일치, 회차 길이·경계·timestamp·파일 참조를 확인했다. 영상 재인코딩은 없다.
- 전역·회차별 수치 통계를 실제 프레임에서 float64·모집단 표준편차·정확한 선형 분위수로 재계산했다. 영상 통계는 원본 표본 통계의 공식 집계값을 유지했다. 원본 통계는 변경하지 않았다.
- LeRobot PyAV로 54회차의 처음·마지막 총108시점에서 카메라3개를 읽고 shape·유한값·회차 번호를 확인했다. 전체 영상의 의미/성공 전수 검사는 아니다.
- HTML의 활성 URL8개가 데이터셋 ID와 일치하며 통합본/원본 링크8개 HTTP200을 확인했다. Edge의 1440/768/390/320px에서 접힘·펼침, 마우스·키보드 토글, 가로 넘침 없음을 확인했다. PC/모바일 스크린샷을 검토했다. 외부 이미지·폰트·스크립트 의존성이 없다.

## 결과 위치 및 한계

- 새 통합본 ID: `lmsforAI/so101_water_v2_merged54_20261020` — 공개 업로드·원격 검증 완료.
- 로컬: `data/lerobot/lmsforAI/so101_water_v2_merged54_20261020/merged/`.
- 원본 추적: 통합본의 `episode_mapping.csv`, `meta/provenance.json`.
- 검사 스크립트·해시·통계·로그·화면: Git 제외 `outputs/water_merge_20261020/`.

기록 당시 보정·물리적 좌우 대응·정규화 옵션의 동일성은 메타데이터만으로 확정할 수 없다. 설치된 팔 구현은 use_degrees에 따라 몸체 관절의 degree/정규화 값을 선택하므로 모든 값을 각도로 단정하지 않는다. 값을 변환하지 않았다.

물 양·시연 성공률·학습 성능은 별도 평가 대상이다. 원본과 통합본을 함께 학습에 넣어 동일 시연을 중복 집계하지 않는다. 로봇 코드·장치 설정·보정 파일 변경, 실물 구동·추가 녹화·학습은 없었다. 데이터/HTML 전용 검사이며 로봇 단위검사는 재실행하지 않았다.
