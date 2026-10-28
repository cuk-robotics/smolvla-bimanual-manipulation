# RTX 5070 Ti 가루 정책 추가 학습 — 2026-10-07

현재 PC의 RTX 5070 Ti 16GB에서 전달받은 `models/matcha-shaker-w6-261007-01`을 가루 작업으로 추가 학습한다. 기존 가중치로 초기화하며, 전달받지 않은 optimizer/scheduler 상태의 재개는 아니다. 물 작업 성능 보존은 보장하지 않는다.

CMD 실행:

```bat
cd /d E:\Desktop\smolvla-bimanual-manipulation
scripts\windows\train_powder.bat
```

배치 파일은 기존 `cuk-robotics` Python으로 설치된 공식 `lerobot.scripts.lerobot_train`을 실행한다. 로컬 설정은 Git 제외 `configs/local/powder_train_5070ti/train_config.json`이다. 데이터·모델·토크나이저는 로컬 경로를 사용하고 네트워크·자동 업로드·WandB는 비활성화한다. 장치 연결은 없다.

현재 속도 조정 설정: 가루 40개/71,719프레임, batch 32, 5,000 업데이트, seed 1000, 초기 학습률 1e-5, warmup 125, cosine decay 5,000, 종료 학습률 1e-6, chunk_size/n_action_steps 50/50, num_workers 4, prefetch_factor 2, PyAV. 이미지 증강은 이번 비교에서 비활성화한다. 기존 batch8×20,000과 같은 160,000회 관측 제시/약 2.23회분이다. 업데이트 횟수와 배치 구성이 달라지므로 학습 결과가 동일하다는 의미는 아니다. 고유 프레임 전체 순회를 보장하는 수치도 아니다.

기존 검증 시연 `[4,6,10,22,25,27,29,34,42,49]`는 학습에서 제외한다. 자동 검증 손실은 활성화하지 않았으며 이 10개와 실물 시험으로 체크포인트를 별도 비교해야 한다. 새 데이터의 정규화 통계는 공식 warm-start 경로에서 적용되며 원본 모델·원본 통계 파일을 수정하지 않는다.

모델은 기존 freeze_vision_encoder/train_expert_only/train_state_proj 설정을 사용한다. AMP 활성화 검사에서 BF16 gradient에 대한 GradScaler 오류가 발생해 `use_amp=false`를 사용한다. TorchCodec 로드 경고가 나올 수 있으나 선택한 영상 경로는 PyAV다.

실행마다 공식 trainer가 `outputs/train/<날짜>/<시각>_powder_5070ti_warmstart`를 새로 만든다. 500 업데이트마다 및 마지막에 checkpoint를 저장한다. 기존 실행이 진행 중이면 이 파일 수정이 실행 중 객체에 반영되지 않는다. 실험 중간 종료 후 재개에는 해당 실행의 저장된 `train_config.json`과 training state를 사용해야 한다. 배치 파일 기본 명령은 전달받은 원본 체크포인트에서 새 실험을 시작한다.

짧은 실행 검사와 본 학습 완료·장기 수치 안정성·실물 성공률은 구분한다.

검증: 같은 배치 파일·batch8・num_workers2・AMP=false로 공식 trainer 2회 업데이트 완료(exit 0). loss 1.402/1.031, gradient norm 12.166/10.846은 유한값이고 보고된 GPU 메모리는 3.49/3.90GB다. 짧은 검사에서는 저장을 비활성화했으며 scheduler가 2스텝으로 자동 축소되므로 장기 학습률 검증을 뜻하지 않는다. 결과 경로는 `outputs/train/powder_5070ti_smoke_noamp_20261007`이다.

속도 조정 검사: batch32/num_workers4로 공식 trainer 8회 업데이트 완료(exit0). 최대 보고 GPU 메모리 10.85GB, 후반 업데이트 약 1.14초/32관측이며 loss·gradient는 유한값이다. 로그는 `outputs/inference_matcha_w6_preflight/train_speed_b32_w4_u8.log`이다. 설치된 공식 factory는 map-style 데이터의 영상 반환을 이미 uint8로 고정하므로 `dataset.return_uint8=true`는 이번 속도 개선의 추가 원인으로 보지 않는다. 검사는 짧고 초기 모델/worker 로딩 시간을 포함하며 장기 처리량·수렴 성능을 보장하지 않는다.

이어서 기존 batch8/workers2 조건도 8업데이트 exit0로 비교했다. 3~8번째 로그에서 기존 21~22관측/초·최대3.90GB, 변경 조건 28관측/초·최대10.85GB로 후반 처리량 약30% 증가를 확인했다. 기존 첫 배치 대기 약25초, 변경 약57초이므로 짧은 실행 전체 시간을 비교하면 초기 로딩의 영향을 받는다. 장기 전체 소요시간은 측정하지 않았다. 원시 비교 로그는 `outputs/inference_matcha_w6_preflight/train_speed_b8_w2.log`이다. 실제 학습의 마지막 작은 배치, 저장·영상 읽기 변동을 포함한 지속 측정이 필요하다.
