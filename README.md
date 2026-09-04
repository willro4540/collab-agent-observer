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
