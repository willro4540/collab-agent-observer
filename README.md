# collab-agent-observer

"협력 에이전트" v1 — 안전판 스코프. idea-bank(`04-기술-품목-인벤토리.md`, 2026-09-04)의
최종 확정 스코프를 그대로 구현.

## 구성 (2개뿐)

1. **`src/logger.py`** — 조용한 로거. 60초마다 열려있는 창 목록+활성 창을
   `logs/window_snapshots.jsonl`에 판단 없이 append만 함.
2. **`src/server.py`** — 온디맨드 MCP 서버 (stdio). 도구 4개:
   - `list_windows()` — 현재 열린 창 목록
   - `capture_window(title_contains)` — 특정 창 캡처 (로컬 OCR 없음, Claude가 직접 봄)
   - `capture_screen()` — 전체 화면 캡처
   - `read_log(name, tail_lines)` — 화이트리스트 등록된 로그만 읽기

## 의도적으로 빠진 것 (연구판으로 분류됨, idea-bank 참고)

- 자동 변화 감지(diff-gating) — "의미있는 변화인가"는 로깅 시점이 아니라 Claude가
  read_log로 읽을 때 자연어로 판단
- 훅 기반 자동 브리핑
- 브라우저 actuation(마우스 조작 등)
- Colab 실시간 연동(현재는 별도 `pixiv-style-dataset/docs/colab_status_check_manual.md`
  메뉴얼로 안내만)

## 실행

```powershell
# 로거 (선택, 백그라운드)
python src\logger.py

# MCP 서버는 Claude Code에 등록해서 사용 (claude mcp add로 등록)
```

## 설계 원칙 (오늘 CAD-MCP 코드 레벨 분석에서 배운 것 반영)

- `read_log`는 화이트리스트 등록된 이름만 받는다 — CAD-MCP의 `save_drawing`이 임의 경로를
  그대로 받아쓰던 결함(autocad-architecture-study/docs/11 §2)을 반복하지 않기 위함.
- 스크린샷은 최대 1568px로 리사이즈 후 JPEG — 비전 토큰 절약.

## 검증 이력 (2026-09-04)

1. **함수 직접 호출 테스트** — `list_windows`/`capture_window`/`capture_screen`/`read_log`
   전부 정상 동작 확인. 실제 화면 캡처(이 세션의 터미널+브라우저)까지 눈으로 확인.
2. **적대적 재검토로 버그 3개 발견 → 수정 → 재검증**: 최소화/화면 밖 창 캡처 시 에러 없이
   새까만 이미지만 반환하던 문제(가장 심각, 조용한 실패), `read_log`의 비효율적 전체 파일
   읽기, `logger.py`의 예외 미처리로 인한 조용한 전체 중단 위험 — 전부 수정 후 회귀 없음
   확인.
3. **실제 MCP stdio 프로토콜 E2E 테스트** (`src/_e2e_client_test.py`, 진짜 `ClientSession`으로
   `initialize`→`list_tools`→`call_tool` 전체 경로 실행) — Claude Code 재시작 없이도 서버가
   프로토콜 레벨에서 완전히 정상 동작함을 확인. 재사용 가능한 회귀 테스트로 남겨둠
   (`python src/_e2e_client_test.py`로 언제든 재실행 가능).

## 비정상 상황 대응 (troubleshooting)

- **`claude mcp list`에서 이 서버가 Connected로 안 뜰 때**: 터미널에서
  `python src\server.py`를 직접 실행해서 즉시 나오는 예외 메시지부터 확인(임포트 실패,
  의존성 누락 등은 여기서 바로 드러남). 정상이면 아무 출력 없이 대기 상태가 됨(Ctrl+C로 종료).
- **`src\_e2e_client_test.py`가 실패할 때**: 어느 단계(initialize/list_tools/call_tool)에서
  멈췄는지가 그대로 원인 위치를 가리킴 — 이 스크립트 자체를 1차 진단 도구로 쓴다.
- **백그라운드 로거(`logger.py`)가 죽었는지 확인하는 법**: `window_snapshots.jsonl`의
  마지막 줄 타임스탬프가 60초 이상 안 갱신되면 죽은 것. 프로세스 목록에서 안 보이면
  그냥 재실행(`python src\logger.py`) — 상태를 유지할 필요가 없는 순수 append-only
  로거라 재시작에 부작용 없음.
- **로그 파일이 깨졌거나 이상한 바이트가 섞였을 때**: `read_log`는 `errors="replace"`로
  읽으므로 깨진 바이트가 있어도 서버가 죽지 않고 `�`로 치환해서 계속 동작한다 — 다만
  근본 원인(비정상 종료 중 쓰기 등)은 별도로 봐야 함.
- **의존성(pywinctl/mss/mcp)이 오염되거나 버전이 꼬였을 때**: 이 프로젝트는 전역 Python
  환경을 그대로 쓴다(CAD-MCP처럼 venv 격리 안 함, 최신 mcp API로 처음부터 짜서 버전 충돌
  없었음) — 문제가 생기면 `pip show mcp pywinctl mss`로 버전부터 확인.
