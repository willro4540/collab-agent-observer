"""collab-agent-observer — MCP server, v1 "안전판" 스코프.

idea-bank 2026-09-04 "협력 에이전트" 항목의 최종 v1 스코프 그대로:
  - 온디맨드만 (자동 diff-감지, 훅 자동주입 없음 — 그건 연구판)
  - 스크린샷은 로컬 OCR 없이 그대로 반환 — Claude의 네이티브 비전으로 분석+조언까지 포함
  - 로그는 화이트리스트 등록된 것만 (CAD-MCP의 "입력 검증 전무" 결함을 반복하지 않음,
    autocad-architecture-study/docs/11 §2 참고)
"""

import json
from pathlib import Path

import mss
import pywinctl as pwc
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.utilities.types import Image
from PIL import Image as PILImage

server = MCPServer("collab-agent-observer")

MAX_IMAGE_EDGE = 1568  # Claude vision 권장 최대 변 — 이 이상은 토큰만 더 먹고 정확도 이득 적음

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# 화이트리스트: read_log가 접근 가능한 로그는 여기 등록된 것만.
# 임의 경로를 그대로 받지 않는다 — CAD-MCP가 save_drawing에서 이 검증을 안 해서 생긴
# "아무 경로에나 쓸 수 있음" 결함(autocad-architecture-study/docs/11 §2)을 반대로 적용한 것.
LOG_WHITELIST: dict[str, Path] = {
    "window_snapshots": LOG_DIR / "window_snapshots.jsonl",
    "cad_mcp": Path(r"C:\Users\user\Desktop\CAD-MCP\cad_mcp.log"),
}


def _resize_for_vision(img: PILImage.Image) -> PILImage.Image:
    w, h = img.size
    scale = min(1.0, MAX_IMAGE_EDGE / max(w, h))
    if scale < 1.0:
        img = img.resize((round(w * scale), round(h * scale)), PILImage.LANCZOS)
    return img


def _grab_to_pil(region: dict) -> PILImage.Image:
    with mss.MSS() as sct:
        shot = sct.grab(region)
    img = PILImage.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")
    return _resize_for_vision(img)


def _pil_to_image(img: PILImage.Image) -> Image:
    import io

    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="JPEG", quality=85)
    return Image(data=buf.getvalue(), format="jpeg")


@server.tool()
def list_windows() -> str:
    """현재 열려있는 창 목록을 JSON으로 반환한다 (제목 없거나 100x100보다 작은
    시스템 창은 제외). capture_window에 넘길 title_contains 값을 찾을 때 먼저 쓴다."""
    wins = []
    for w in pwc.getAllWindows():
        title = w.title.strip()
        if not title:
            continue
        box = w.box
        if box.width < 100 or box.height < 100:
            continue
        wins.append({"title": title, "width": box.width, "height": box.height})
    return json.dumps(wins, ensure_ascii=False, indent=2)


@server.tool()
def capture_window(title_contains: str) -> Image | str:
    """제목에 title_contains(대소문자 무관 부분일치)가 포함된 창을 찾아 캡처한다.
    로컬 OCR 없이 이미지를 그대로 반환한다 — Claude가 직접 보고 상황 설명+조언까지
    한 번에 답한다. 여러 개 매칭되면 첫 번째만 캡처한다."""
    matches = [
        w for w in pwc.getAllWindows()
        if w.title.strip() and title_contains.lower() in w.title.lower()
    ]
    if not matches:
        return f"'{title_contains}'가 포함된 창을 찾을 수 없습니다. list_windows로 먼저 확인하세요."
    w = matches[0]
    box = w.box
    img = _grab_to_pil({"left": box.left, "top": box.top, "width": box.width, "height": box.height})
    return _pil_to_image(img)


@server.tool()
def capture_screen() -> Image:
    """주 모니터 전체를 캡처한다."""
    with mss.MSS() as sct:
        region = sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]
    img = _grab_to_pil(region)
    return _pil_to_image(img)


@server.tool()
def read_log(name: str, tail_lines: int = 100) -> str:
    """화이트리스트에 등록된 로그 파일의 마지막 tail_lines줄을 읽는다.
    사용 가능한 name 목록: window_snapshots(이 서버 자신의 창 스냅샷 기록),
    cad_mcp(CAD-MCP의 실행 로그). 등록 안 된 이름은 거부한다."""
    if name not in LOG_WHITELIST:
        return f"알 수 없는 로그 이름: {name!r}. 사용 가능: {sorted(LOG_WHITELIST)}"
    path = LOG_WHITELIST[name]
    if not path.exists():
        return f"로그 파일이 아직 없습니다: {path}"
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    tail = lines[-tail_lines:]
    return "\n".join(tail) if tail else "(로그가 비어있습니다)"


if __name__ == "__main__":
    server.run(transport="stdio")
