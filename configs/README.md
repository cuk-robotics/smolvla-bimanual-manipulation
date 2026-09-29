# 설정

`project.example.json`은 프로젝트 자체의 설계 예시이며 LeRobot CLI에 직접 전달하는 설정이 아닙니다.
`null`과 빈 배열은 미확정 항목입니다. 임의의 포트·장치 ID·관절 한계로 대체하지 않습니다.

개인 장치 설정은 `configs/local/` 또는 `*.local.json`에 보관합니다.
기본 상태는 dry run이며, 현재 저장소에는 실물 실행 기능이 없습니다.
설정의 `hardware_enabled`를 바꾸어도 하드웨어 기능이 구현되거나 검증되는 것은 아닙니다.
