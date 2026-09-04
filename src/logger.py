"""조용한 로거 — 판단 없이 그냥 기록만 한다.

idea-bank 2026-09-04 "협력 에이전트" v1 스코프의 컴포넌트 (1): 어떤 창이 열려있는지를
INTERVAL초마다 window_snapshots.jsonl에 한 줄씩 append. "이게 의미있는 변화인가"는
여기서 판단하지 않는다 — 그 판단은 read_log로 나중에 Claude가 읽을 때 자연어로 한다
(diff-gating을 없앤 오늘의 설계 결정 그대로, idea-bank 참고).

실행: python logger.py  (Ctrl+C로 중단)
"""

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import pywinctl as pwc

INTERVAL_SECONDS = 60
LOG_PATH = Path(__file__).resolve().parent.parent / "logs" / "window_snapshots.jsonl"
LOG_PATH.parent.mkdir(exist_ok=True)


def snapshot() -> dict:
    titles = sorted({
        w.title.strip()
        for w in pwc.getAllWindows()
        if w.title.strip() and w.box.width >= 100 and w.box.height >= 100
    })
    active = pwc.getActiveWindowTitle() or ""
    return {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "active": active,
        "open_windows": titles,
    }


def main() -> None:
    print(f"[logger] {INTERVAL_SECONDS}초 주기로 {LOG_PATH}에 기록 시작 (Ctrl+C로 중단)")
    while True:
        entry = snapshot()
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        time.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[logger] 중단됨")
